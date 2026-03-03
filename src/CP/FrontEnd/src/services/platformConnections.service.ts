// src/CP/FrontEnd/src/services/platformConnections.service.ts
// Calls CP BackEnd /api/cp/... routes added in CP-SKILLS-1 Iteration 1.
// Uses gatewayRequestJson for auth header injection + correlation ID.
//
// PLANT-SKILLS-1 It3: interface aligned with Plant BackEnd ConnectionResponse:
//   id (was connection_id), platform_key (was platform_name)
// CreateConnectionBody aligned with new CP BE CreatePlatformConnectionBody:
//   skill_id + platform_key + credentials (CP BE writes to Secret Manager)

import { gatewayRequestJson } from './gatewayApiClient'

export interface PlatformConnection {
  /** Matches Plant BackEnd ConnectionResponse.id */
  id: string
  hired_instance_id: string
  skill_id: string
  /** Matches Plant BackEnd ConnectionResponse.platform_key */
  platform_key: string
  status?: string
  connected_at?: string | null
  last_verified_at?: string | null
  created_at: string
  updated_at: string
}

export interface CreateConnectionBody {
  /** Must match the skill to which this platform is connected. */
  skill_id: string
  /** e.g. "delta_exchange", "instagram", "facebook" */
  platform_key: string
  /**
   * Raw credentials dict — CP BackEnd writes this to GCP Secret Manager
   * and stores only the opaque secret_ref in the database.
   * NEVER logged or persisted to DB by the frontend or CP BackEnd.
   */
  credentials?: Record<string, unknown>
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
