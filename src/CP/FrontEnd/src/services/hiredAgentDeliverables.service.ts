import { gatewayRequestJson } from './gatewayApiClient'

export type Deliverable = {
  deliverable_id: string
  hired_instance_id: string
  goal_instance_id: string
  goal_template_id: string

  title: string
  payload: Record<string, unknown>

  review_status: 'pending_review' | 'approved' | 'rejected' | string
  review_notes?: string | null
  approval_id?: string | null

  execution_status: 'not_executed' | 'executed' | string
  executed_at?: string | null

  created_at?: string | null
  updated_at?: string | null
}

export type DeliverablesListResponse = {
  hired_instance_id: string
  deliverables: Deliverable[]
}

export type ReviewDeliverableInput = {
  decision: 'approved' | 'rejected'
  notes?: string | null
  approval_id?: string | null
}

export type ReviewDeliverableResponse = {
  deliverable_id: string
  review_status: string
  approval_id?: string | null
  updated_at?: string | null
}

export async function listHiredAgentDeliverables(hiredInstanceId: string): Promise<DeliverablesListResponse> {
  return gatewayRequestJson<DeliverablesListResponse>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/deliverables`,
    { method: 'GET' }
  )
}

export async function reviewHiredAgentDeliverable(
  deliverableId: string,
  input: ReviewDeliverableInput
): Promise<ReviewDeliverableResponse> {
  return gatewayRequestJson<ReviewDeliverableResponse>(
    `/cp/hired-agents/deliverables/${encodeURIComponent(deliverableId)}/review`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input)
    }
  )
}
