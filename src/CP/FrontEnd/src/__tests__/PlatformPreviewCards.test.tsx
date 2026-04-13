import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { YouTubePreviewCard, LinkedInPreviewCard, InstagramPreviewCard } from '../components/PlatformPreviewCards'

/**
 * E8-S1-T1: YouTubePreviewCard renders with title and channel name.
 * E8-S1-T2: LinkedInPreviewCard renders with text and engagement bar.
 * E8-S1-T3: InstagramPreviewCard renders with hashtags.
 */
describe('Platform preview cards (E8-S1)', () => {
  it('renders YouTubePreviewCard with title and channel name', () => {
    render(
      <YouTubePreviewCard
        title="Test Video Title"
        text="Test video description"
        hashtags={['#test', '#video']}
        channelName="WAOOAW"
      />
    )

    expect(screen.getByTestId('youtube-preview-card')).toBeInTheDocument()
    expect(screen.getByText('Test Video Title')).toBeInTheDocument()
    expect(screen.getByText('WAOOAW')).toBeInTheDocument()
    expect(screen.getByText('0 views · Just now')).toBeInTheDocument()
  })

  it('renders LinkedInPreviewCard with text and engagement bar', () => {
    render(
      <LinkedInPreviewCard
        title="Test Post"
        text="Hello world from LinkedIn"
        hashtags={['#test', '#linkedin']}
        channelName="Test Business"
      />
    )

    expect(screen.getByTestId('linkedin-preview-card')).toBeInTheDocument()
    expect(screen.getByText('Hello world from LinkedIn')).toBeInTheDocument()
    expect(screen.getByText('Test Business')).toBeInTheDocument()
    expect(screen.getByText('👍 Like')).toBeInTheDocument()
    expect(screen.getByText('💬 Comment')).toBeInTheDocument()
    expect(screen.getByText('🔁 Repost')).toBeInTheDocument()
    expect(screen.getByText('📤 Send')).toBeInTheDocument()
  })

  it('renders InstagramPreviewCard with hashtags', () => {
    render(
      <InstagramPreviewCard
        title="Test Post"
        text="Amazing content here!"
        hashtags={['#ai', '#marketing']}
        channelName="TestPage"
      />
    )

    expect(screen.getByTestId('instagram-preview-card')).toBeInTheDocument()
    expect(screen.getByText(/Amazing content here!/)).toBeInTheDocument()
    expect(screen.getByText('#ai #marketing')).toBeInTheDocument()
    // Check for profile initials
    expect(screen.getAllByText('TestPage').length).toBeGreaterThan(0)
  })

  it('renders YouTubePreviewCard with thumbnail URL', () => {
    const thumbnailUrl = 'https://example.com/thumbnail.jpg'
    
    const { container } = render(
      <YouTubePreviewCard
        title="Video with thumbnail"
        text="Description"
        hashtags={[]}
        thumbnailUrl={thumbnailUrl}
        channelName="MyChannel"
      />
    )

    const thumbnailDiv = container.querySelector('div[style*="url(https://example.com/thumbnail.jpg)"]')
    expect(thumbnailDiv).toBeInTheDocument()
  })

  it('renders LinkedInPreviewCard with hashtags', () => {
    render(
      <LinkedInPreviewCard
        title="Post"
        text="Content"
        hashtags={['#business', '#growth']}
        channelName="Company"
      />
    )

    expect(screen.getByText('#business #growth')).toBeInTheDocument()
  })

  it('renders InstagramPreviewCard with long text truncated', () => {
    const longText = 'A'.repeat(200)
    
    render(
      <InstagramPreviewCard
        title="Test"
        text={longText}
        hashtags={[]}
        channelName="Account"
      />
    )

    // Should truncate at 150 chars and add ellipsis
    const displayedText = screen.getByText(/A+\.\.\./)
    expect(displayedText).toBeInTheDocument()
  })
})
