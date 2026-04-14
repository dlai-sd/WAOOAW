/**
 * usePlatformConnections Hook (MOB-PARITY-1 E4-S1)
 *
 * React Query wrapper for platform connections management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listPlatformConnections,
  createPlatformConnection,
  deletePlatformConnection,
  startYouTubeOAuth,
  PlatformConnection,
  CreateConnectionBody,
} from '../services/platformConnections.service';

export interface UsePlatformConnectionsResult {
  connections: PlatformConnection[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
  connect: (body: CreateConnectionBody) => Promise<PlatformConnection>;
  connectYouTube: (redirectUri: string) => Promise<{ authorization_url: string }>;
  disconnect: (connectionId: string) => Promise<void>;
}

export function usePlatformConnections(hiredAgentId: string | undefined): UsePlatformConnectionsResult {
  const queryClient = useQueryClient();
  const queryKey = ['platformConnections', hiredAgentId];

  const query = useQuery<PlatformConnection[]>({
    queryKey,
    queryFn: () => listPlatformConnections(hiredAgentId!),
    enabled: !!hiredAgentId,
    staleTime: 1000 * 60 * 5,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
  });

  const connectMutation = useMutation({
    mutationFn: (body: CreateConnectionBody) =>
      createPlatformConnection(hiredAgentId!, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  const connectYouTubeMutation = useMutation({
    mutationFn: (redirectUri: string) => startYouTubeOAuth(redirectUri),
  });

  const disconnectMutation = useMutation({
    mutationFn: (connectionId: string) =>
      deletePlatformConnection(hiredAgentId!, connectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    connections: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: () => queryClient.invalidateQueries({ queryKey }),
    connect: (body: CreateConnectionBody) => connectMutation.mutateAsync(body),
    connectYouTube: (redirectUri: string) => connectYouTubeMutation.mutateAsync(redirectUri),
    disconnect: (connectionId: string) => disconnectMutation.mutateAsync(connectionId),
  };
}
