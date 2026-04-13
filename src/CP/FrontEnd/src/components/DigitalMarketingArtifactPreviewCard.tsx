import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { DraftPost } from '../services/marketingReview.service'

function renderTablePreview(post: DraftPost) {
  const preview = post.artifact_metadata?.table_preview as
    | { columns?: string[]; rows?: Array<Record<string, string>> }
    | undefined

  if (!preview?.columns?.length || !preview?.rows?.length) {
    // Fallback: render raw markdown table if post.text contains pipe characters
    if (post.text && post.text.includes('|')) {
      return (
        <div style={{ overflowX: 'auto' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{post.text}</ReactMarkdown>
        </div>
      )
    }
    return null
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
        <thead>
          <tr>
            {preview.columns.map((column) => (
              <th key={column} style={{ textAlign: 'left', padding: '0.45rem', borderBottom: '1px solid var(--colorNeutralStroke2)' }}>
                {column.replace(/_/g, ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {preview.rows.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`}>
              {preview.columns?.map((column) => (
                <td key={`${rowIndex}-${column}`} style={{ padding: '0.45rem', borderBottom: '1px solid color-mix(in srgb, var(--colorNeutralStroke2) 60%, transparent)' }}>
                  {String(row?.[column] || '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function DigitalMarketingArtifactPreviewCard({ post }: { post: DraftPost }) {
  const artifactType = post.artifact_type || 'text'
  const artifactStatus = post.artifact_generation_status || 'not_requested'
  const hasGeneratedArtifacts = Boolean(post.generated_artifacts?.length)

  if (artifactType === 'text' && artifactStatus === 'not_requested' && !hasGeneratedArtifacts) {
    return null
  }

  const tablePreview = artifactType === 'table' ? renderTablePreview(post) : null

  return (
    <div style={{ marginBottom: '0.75rem', padding: '0.75rem', borderRadius: '10px', background: 'color-mix(in srgb, var(--colorNeutralBackground2) 82%, transparent)', display: 'grid', gap: '0.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
        <div style={{ fontWeight: 600 }}>Requested asset: {artifactType.replace(/_/g, ' ')}</div>
        <div style={{ opacity: 0.75, fontSize: '0.82rem' }}>Status: {artifactStatus}</div>
      </div>
      {tablePreview}
      {artifactType !== 'table' && artifactStatus === 'queued' ? (
        <div style={{ fontSize: '0.84rem', opacity: 0.82 }}>
          The DMA has accepted this media request and queued generation. Review remains explicit and publish stays blocked until the asset is ready.
        </div>
      ) : null}
      {artifactType !== 'table' && artifactStatus === 'failed' ? (
        <div style={{ fontSize: '0.84rem', color: 'var(--colorPaletteRedForeground1)' }}>
          Media generation failed. Adjust the request or retry after reviewing the asset requirements.
        </div>
      ) : null}
      {(post.artifact_preview_uri || post.artifact_uri) && artifactType !== 'table' ? (
        <a
          href={post.artifact_preview_uri || post.artifact_uri || '#'}
          target="_blank"
          rel="noreferrer"
          style={{ color: 'var(--colorBrandForegroundLink)', fontSize: '0.84rem' }}
        >
          Open generated asset
        </a>
      ) : null}
    </div>
  )
}