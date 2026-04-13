/**
 * Universal Markdown Pipeline — single rendering entry point for all AI agent content.
 *
 * Replaces scattered ReactMarkdown / plain-text rendering across the app.
 * All content (tables, code blocks, images, links, lists) flows through one
 * pipeline with consistent styling and plugin support.
 *
 * Usage:
 *   <AgentContentRenderer content={post.text} />
 *   <AgentContentRenderer content={post.text} variant="compact" />
 */
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'

export type ContentVariant = 'default' | 'compact' | 'full'

export interface AgentContentRendererProps {
  /** Markdown or plain text content to render */
  content: string
  /** Visual density: 'compact' for inline cards, 'full' for detail views */
  variant?: ContentVariant
  /** Additional CSS class name for the container */
  className?: string
  /** Override inline styles on the root container */
  style?: React.CSSProperties
  /** Test ID for automation */
  'data-testid'?: string
}

const VARIANT_STYLES: Record<ContentVariant, React.CSSProperties> = {
  default: { fontSize: '0.9rem', lineHeight: 1.55 },
  compact: { fontSize: '0.82rem', lineHeight: 1.45 },
  full: { fontSize: '0.95rem', lineHeight: 1.65 },
}

/** Custom markdown component renderers with WAOOAW dark-theme table styling. */
const markdownComponents: Components = {
  table: ({ children, ...props }) => (
    <div style={{ overflowX: 'auto', margin: '0.5rem 0' }}>
      <table
        {...props}
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '0.82rem',
        }}
      >
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }) => (
    <thead {...props} style={{ borderBottom: '2px solid var(--colorNeutralStroke1, #444)' }}>
      {children}
    </thead>
  ),
  th: ({ children, ...props }) => (
    <th
      {...props}
      style={{
        textAlign: 'left',
        padding: '0.5rem 0.6rem',
        fontWeight: 600,
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </th>
  ),
  td: ({ children, ...props }) => (
    <td
      {...props}
      style={{
        padding: '0.45rem 0.6rem',
        borderBottom: '1px solid color-mix(in srgb, var(--colorNeutralStroke2, #333) 60%, transparent)',
      }}
    >
      {children}
    </td>
  ),
  code: ({ children, className, ...props }) => {
    const isBlock = className?.includes('language-')
    if (isBlock) {
      return (
        <pre
          style={{
            background: 'var(--colorNeutralBackground3, #1e1e1e)',
            borderRadius: '6px',
            padding: '0.75rem',
            overflowX: 'auto',
            fontSize: '0.82rem',
            lineHeight: 1.5,
            margin: '0.5rem 0',
          }}
        >
          <code className={className} {...props}>{children}</code>
        </pre>
      )
    }
    return (
      <code
        {...props}
        style={{
          background: 'var(--colorNeutralBackground3, #1e1e1e)',
          borderRadius: '3px',
          padding: '0.15rem 0.35rem',
          fontSize: '0.85em',
        }}
      >
        {children}
      </code>
    )
  },
  a: ({ children, href, ...props }) => (
    <a
      {...props}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      style={{ color: 'var(--colorBrandForegroundLink, #667eea)' }}
    >
      {children}
    </a>
  ),
  img: ({ src, alt, ...props }) => (
    <img
      {...props}
      src={src}
      alt={alt || 'Agent-generated image'}
      style={{
        maxWidth: '100%',
        maxHeight: '320px',
        borderRadius: '6px',
        objectFit: 'cover',
        margin: '0.4rem 0',
      }}
    />
  ),
  blockquote: ({ children, ...props }) => (
    <blockquote
      {...props}
      style={{
        borderLeft: '3px solid var(--colorBrandForeground1, #667eea)',
        margin: '0.5rem 0',
        padding: '0.25rem 0.75rem',
        opacity: 0.85,
      }}
    >
      {children}
    </blockquote>
  ),
}

export function AgentContentRenderer({
  content,
  variant = 'default',
  className,
  style,
  'data-testid': testId,
}: AgentContentRendererProps) {
  if (!content) return null

  const mergedStyle: React.CSSProperties = {
    ...VARIANT_STYLES[variant],
    ...style,
  }

  return (
    <div
      className={`agent-content-renderer ${className || ''}`.trim()}
      style={mergedStyle}
      data-testid={testId || 'agent-content-renderer'}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={markdownComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
