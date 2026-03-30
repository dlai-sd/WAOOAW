import { afterEach, describe, expect, it } from 'vitest';

import {
  beginYouTubeOAuthFlow,
  clearPendingYouTubeOAuthContext,
  clearYouTubeOAuthResult,
  getStoredYouTubeOAuthState,
  getYouTubeOAuthCallbackUri,
  readPendingYouTubeOAuthContext,
  readYouTubeOAuthResult,
  storeYouTubeOAuthResult,
} from '../utils/youtubeOAuthFlow';

describe('youtubeOAuthFlow', () => {
  afterEach(() => {
    window.sessionStorage.clear();
  });

  it('persists callback context across the OAuth redirect', () => {
    beginYouTubeOAuthFlow({
      state: 'oauth-state-123',
      source: 'activation-wizard',
      returnTo: '/my-agents',
      redirectUri: 'https://cp.demo.waooaw.com/auth/youtube/callback',
      hiredInstanceId: 'HAI-123',
      skillId: 'skill-youtube',
    });

    expect(getStoredYouTubeOAuthState()).toBe('oauth-state-123');
    expect(readPendingYouTubeOAuthContext()).toEqual({
      state: 'oauth-state-123',
      source: 'activation-wizard',
      returnTo: '/my-agents',
      redirectUri: 'https://cp.demo.waooaw.com/auth/youtube/callback',
      hiredInstanceId: 'HAI-123',
      skillId: 'skill-youtube',
    });

    clearPendingYouTubeOAuthContext();

    expect(getStoredYouTubeOAuthState()).toBeNull();
    expect(readPendingYouTubeOAuthContext()).toBeNull();
  });

  it('stores the completed connection result for post-redirect resume', () => {
    storeYouTubeOAuthResult({
      source: 'hire-setup',
      returnTo: '/hire-setup',
      subscriptionId: 'SUB-123',
      hiredInstanceId: 'HAI-123',
      connection: {
        id: 'conn-1',
        customer_id: 'cust-1',
        platform_key: 'youtube',
        display_name: 'My Channel',
        granted_scopes: ['youtube.upload'],
        verification_status: 'verified',
        connection_status: 'connected',
        created_at: '2026-03-30T11:00:00Z',
        updated_at: '2026-03-30T11:00:00Z',
      },
      message: 'Connected My Channel',
    });

    expect(readYouTubeOAuthResult()).toEqual({
      source: 'hire-setup',
      returnTo: '/hire-setup',
      subscriptionId: 'SUB-123',
      hiredInstanceId: 'HAI-123',
      connection: {
        id: 'conn-1',
        customer_id: 'cust-1',
        platform_key: 'youtube',
        display_name: 'My Channel',
        granted_scopes: ['youtube.upload'],
        verification_status: 'verified',
        connection_status: 'connected',
        created_at: '2026-03-30T11:00:00Z',
        updated_at: '2026-03-30T11:00:00Z',
      },
      message: 'Connected My Channel',
    });

    clearYouTubeOAuthResult();

    expect(readYouTubeOAuthResult()).toBeNull();
  });

  it('builds the public callback URL from the current origin', () => {
    expect(getYouTubeOAuthCallbackUri()).toBe('http://localhost:3000/auth/youtube/callback');
  });
});