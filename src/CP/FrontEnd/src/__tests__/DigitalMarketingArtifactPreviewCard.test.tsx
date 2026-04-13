import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DigitalMarketingArtifactPreviewCard } from '../components/DigitalMarketingArtifactPreviewCard'


describe('DigitalMarketingArtifactPreviewCard', () => {
  it('renders a table preview when table metadata is available', () => {
    render(
      <DigitalMarketingArtifactPreviewCard
        post={{
          post_id: 'post-1',
          channel: 'youtube',
          text: 'Review this content plan',
          review_status: 'pending_review',
          artifact_type: 'table',
          artifact_generation_status: 'ready',
          artifact_metadata: {
            table_preview: {
              columns: ['content_pillar', 'customer_angle'],
              rows: [{ content_pillar: 'Hook', customer_angle: 'Parents' }],
            },
          },
        }}
      />
    )

    expect(screen.getByText(/Requested asset: table/i)).toBeInTheDocument()
    expect(screen.getByText('Hook')).toBeInTheDocument()
    expect(screen.getByText('Parents')).toBeInTheDocument()
  })

  it('renders queued state copy for binary media requests', () => {
    render(
      <DigitalMarketingArtifactPreviewCard
        post={{
          post_id: 'post-2',
          channel: 'youtube',
          text: 'Review this short-form script',
          review_status: 'pending_review',
          artifact_type: 'video',
          artifact_generation_status: 'queued',
        }}
      />
    )

    expect(screen.getByText(/Status: queued/i)).toBeInTheDocument()
    expect(screen.getByText(/queued generation/i)).toBeInTheDocument()
  })

  it('E3-S1-T2: renders markdown table fallback when table_preview is missing but text contains GFM', () => {
    render(
      <DigitalMarketingArtifactPreviewCard
        post={{
          post_id: 'post-3',
          channel: 'youtube',
          text: '| # | Theme | Description |\n|---|-------|-------------|\n| 1 | Test | Test theme |',
          review_status: 'pending_review',
          artifact_type: 'table',
          artifact_generation_status: 'ready',
          // No artifact_metadata.table_preview
        }}
      />
    )

    // Should render the markdown table fallback
    expect(screen.getByText(/Requested asset: table/i)).toBeInTheDocument()
    // ReactMarkdown should convert the GFM to a table element
    const tableElement = document.querySelector('table')
    expect(tableElement).toBeInTheDocument()
  })

  it('E3-S2-T1: renders queued state for image artifact', () => {
    render(
      <DigitalMarketingArtifactPreviewCard
        post={{
          post_id: 'post-4',
          channel: 'youtube',
          text: 'Image description',
          review_status: 'pending_review',
          artifact_type: 'image',
          artifact_generation_status: 'queued',
        }}
      />
    )

    expect(screen.getByText(/Requested asset: image/i)).toBeInTheDocument()
    expect(screen.getByText(/queued generation/i)).toBeInTheDocument()
  })

  it('E3-S2-T2: renders failed state for video artifact', () => {
    render(
      <DigitalMarketingArtifactPreviewCard
        post={{
          post_id: 'post-5',
          channel: 'youtube',
          text: 'Video script',
          review_status: 'pending_review',
          artifact_type: 'video',
          artifact_generation_status: 'failed',
        }}
      />
    )

    expect(screen.getByText(/Requested asset: video/i)).toBeInTheDocument()
    expect(screen.getByText(/generation failed/i)).toBeInTheDocument()
  })

  it('E3-S2-T3: renders link for audio artifact with artifact_uri', () => {
    render(
      <DigitalMarketingArtifactPreviewCard
        post={{
          post_id: 'post-6',
          channel: 'youtube',
          text: 'Audio script',
          review_status: 'pending_review',
          artifact_type: 'audio',
          artifact_generation_status: 'ready',
          artifact_uri: 'https://example.com/audio.mp3',
        }}
      />
    )

    expect(screen.getByText(/Requested asset: audio/i)).toBeInTheDocument()
    const link = screen.getByText(/Open generated asset/i)
    expect(link).toBeInTheDocument()
    expect(link.getAttribute('href')).toBe('https://example.com/audio.mp3')
  })
})