/**
 * usePlatformConnections Hook Tests
 */

import { renderHook, waitFor, act } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const mockListConnections = jest.fn();
const mockCreateConnection = jest.fn();
const mockDeleteConnection = jest.fn();
const mockStartYouTubeOAuth = jest.fn();

jest.mock('../../src/services/platformConnections.service', () => ({
  listPlatformConnections: (...args: unknown[]) => mockListConnections(...args),
  createPlatformConnection: (...args: unknown[]) => mockCreateConnection(...args),
  deletePlatformConnection: (...args: unknown[]) => mockDeleteConnection(...args),
  startYouTubeOAuth: (...args: unknown[]) => mockStartYouTubeOAuth(...args),
}));

import { usePlatformConnections } from '../../src/hooks/usePlatformConnections';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const MOCK_CONNECTIONS = [
  { id: 'c1', hired_instance_id: 'ha1', skill_id: 'dma', platform_key: 'youtube', status: 'connected', created_at: '2026-01-01', updated_at: '2026-01-01' },
];

describe('usePlatformConnections', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns empty array when hiredAgentId is undefined', () => {
    const { result } = renderHook(() => usePlatformConnections(undefined), {
      wrapper: createWrapper(),
    });
    expect(result.current.connections).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it('fetches connections when hiredAgentId is provided', async () => {
    mockListConnections.mockResolvedValue(MOCK_CONNECTIONS);
    const { result } = renderHook(() => usePlatformConnections('ha1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.connections).toHaveLength(1);
    expect(mockListConnections).toHaveBeenCalledWith('ha1');
  });

  it('connect mutation calls createPlatformConnection', async () => {
    mockListConnections.mockResolvedValue(MOCK_CONNECTIONS);
    mockCreateConnection.mockResolvedValue(MOCK_CONNECTIONS[0]);

    const { result } = renderHook(() => usePlatformConnections('ha1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.connect({ skill_id: 'dma', platform_key: 'youtube' });
    });

    expect(mockCreateConnection).toHaveBeenCalledWith('ha1', { skill_id: 'dma', platform_key: 'youtube' });
  });

  it('connectYouTube mutation calls startYouTubeOAuth', async () => {
    mockListConnections.mockResolvedValue([]);
    mockStartYouTubeOAuth.mockResolvedValue({ authorization_url: 'https://oauth.google.com' });

    const { result } = renderHook(() => usePlatformConnections('ha1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.connectYouTube('https://redirect.uri');
    });

    expect(mockStartYouTubeOAuth).toHaveBeenCalledWith('https://redirect.uri');
  });

  it('disconnect mutation calls deletePlatformConnection', async () => {
    mockListConnections.mockResolvedValue(MOCK_CONNECTIONS);
    mockDeleteConnection.mockResolvedValue(undefined);

    const { result } = renderHook(() => usePlatformConnections('ha1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.disconnect('c1');
    });

    expect(mockDeleteConnection).toHaveBeenCalledWith('ha1', 'c1');
  });
});
