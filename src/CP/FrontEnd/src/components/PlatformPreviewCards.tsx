import React from 'react'

interface PlatformPreviewProps {
  title: string
  text: string
  hashtags: string[]
  thumbnailUrl?: string
  channelName: string
}

export const YouTubePreviewCard: React.FC<PlatformPreviewProps> = ({
  title,
  text,
  hashtags,
  thumbnailUrl,
  channelName,
}) => (
  <div
    style={{
      background: '#0f0f0f',
      borderRadius: '12px',
      overflow: 'hidden',
      maxWidth: '360px',
      fontFamily: 'Roboto, sans-serif',
      border: '1px solid #272727',
    }}
    data-testid="youtube-preview-card"
  >
    <div
      style={{
        width: '100%',
        aspectRatio: '16/9',
        background: thumbnailUrl
          ? `url(${thumbnailUrl}) center/cover`
          : 'linear-gradient(135deg, #667eea, #00f2fe)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontSize: '48px',
      }}
    >
      {!thumbnailUrl && '▶'}
    </div>
    <div style={{ padding: '12px' }}>
      <div
        style={{
          color: '#f1f1f1',
          fontSize: '14px',
          fontWeight: 500,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          lineHeight: '20px',
          marginBottom: '8px',
        }}
      >
        {title}
      </div>
      <div style={{ color: '#aaa', fontSize: '12px', marginBottom: '4px' }}>
        {channelName}
      </div>
      <div style={{ color: '#aaa', fontSize: '12px' }}>
        0 views · Just now
      </div>
    </div>
  </div>
)

export const LinkedInPreviewCard: React.FC<PlatformPreviewProps> = ({
  title,
  text,
  hashtags,
  thumbnailUrl,
  channelName,
}) => (
  <div
    style={{
      background: '#fff',
      borderRadius: '8px',
      overflow: 'hidden',
      maxWidth: '552px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      border: '1px solid #e0e0e0',
      color: '#000',
    }}
    data-testid="linkedin-preview-card"
  >
    <div style={{ padding: '12px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #0077b5, #00a0dc)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: '20px',
            fontWeight: 600,
          }}
        >
          {channelName.charAt(0).toUpperCase()}
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '14px' }}>{channelName}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>Just now</div>
        </div>
      </div>
      <div style={{ fontSize: '14px', lineHeight: '20px', whiteSpace: 'pre-wrap', marginBottom: '8px' }}>
        {text.slice(0, 280)}
        {text.length > 280 && '...'}
      </div>
      {hashtags.length > 0 && (
        <div style={{ fontSize: '14px', color: '#0073b1', marginBottom: '8px' }}>
          {hashtags.join(' ')}
        </div>
      )}
    </div>
    {thumbnailUrl && (
      <div style={{ width: '100%', maxHeight: '300px', overflow: 'hidden' }}>
        <img
          src={thumbnailUrl}
          alt="Post thumbnail"
          style={{ width: '100%', height: 'auto', objectFit: 'cover' }}
        />
      </div>
    )}
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-around',
        padding: '8px 16px',
        borderTop: '1px solid #e0e0e0',
      }}
    >
      <div style={{ fontSize: '13px', color: '#666', display: 'flex', alignItems: 'center', gap: '4px' }}>
        👍 Like
      </div>
      <div style={{ fontSize: '13px', color: '#666', display: 'flex', alignItems: 'center', gap: '4px' }}>
        💬 Comment
      </div>
      <div style={{ fontSize: '13px', color: '#666', display: 'flex', alignItems: 'center', gap: '4px' }}>
        🔁 Repost
      </div>
      <div style={{ fontSize: '13px', color: '#666', display: 'flex', alignItems: 'center', gap: '4px' }}>
        📤 Send
      </div>
    </div>
  </div>
)

export const InstagramPreviewCard: React.FC<PlatformPreviewProps> = ({
  title,
  text,
  hashtags,
  thumbnailUrl,
  channelName,
}) => (
  <div
    style={{
      background: '#fff',
      borderRadius: '8px',
      overflow: 'hidden',
      maxWidth: '470px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      border: '1px solid #dbdbdb',
      color: '#000',
    }}
    data-testid="instagram-preview-card"
  >
    <div style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
      <div
        style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          background: 'linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: '16px',
          fontWeight: 600,
        }}
      >
        {channelName.charAt(0).toUpperCase()}
      </div>
      <div style={{ fontWeight: 600, fontSize: '14px' }}>{channelName}</div>
    </div>
    <div
      style={{
        width: '100%',
        aspectRatio: '1/1',
        background: thumbnailUrl
          ? `url(${thumbnailUrl}) center/cover`
          : 'linear-gradient(135deg, #f093fb, #f5576c)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontSize: '48px',
      }}
    >
      {!thumbnailUrl && '📷'}
    </div>
    <div style={{ padding: '12px 16px' }}>
      <div style={{ display: 'flex', gap: '16px', marginBottom: '8px' }}>
        <span style={{ fontSize: '24px' }}>❤️</span>
        <span style={{ fontSize: '24px' }}>💬</span>
        <span style={{ fontSize: '24px' }}>📤</span>
      </div>
      <div style={{ fontSize: '14px', marginBottom: '4px' }}>
        <span style={{ fontWeight: 600, marginRight: '4px' }}>{channelName}</span>
        <span>{text.slice(0, 150)}{text.length > 150 && '...'}</span>
      </div>
      {hashtags.length > 0 && (
        <div style={{ fontSize: '14px', color: '#00376b' }}>
          {hashtags.join(' ')}
        </div>
      )}
      <div style={{ fontSize: '12px', color: '#8e8e8e', marginTop: '8px' }}>
        Just now
      </div>
    </div>
  </div>
)
