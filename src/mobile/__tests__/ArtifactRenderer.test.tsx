import React from 'react'
import { render } from '@testing-library/react-native'
import { ArtifactRenderer } from '@/components/ArtifactRenderer'
import type { DraftPost } from '@/services/marketingReview.service'

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      neonCyan: '#00f2fe',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
    },
    typography: {
      fontFamily: { display: 'SpaceGrotesk_700Bold', body: 'Inter_400Regular', bodyBold: 'Inter_600SemiBold' },
    },
  }),
}))

jest.mock('react-native/Libraries/Utilities/Platform', () => ({ OS: 'ios' }))

const makePost = (overrides: Partial<DraftPost>): DraftPost => ({
  post_id: 'p1',
  channel: 'youtube',
  text: 'test post',
  review_status: 'pending_review',
  ...overrides,
})

describe('ArtifactRenderer', () => {
  it('E2-S2-T1: renders artifact-image for image type', () => {
    const { getByTestId } = render(
      <ArtifactRenderer post={makePost({ artifact_type: 'image', artifact_uri: 'https://img.jpg' })} />
    )
    expect(getByTestId('artifact-image')).toBeTruthy()
  })

  it('E2-S2-T2: renders artifact-video with play text for video type', () => {
    const { getByTestId, getByText } = render(
      <ArtifactRenderer post={makePost({ artifact_type: 'video', artifact_uri: 'https://vid.mp4' })} />
    )
    expect(getByTestId('artifact-video')).toBeTruthy()
    expect(getByText('▶ Play video')).toBeTruthy()
  })

  it('E2-S2-T3: renders artifact-table for table type with valid JSON', () => {
    const { getByTestId } = render(
      <ArtifactRenderer
        post={makePost({ artifact_type: 'table', artifact_uri: '[{"col":"val"}]' })}
      />
    )
    expect(getByTestId('artifact-table')).toBeTruthy()
  })

  it('E2-S2-T4: shows generating text when status is running', () => {
    const { getByText } = render(
      <ArtifactRenderer
        post={makePost({ artifact_generation_status: 'running' })}
      />
    )
    expect(getByText('Generating artifact…')).toBeTruthy()
  })

  it('E2-S2-T5: shows failed text when status is failed', () => {
    const { getByText } = render(
      <ArtifactRenderer
        post={makePost({ artifact_generation_status: 'failed' })}
      />
    )
    expect(getByText('Artifact generation failed')).toBeTruthy()
  })

  it('E2-S2-T6: renders nothing for text type', () => {
    const { toJSON } = render(
      <ArtifactRenderer post={makePost({ artifact_type: 'text', artifact_uri: 'some text' })} />
    )
    expect(toJSON()).toBeNull()
  })
})
