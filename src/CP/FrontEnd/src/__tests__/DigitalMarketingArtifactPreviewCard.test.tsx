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
})