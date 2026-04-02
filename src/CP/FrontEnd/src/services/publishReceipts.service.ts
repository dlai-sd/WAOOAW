import { gatewayRequestJson } from './gatewayApiClient'

export interface PublishReceipt {
  id: string
  hired_instance_id: string
  platform_key: string
  published_at: string
  status: string
  platform_url?: string
  error_message?: string
}

export async function listPublishReceipts(hiredInstanceId: string): Promise<PublishReceipt[]> {
  const data = await gatewayRequestJson<unknown>(
    `/cp/publish-receipts/${encodeURIComponent(hiredInstanceId)}`,
    { method: 'GET' }
  )
  if (Array.isArray(data)) return data as PublishReceipt[]
  if (Array.isArray((data as any)?.items)) return (data as any).items as PublishReceipt[]
  return []
}
