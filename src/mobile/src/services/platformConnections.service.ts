/**
 * Platform Connections Service (MOB-PARITY-1 E4-S1)
 *
 * Matches CP Frontend platformConnections.service.ts — same endpoint contract.
 * YouTube OAuth uses a separate endpoint from general platform connections.
 */

import cpApiClient from '../lib/cpApiClient';

export interface PlatformConnection {
  id: string;
  hired_instance_id: string;
  skill_id: string;
  customer_platform_credential_id?: string | null;
  platform_key: string;
  status?: string;
  connected_at?: string | null;
  last_verified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateConnectionBody {
  skill_id: string;
  platform_key: string;
  credentials?: Record<string, unknown>;
}

export async function listPlatformConnections(hiredAgentId: string): Promise<PlatformConnection[]> {
  const response = await cpApiClient.get<PlatformConnection[]>(
    `/cp/hired-agents/${hiredAgentId}/platform-connections`
  );
  const data = response.data;
  if (Array.isArray(data)) return data;
  if (Array.isArray((data as Record<string, unknown>)?.connections)) {
    return (data as { connections: PlatformConnection[] }).connections;
  }
  return [];
}

export async function createPlatformConnection(
  hiredAgentId: string,
  body: CreateConnectionBody
): Promise<PlatformConnection> {
  const response = await cpApiClient.post<PlatformConnection>(
    `/cp/hired-agents/${hiredAgentId}/platform-connections`,
    body
  );
  return response.data;
}

export async function deletePlatformConnection(
  hiredAgentId: string,
  connectionId: string
): Promise<void> {
  await cpApiClient.delete(
    `/cp/hired-agents/${hiredAgentId}/platform-connections/${connectionId}`
  );
}

export async function startYouTubeOAuth(redirectUri: string): Promise<{ authorization_url: string }> {
  const response = await cpApiClient.post<{ authorization_url: string }>(
    '/cp/youtube-connections/connect/start',
    { redirect_uri: redirectUri }
  );
  return response.data;
}
