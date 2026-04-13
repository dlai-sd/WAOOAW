/**
 * Artifact Preview Registry — config-driven plugin system for content renderers.
 *
 * Maps artifact types to renderer components.  Adding support for a new artifact
 * type requires ONE call to `registerArtifactRenderer()` — zero component surgery.
 *
 * Usage:
 *   // 1. Register once at startup (or inline in your file):
 *   registerArtifactRenderer('table', { component: TableRenderer, label: 'Content Calendar' })
 *
 *   // 2. Render anywhere:
 *   <ArtifactPreviewRegistry artifactType={post.artifact_type} post={post} />
 *
 * The registry ships with built-in renderers for table, text, image, video,
 * audio, and video_audio.  Every entry can be replaced or extended at runtime.
 */
import { Spinner } from '@fluentui/react-components'
import { AgentContentRenderer } from './AgentContentRenderer'
import type { DraftPost } from '../../services/marketingReview.service'

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface ArtifactRendererProps {
  /** The draft post to render */
  post: DraftPost
  /** Optional resolved artifact URI (from polling or realtime) */
  effectiveUri?: string | null
  /** Optional resolved MIME type */
  effectiveMime?: string | null
  /** Current artifact generation status */
  effectiveGenStatus?: string | null
}

export interface ArtifactRendererEntry {
  /** React component that renders this artifact type */
  component: React.ComponentType<ArtifactRendererProps>
  /** Human-readable label for the artifact type */
  label: string
}

// ---------------------------------------------------------------------------
// Registry internals
// ---------------------------------------------------------------------------

const _registry = new Map<string, ArtifactRendererEntry>()

/**
 * Register (or replace) a renderer for a given artifact type.
 *
 * `artifactType` is case-insensitive and stored in lower case.
 */
export function registerArtifactRenderer(
  artifactType: string,
  entry: ArtifactRendererEntry,
): void {
  _registry.set(artifactType.toLowerCase(), entry)
}

/**
 * Look up a registered renderer.  Returns `undefined` when no match is found,
 * which lets callers fall back to their own default.
 */
export function getArtifactRenderer(
  artifactType: string | undefined | null,
): ArtifactRendererEntry | undefined {
  if (!artifactType) return undefined
  return _registry.get(artifactType.toLowerCase())
}

// ---------------------------------------------------------------------------
// Built-in renderers
// ---------------------------------------------------------------------------

/** Table renderer — markdown → GFM table via AgentContentRenderer. */
function TableRenderer({ post }: ArtifactRendererProps) {
  // Prefer structured table_preview metadata if available
  const preview = post.artifact_metadata?.table_preview as
    | { columns?: string[]; rows?: Array<Record<string, string>> }
    | undefined

  if (preview?.columns?.length && preview?.rows?.length) {
    // Build a markdown table from the structured preview data
    const header = preview.columns.join(' | ')
    const separator = preview.columns.map(() => '---').join(' | ')
    const rows = preview.rows.map(
      (row) => preview.columns!.map((col) => String(row[col] || '—')).join(' | ')
    )
    const markdownTable = `| ${header} |\n| ${separator} |\n${rows.map((r) => `| ${r} |`).join('\n')}`
    const fullContent = post.text?.includes('**Master Theme') ? post.text : markdownTable
    return <AgentContentRenderer content={fullContent} data-testid="artifact-table-renderer" />
  }

  // Fallback: raw markdown table from post.text
  if (post.text) {
    return <AgentContentRenderer content={post.text} data-testid="artifact-table-renderer" />
  }

  return null
}

/** Plain text / general markdown renderer. */
function TextRenderer({ post }: ArtifactRendererProps) {
  return <AgentContentRenderer content={post.text} variant="default" data-testid="artifact-text-renderer" />
}

