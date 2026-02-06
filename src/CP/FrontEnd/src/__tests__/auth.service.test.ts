import { describe, it, expect, vi, beforeEach } from 'vitest';

let authService: (typeof import('../services/auth.service'))['authService']

describe('auth.service', () => {
  beforeEach(async () => {
    localStorage.clear();
    vi.resetModules();
    ;({ authService } = await import('../services/auth.service'));
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

  it('fails closed when JWT is expired (clears cp_access_token)', async () => {
    const nowSeconds = Math.floor(Date.now() / 1000)
    const header = btoa(JSON.stringify({ alg: 'none', typ: 'JWT' })).replace(/=+$/g, '')
    const payload = btoa(
      JSON.stringify({ user_id: '1', email: 'test@example.com', token_type: 'access', exp: nowSeconds - 10, iat: nowSeconds - 100 })
    )
      .replace(/=+$/g, '')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
    const token = `${header}.${payload}.sig`

    localStorage.setItem('cp_access_token', token)

    vi.resetModules()
    ;({ authService } = await import('../services/auth.service'))

    expect(authService.isAuthenticated()).toBe(false)
    expect(localStorage.getItem('cp_access_token')).toBeNull()
  })

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
    expect(localStorage.getItem('cp_access_token')).toBe('token123');
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
      expires_in: 3600
    });

    const tokens = authService.handleOAuthCallback();
    expect(tokens).toBeTruthy();
    expect(tokens!.access_token).toBe('test_token');
  });
});
