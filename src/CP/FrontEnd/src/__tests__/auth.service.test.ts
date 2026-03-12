import { describe, it, expect, vi, beforeEach } from 'vitest';

let authService: (typeof import('../services/auth.service'))['authService']
const SESSION_HINT_STORAGE_KEY = 'waooaw:session-restorable'

describe('auth.service', () => {
  beforeEach(async () => {
    localStorage.clear();
    sessionStorage.clear();
    vi.resetModules();
    vi.restoreAllMocks();
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

  it('clears legacy stored tokens on startup', async () => {
    localStorage.setItem('cp_access_token', 'legacy-access')
    localStorage.setItem('access_token', 'legacy-access-2')
    localStorage.setItem('refresh_token', 'legacy-refresh')
    localStorage.setItem('token_expires_at', '999999999')

    vi.resetModules()
    ;({ authService } = await import('../services/auth.service'))

    expect(authService.isAuthenticated()).toBe(false)
    expect(localStorage.getItem('cp_access_token')).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
    expect(localStorage.getItem('token_expires_at')).toBeNull()
  })

  it('skips silent refresh when no session hint exists', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')

    await expect(authService.silentRefresh()).resolves.toBeNull()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('allows forced silent refresh without a session hint', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: 'forced-refresh-token',
          token_type: 'bearer',
          expires_in: 3600,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      )
    )

    await expect(authService.silentRefresh(true)).resolves.toBe('forced-refresh-token')
    expect(authService.getAccessToken()).toBe('forced-refresh-token')
    expect(localStorage.getItem(SESSION_HINT_STORAGE_KEY)).toBe('1')
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
    expect(authService.getAccessToken()).toBe('token123');
    expect(localStorage.getItem(SESSION_HINT_STORAGE_KEY)).toBe('1');
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
    authService.setTokens({
      access_token: 'test_token',
      expires_in: 3600,
      token_type: 'bearer'
    });

    expect(authService.getAccessToken()).toBe('test_token');
    expect(localStorage.getItem(SESSION_HINT_STORAGE_KEY)).toBe('1');
  });
});
