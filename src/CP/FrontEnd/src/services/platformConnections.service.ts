// src/CP/FrontEnd/src/services/platformConnections.service.ts
// Calls CP BackEnd /api/cp/... routes added in CP-SKILLS-1 Iteration 1.
// Uses gatewayRequestJson for auth header injection + correlation ID.

import { gatewayRequestJson } from './gatewayApiClient'

export interface PlatformConnection {
  connection_id: string
  platform_name: string
  connection_type: string
  status?: string
  metadata?: Record<string, unknown>
}

export interface CreateConnectionBody {
  platform_name: string
  connection_type: string
  credentials?: Record<string, unknown>
  metadata?: Record<string, unknown>
}

/**
 * List all platform connections for a hired agent.
 * Calls: GET /api/cp/hired-agents/{hired_instance_id}/platform-connections
 */
export async function listPlatformConnections(
  hiredInstanceId: string
): Promise<PlatformConnection[]> {
  const data = await gatewayRequestJson<unknown>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/platform-connections`
  )
  if (Array.isArray(data)) return data as PlatformConnection[]
  if (Array.isArray((data as any)?.connections)) return (data as any).connections as PlatformConnection[]
  return []
}

/**
 * Create a new platform connection.
 * Calls: POST /api/cp/hired-agents/{hired_instance_id}/platform-connections
 */
export async function createPlatformConnection(
  hiredInstanceId: string,
  body: CreateConnectionBody
): Promise<PlatformConnection> {
  return gatewayRequestJson<PlatformConnection>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/platform-connections`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }
  )
}

/**
 * Delete a platform connection.
 * Calls: DELETE /api/cp/hired-agents/{hired_instance_id}/platform-connections/{connection_id}
 */
export async function deletePlatformConnection(
  hiredInstanceId: string,
  connectionId: string
): Promise<void> {
  await gatewayRequestJson<unknown>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/platform-connections/${encodeURIComponent(connectionId)}`,
    { method: 'DELETE' }
  )
}
