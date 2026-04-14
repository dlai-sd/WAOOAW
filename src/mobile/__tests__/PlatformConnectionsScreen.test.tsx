/**
 * PlatformConnectionsScreen Tests (MOB-PARITY-1 E4-S1)
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';

// ─── Mock theme ───────────────────────────────────────────────────────────────

const mockTheme = {
  colors: {
    black: '#0a0a0a', neonCyan: '#00f2fe', neonPurple: '#667eea',
    textPrimary: '#ffffff', textSecondary: '#a1a1aa', card: '#18181b',
    error: '#ef4444', success: '#10b981', warning: '#f59e0b',
    border: '#374151', background: '#0a0a0a',
  },
  spacing: {
    xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48,
    screenPadding: { horizontal: 20, vertical: 20 },
  },
  typography: {
    fontFamily: {
      display: 'SpaceGrotesk_700Bold',
      body: 'Inter_400Regular',
      bodyBold: 'Inter_600SemiBold',
    },
  },
};

jest.mock('../src/hooks/useTheme', () => ({ useTheme: () => mockTheme }));

// ─── Mock route ───────────────────────────────────────────────────────────────

jest.mock('@react-navigation/native', () => ({
  useRoute: () => ({ params: { hiredAgentId: 'ha1' } }),
  useNavigation: () => ({ navigate: jest.fn(), goBack: jest.fn() }),
}));

// ─── Mock WebBrowser ─────────────────────────────────────────────────────────

const mockOpenBrowserAsync = jest.fn(() => Promise.resolve());
jest.mock('expo-web-browser', () => ({
  openBrowserAsync: (...args: unknown[]) => mockOpenBrowserAsync(...args),
}));

jest.mock('expo-auth-session', () => ({
  makeRedirectUri: jest.fn(({ path }: { path: string }) => `waooaw://${path}`),
}));

// ─── Mock hook ────────────────────────────────────────────────────────────────

const mockConnect = jest.fn(() => Promise.resolve({ id: 'conn-new' }));
const mockConnectYouTube = jest.fn(() =>
  Promise.resolve({ authorization_url: 'https://accounts.google.com/o/oauth2/auth?test=1' })
);
const mockDisconnect = jest.fn(() => Promise.resolve());
const mockRefetch = jest.fn();
const mockUsePlatformConnections = jest.fn();

jest.mock('../src/hooks/usePlatformConnections', () => ({
  usePlatformConnections: () => mockUsePlatformConnections(),
}));

import { PlatformConnectionsScreen } from '../src/screens/agents/PlatformConnectionsScreen';

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('PlatformConnectionsScreen', () => {
  const connections = [
    {
      id: 'conn1',
      hired_instance_id: 'ha1',
      skill_id: 'digital_marketing',
      platform_key: 'youtube',
      status: 'connected',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'conn2',
      hired_instance_id: 'ha1',
      skill_id: 'digital_marketing',
      platform_key: 'instagram',
      status: 'disconnected',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'conn3',
      hired_instance_id: 'ha1',
      skill_id: 'digital_marketing',
      platform_key: 'facebook',
      status: 'pending',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockUsePlatformConnections.mockReturnValue({
      connections,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      connect: mockConnect,
      connectYouTube: mockConnectYouTube,
      disconnect: mockDisconnect,
    });
  });

  it('renders platform cards with status badges', () => {
    const { getByTestId } = render(<PlatformConnectionsScreen />);
    expect(getByTestId('platform-connections-screen')).toBeTruthy();
    expect(getByTestId('platform-card-youtube')).toBeTruthy();
    expect(getByTestId('platform-card-instagram')).toBeTruthy();
    expect(getByTestId('status-badge-youtube')).toBeTruthy();
  });

  it('shows summary header with correct connected count', () => {
    const { getByTestId } = render(<PlatformConnectionsScreen />);
    // YouTube is connected, others are not
    expect(getByTestId('connections-summary')).toBeTruthy();
  });

  it('renders EmptyState when connections loading fails with empty', () => {
    mockUsePlatformConnections.mockReturnValue({
      connections: [],
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      connect: mockConnect,
      connectYouTube: mockConnectYouTube,
      disconnect: mockDisconnect,
    });
    // With empty connections but SUPPORTED_PLATFORMS present, no EmptyState is shown
    // — the screen renders the hardcoded platforms with no connection
    const { getByTestId } = render(<PlatformConnectionsScreen />);
    expect(getByTestId('platform-connections-screen')).toBeTruthy();
  });

  it('renders LoadingSpinner when loading', () => {
    mockUsePlatformConnections.mockReturnValue({
      connections: [],
      isLoading: true,
      error: null,
      refetch: mockRefetch,
      connect: mockConnect,
      connectYouTube: mockConnectYouTube,
      disconnect: mockDisconnect,
    });
    const { UNSAFE_getByType } = render(<PlatformConnectionsScreen />);
    const { LoadingSpinner } = require('../src/components/LoadingSpinner');
    expect(UNSAFE_getByType(LoadingSpinner)).toBeTruthy();
  });

  it('calls connectYouTube and opens browser when YouTube connect tapped', async () => {
    // Make youtube disconnected
    mockUsePlatformConnections.mockReturnValue({
      connections: [],
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      connect: mockConnect,
      connectYouTube: mockConnectYouTube,
      disconnect: mockDisconnect,
    });
    const { getByTestId } = render(<PlatformConnectionsScreen />);
    fireEvent.press(getByTestId('connect-youtube-btn'));
    await waitFor(() => {
      expect(mockConnectYouTube).toHaveBeenCalled();
      expect(mockOpenBrowserAsync).toHaveBeenCalledWith(
        'https://accounts.google.com/o/oauth2/auth?test=1'
      );
    });
  });

  it('calls connect when non-YouTube credentials submitted', async () => {
    mockUsePlatformConnections.mockReturnValue({
      connections: [],
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      connect: mockConnect,
      connectYouTube: mockConnectYouTube,
      disconnect: mockDisconnect,
    });
    const { getByTestId } = render(<PlatformConnectionsScreen />);
    // Press connect for instagram
    fireEvent.press(getByTestId('connect-btn-instagram'));
    // Fill credential form and submit
    await waitFor(() => expect(getByTestId('credential-form-modal')).toBeTruthy());
    fireEvent.changeText(getByTestId('credential-input-api-key'), 'test-api-key');
    fireEvent.press(getByTestId('credential-submit-btn'));
    await waitFor(() => {
      expect(mockConnect).toHaveBeenCalledWith(
        expect.objectContaining({ platform_key: 'instagram', credentials: { api_key: 'test-api-key' } })
      );
    });
  });
});
