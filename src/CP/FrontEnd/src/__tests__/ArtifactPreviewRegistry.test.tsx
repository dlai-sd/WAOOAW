import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  ArtifactPreviewRegistry,
  registerArtifactRenderer,
  getArtifactRenderer,
} from '../components/rendering/ArtifactPreviewRegistry'
import type { DraftPost } from '../services/marketingReview.service'

// Helper: build a minimal DraftPost for testing
function makePost(overrides: Partial<DraftPost> = {}): DraftPost {
  return {
    post_id: 'test-post-1',
    channel: 'youtube',
    text: 'Test content',
    review_status: 'pending_review',
    ...overrides,
  }
}

describe('ArtifactPreviewRegistry', () => {
  it('renders table artifact with markdown table', () => {
    const tableMarkdown = [
      '| # | Theme | Description |',
      '|---|-------|-------------|',
      '| 1 | Bridal | Beauty tutorials |',
    ].join('\n')

    render(
      <ArtifactPreviewRegistry
        artifactType="table"
        post={makePost({ text: tableMarkdown, artifact_type: 'table' })}
      />
    )

    expect(screen.getByTestId('artifact-table-renderer')).toBeInTheDocument()
    expect(screen.getByText('Bridal')).toBeInTheDocument()
  })

  it('renders table artifact from structured table_preview metadata', () => {
    render(
      <ArtifactPreviewRegistry
        artifactType="table"
        post={makePost({
          text: 'raw text fallback',
          artifact_type: 'table',
          artifact_metadata: {
            table_preview: {
              columns: ['#', 'Theme', 'Frequency'],
              rows: [
                { '#': '1', 'Theme': 'SEO Tips', 'Frequency': 'weekly' },
                { '#': '2', 'Theme': 'Social Media', 'Frequency': 'daily' },
              ],
            },
          },
        })}
      />
    )

    expect(screen.getByTestId('artifact-table-renderer')).toBeInTheDocument()
    expect(screen.getByText('SEO Tips')).toBeInTheDocument()
    expect(screen.getByText('Social Media')).toBeInTheDocument()
  })

  it('renders text artifact with markdown formatting', () => {
    render(
      <ArtifactPreviewRegistry
        artifactType="text"
        post={makePost({ text: '**Bold** and _italic_', artifact_type: 'text' })}
      />
    )

    expect(screen.getByTestId('artifact-text-renderer')).toBeInTheDocument()
    expect(screen.getByText('Bold')).toBeInTheDocument()
  })

  it('renders image artifact when URI available', () => {
    render(
      <ArtifactPreviewRegistry
        artifactType="image"
        post={makePost({ artifact_type: 'image' })}
        effectiveUri="https://example.com/image.png"
        effectiveMime="image/png"
        effectiveGenStatus="ready"
      />
    )

    expect(screen.getByTestId('artifact-image-renderer')).toBeInTheDocument()
  })

  it('shows loading spinner for queued image artifact', () => {
    render(
      <ArtifactPreviewRegistry
        artifactType="image"
        post={makePost({ artifact_type: 'image' })}
        effectiveGenStatus="queued"
      />
    )

    expect(screen.getByText('Generating image…')).toBeInTheDocument()
  })

  it('shows error for failed artifact', () => {
    render(
      <ArtifactPreviewRegistry
        artifactType="image"
        post={makePost({ artifact_type: 'image', text: '' })}
        effectiveGenStatus="failed"
      />
    )

    expect(screen.getByTestId('artifact-error')).toBeInTheDocument()
  })

  it('falls back to text renderer for unknown artifact type', () => {
    render(
      <ArtifactPreviewRegistry
        artifactType="hologram"
        post={makePost({ text: 'Futuristic content' })}
      />
    )

    expect(screen.getByTestId('artifact-fallback-renderer')).toBeInTheDocument()
    expect(screen.getByText('Futuristic content')).toBeInTheDocument()
  })

  it('defaults to post.artifact_type when artifactType prop is not provided', () => {
    render(
      <ArtifactPreviewRegistry
        post={makePost({ text: 'Table data', artifact_type: 'table' })}
      />
    )

    expect(screen.getByTestId('artifact-table-renderer')).toBeInTheDocument()
  })
})

