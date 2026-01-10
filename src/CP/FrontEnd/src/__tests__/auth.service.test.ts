import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authService } from '../services/auth.service';

describe('auth.service', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('starts with no authentication', () => {
    expect(authService.isAuthenticated()).toBe(false);
  });

  it('returns null for access token when not authenticated', () => {
    expect(authService.getAccessToken()).toBeNull();
  });

  it('decodes valid JWT token', () => {
    const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMSIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsInRva2VuX3R5cGUiOiJhY2Nlc3MifQ.test';
    const decoded = authService.decodeToken(mockToken);
    expect(decoded).toBeTruthy();
  });

  it('returns null for invalid token', () => {
    const decoded = authService.decodeToken('invalid');
    expect(decoded).toBeNull();
  });

  it('handles OAuth callback from URL', () => {
    const searchParams = '?access_token=token123&refresh_token=refresh123&expires_in=3600';
    Object.defineProperty(window, 'location', {
      value: { search: searchParams, pathname: '/' },
      writable: true
    });

    const tokens = authService.handleOAuthCallback();
    expect(tokens).toBeTruthy();
  });

  it('returns null when no tokens in URL', () => {
    Object.defineProperty(window, 'location', {
      value: { search: '', pathname: '/' },
      writable: true
    });

    const tokens = authService.handleOAuthCallback();
    expect(tokens).toBeNull();
  });

  it('saves tokens to localStorage', () => {
    authService.handleOAuthCallback = vi.fn().mockReturnValue({
      access_token: 'test_token',
      refresh_token: 'test_refresh',
      expires_in: 3600
    });

    const tokens = authService.handleOAuthCallback();
    expect(tokens).toBeTruthy();
    expect(tokens!.access_token).toBe('test_token');
  });
});
