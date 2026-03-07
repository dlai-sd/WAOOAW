import { useState } from 'react'
import type { CSSProperties } from 'react'
import {
  Body1,
  Button,
  Card,
  CardHeader,
  Field,
  Input,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
} from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

type ApprovalRecord = {
  approval_id: string
  customer_id: string
  agent_id: string
  action: string
  correlation_id?: string | null
  purpose?: string | null
  notes?: string | null
  created_at?: string
  expires_at?: string | null
}

type DeliveryType = 'Trade Plan' | 'Content Draft' | 'Report' | 'Other'

function getDeliveryType(action: string): DeliveryType {
  const a = action.toLowerCase()
  if (a.includes('trade') || a.includes('trading') || a.includes('buy') || a.includes('sell')) return 'Trade Plan'
  if (a.includes('content') || a.includes('draft') || a.includes('post')) return 'Content Draft'
  if (a.includes('report')) return 'Report'
  return 'Other'
}

function deliveryTypeBadgeStyle(type: DeliveryType): CSSProperties {
  switch (type) {
    case 'Trade Plan':
      return { background: 'rgba(245,158,11,0.15)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.4)' }
    case 'Content Draft':
      return { background: 'rgba(0,242,254,0.1)', color: '#00f2fe', border: '1px solid rgba(0,242,254,0.3)' }
    case 'Report':
      return { background: 'rgba(102,126,234,0.15)', color: '#667eea', border: '1px solid rgba(102,126,234,0.4)' }
    default:
      return { background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.6)', border: '1px solid rgba(255,255,255,0.15)' }
  }
}

function buildContextPreview(record: ApprovalRecord): string {
  const type = getDeliveryType(record.action)
  if (type === 'Trade Plan' && record.purpose) {
    // purpose might be like "BUY RELIANCE · 10 shares · ₹2,450"
    return record.purpose.slice(0, 100)
  }
  if (type === 'Content Draft' && record.notes) {
    return record.notes.slice(0, 80)
  }
  if (record.purpose) return record.purpose.slice(0, 80)
  return record.action
}

function getExpiryInfo(expiresAt: string | null | undefined): { label: string; color: string } | null {
  if (!expiresAt) return null
  const expiry = new Date(expiresAt).getTime()
  const now = Date.now()
  const diffMs = expiry - now
  if (diffMs <= 0) return { label: 'Expired', color: '#ef4444' }

  const diffHours = diffMs / (1000 * 60 * 60)
  const h = Math.floor(diffHours)
  const m = Math.floor((diffHours - h) * 60)
  const label = `Expires in ${h}h ${m}m`

  if (diffHours < 2) return { label, color: '#ef4444' }
  if (diffHours < 12) return { label, color: '#f59e0b' }
  return { label, color: 'rgba(255,255,255,0.5)' }
}

export default function ApprovalsQueueScreen() {
  const [customerId, setCustomerId] = useState('')
  const [agentId, setAgentId] = useState('')
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)

  async function handleLoad() {
    setIsLoading(true)
    setError(null)
    try {
      const res = await gatewayApiClient.listApprovals({
        customer_id: customerId.trim() || undefined,
        agent_id: agentId.trim() || undefined,
        limit: 100,
      })
      setApprovals((res?.approvals || []) as ApprovalRecord[])
    } catch (e: unknown) {
      setError(e)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Approvals Queue</Text>
        <Body1>Pending and recent approvals with type badges and expiry countdown</Body1>
      </div>

      {!!error && <ApiErrorPanel title="Approvals queue error" error={error} />}

      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">Filters</Text>} />
        <div style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
          <Field label="Customer ID">
            <Input
              value={customerId}
              onChange={(_, d) => setCustomerId(d.value)}
              placeholder="CUST-..."
            />
          </Field>
          <Field label="Agent ID">
            <Input
              value={agentId}
              onChange={(_, d) => setAgentId(d.value)}
              placeholder="AGT-..."
            />
          </Field>
          <Button appearance="primary" onClick={() => void handleLoad()} disabled={isLoading}>
            Load
          </Button>
        </div>
      </Card>

      {isLoading && (
        <div style={{ padding: 16 }}>
          <Spinner label="Loading approvals..." />
        </div>
      )}

      {!isLoading && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Approval</TableHeaderCell>
              <TableHeaderCell>Type</TableHeaderCell>
              <TableHeaderCell>Action / Preview</TableHeaderCell>
              <TableHeaderCell>Agent</TableHeaderCell>
              <TableHeaderCell>Created</TableHeaderCell>
              <TableHeaderCell>Expires</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {approvals.map(record => {
              const deliveryType = getDeliveryType(record.action)
              const badgeStyle = deliveryTypeBadgeStyle(deliveryType)
              const contextPreview = buildContextPreview(record)
              const expiry = getExpiryInfo(record.expires_at)

              return (
                <TableRow key={record.approval_id}>
                  <TableCell>
                    <Text size={200}>{record.approval_id}</Text>
                  </TableCell>
                  <TableCell>
                    <span
                      style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        borderRadius: 12,
                        fontSize: 12,
                        ...badgeStyle,
                      }}
                    >
                      {deliveryType}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div>
                      <Text size={300} weight="semibold" style={{ display: 'block' }}>
                        {record.action}
                      </Text>
                      <Text size={200} style={{ opacity: 0.7, display: 'block' }}>
                        {contextPreview}
                      </Text>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Text size={200}>{record.agent_id}</Text>
                  </TableCell>
                  <TableCell>
                    <Text size={200}>
                      {record.created_at ? new Date(record.created_at).toLocaleString() : '—'}
                    </Text>
                  </TableCell>
                  <TableCell>
                    {expiry ? (
                      <Text size={200} style={{ color: expiry.color }}>
                        {expiry.label}
                      </Text>
                    ) : (
                      <Text size={200} style={{ opacity: 0.5 }}>—</Text>
                    )}
                  </TableCell>
                </TableRow>
              )
            })}
            {approvals.length === 0 && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Text>No approvals found.</Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