/** Image artifact renderer. */
function ImageRenderer({ post, effectiveUri, effectiveMime, effectiveGenStatus }: ArtifactRendererProps) {
  if (effectiveGenStatus === 'queued' || effectiveGenStatus === 'running') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', opacity: 0.7, fontSize: '0.82rem' }}>
        <Spinner size="tiny" />
        <span>Generating image…</span>
      </div>
    )
  }

  if (effectiveUri && effectiveMime?.startsWith('image/')) {
    return (
      <img
        src={effectiveUri}
        alt={`${post.artifact_type} asset`}
        style={{ maxWidth: '100%', maxHeight: '220px', borderRadius: '6px', objectFit: 'cover' }}
        data-testid="artifact-image-renderer"
      />
    )
  }

  if (effectiveGenStatus === 'failed') {
    return (
      <div style={{ fontSize: '0.84rem', color: 'var(--colorPaletteRedForeground1)' }} data-testid="artifact-error">
        Image generation failed. Adjust the request or retry.
      </div>
    )
  }

  return <AgentContentRenderer content={post.text} data-testid="artifact-text-renderer" />
}

/** Video artifact renderer. */
function VideoRenderer({ post, effectiveUri, effectiveMime, effectiveGenStatus }: ArtifactRendererProps) {
  if (effectiveGenStatus === 'queued' || effectiveGenStatus === 'running') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', opacity: 0.7, fontSize: '0.82rem' }}>
        <Spinner size="tiny" />
        <span>Generating video…</span>
      </div>
    )
  }

  if (effectiveUri) {
    return (
      <a
        href={effectiveUri}
        download
        style={{ fontSize: '0.82rem', color: 'var(--colorBrandForegroundLink)' }}
        data-testid="artifact-video-renderer"
      >
        ↓ Download video asset
      </a>
    )
  }

  return <AgentContentRenderer content={post.text} data-testid="artifact-text-renderer" />
}

/** Audio artifact renderer. */
function AudioRenderer({ post, effectiveUri, effectiveMime, effectiveGenStatus }: ArtifactRendererProps) {
  if (effectiveGenStatus === 'queued' || effectiveGenStatus === 'running') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', opacity: 0.7, fontSize: '0.82rem' }}>
        <Spinner size="tiny" />
        <span>Generating audio…</span>
      </div>
    )
  }

  if (effectiveUri) {
    return (
      <a
        href={effectiveUri}
        download
        style={{ fontSize: '0.82rem', color: 'var(--colorBrandForegroundLink)' }}
        data-testid="artifact-audio-renderer"
      >
        ↓ Download audio asset
      </a>
    )
  }

  return <AgentContentRenderer content={post.text} data-testid="artifact-text-renderer" />
}

/** Video+audio composite renderer. */
function VideoAudioRenderer(props: ArtifactRendererProps) {
  return <VideoRenderer {...props} />
}

/** Fallback renderer for unknown artifact types. */
function FallbackRenderer({ post }: ArtifactRendererProps) {
  return <AgentContentRenderer content={post.text} data-testid="artifact-fallback-renderer" />
}

// ---------------------------------------------------------------------------
// Register built-in renderers
// ---------------------------------------------------------------------------

registerArtifactRenderer('table', { component: TableRenderer, label: 'Content Calendar' })
registerArtifactRenderer('text', { component: TextRenderer, label: 'Text Content' })
registerArtifactRenderer('image', { component: ImageRenderer, label: 'Image Asset' })
registerArtifactRenderer('video', { component: VideoRenderer, label: 'Video Asset' })
registerArtifactRenderer('audio', { component: AudioRenderer, label: 'Audio Asset' })
registerArtifactRenderer('video_audio', { component: VideoAudioRenderer, label: 'Narrated Video' })

// ---------------------------------------------------------------------------
// Registry component — drop-in replacement for scattered rendering conditionals
// ---------------------------------------------------------------------------

export interface ArtifactPreviewRegistryProps extends ArtifactRendererProps {
  /** Artifact type to look up in the registry.  Falls back to post.artifact_type. */
  artifactType?: string | null
}

/**
 * Main registry component.  Looks up the renderer for the given artifact type
 * and delegates.  Falls back to `FallbackRenderer` for unregistered types.
 */
export function ArtifactPreviewRegistry({
  artifactType,
  post,
  effectiveUri,
  effectiveMime,
  effectiveGenStatus,
}: ArtifactPreviewRegistryProps) {
  const resolvedType = artifactType || post.artifact_type || 'text'
  const entry = getArtifactRenderer(resolvedType)
  const Renderer = entry?.component || FallbackRenderer

  return <Renderer post={post} effectiveUri={effectiveUri} effectiveMime={effectiveMime} effectiveGenStatus={effectiveGenStatus} />
}