describe('Registry API', () => {
  it('getArtifactRenderer returns registered entry', () => {
    const entry = getArtifactRenderer('table')
    expect(entry).toBeDefined()
    expect(entry!.label).toBe('Content Calendar')
  })

  it('getArtifactRenderer is case-insensitive', () => {
    const entry = getArtifactRenderer('TABLE')
    expect(entry).toBeDefined()
    expect(entry!.label).toBe('Content Calendar')
  })

  it('getArtifactRenderer returns undefined for unregistered type', () => {
    const entry = getArtifactRenderer('hologram')
    expect(entry).toBeUndefined()
  })

  it('registerArtifactRenderer can register custom renderer', () => {
    const CustomRenderer = () => <div data-testid="custom-renderer">Custom</div>
    registerArtifactRenderer('chart', { component: CustomRenderer, label: 'Chart' })

    const entry = getArtifactRenderer('chart')
    expect(entry).toBeDefined()
    expect(entry!.label).toBe('Chart')

    // Render through registry
    render(
      <ArtifactPreviewRegistry
        artifactType="chart"
        post={makePost()}
      />
    )
    expect(screen.getByTestId('custom-renderer')).toBeInTheDocument()
  })

  it('all built-in artifact types are registered', () => {
    const builtinTypes = ['table', 'text', 'image', 'video', 'audio', 'video_audio']
    for (const type of builtinTypes) {
      expect(getArtifactRenderer(type)).toBeDefined()
    }
  })
})

describe('Customer scenario: DMA content calendar on CP portal', () => {
  it('customer asks "show me a content calendar" — table renders correctly', () => {
    // Simulates: backend returns a table artifact from the DMA agent
    // after customer says "show me a content calendar for my yoga studio"
    const post = makePost({
      post_id: 'dma-cal-001',
      channel: 'youtube',
      artifact_type: 'table',
      text: [
        '**Master Theme:** Yoga Studio Growth',
        '',
        '| # | Theme | Description | Frequency |',
        '|---|-------|-------------|-----------|',
        '| 1 | Morning Routines | 10-min sunrise yoga flows | weekly |',
        '| 2 | Beginner Guides | Accessible yoga for newcomers | weekly |',
        '| 3 | Teacher Spotlights | Instructor stories and tips | bi-weekly |',
      ].join('\n'),
      hashtags: ['#yoga', '#wellness'],
      review_status: 'pending_review',
    })

    render(<ArtifactPreviewRegistry artifactType="table" post={post} />)

    // Table must render as HTML table, NOT as a YouTube video card
    const renderer = screen.getByTestId('artifact-table-renderer')
    expect(renderer).toBeInTheDocument()

    // Verify table structure
    const table = renderer.querySelector('table')
    expect(table).not.toBeNull()

    // Verify content
    expect(screen.getByText('Morning Routines')).toBeInTheDocument()
    expect(screen.getByText('Beginner Guides')).toBeInTheDocument()
    expect(screen.getByText('Teacher Spotlights')).toBeInTheDocument()
  })

  it('customer sees video post — renders as text (not table)', () => {
    const post = makePost({
      post_id: 'dma-vid-001',
      channel: 'youtube',
      artifact_type: 'video',
      text: 'Check out this amazing yoga morning routine!',
      review_status: 'pending_review',
    })

    render(<ArtifactPreviewRegistry artifactType="video" post={post} />)

    // Should NOT render a table
    expect(screen.queryByTestId('artifact-table-renderer')).not.toBeInTheDocument()
    // Should render text content
    expect(screen.getByText('Check out this amazing yoga morning routine!')).toBeInTheDocument()
  })
})
