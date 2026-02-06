import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'

import ApiErrorPanel from './ApiErrorPanel'
import { GatewayApiError } from '../services/gatewayApiClient'

test('ApiErrorPanel renders Plant-style reason/correlation/details', () => {
  const error = new GatewayApiError('Usage limit denied', {
    status: 429,
    correlationId: 'corr-1',
    problem: {
      title: 'Usage Limit Denied',
      detail: 'monthly budget exceeded',
      correlation_id: 'corr-1',
      reason: 'monthly_budget_exceeded',
      details: {
        window_resets_at: '2026-03-01T00:00:00Z'
      }
    }
  })

  render(<ApiErrorPanel title="Test" error={error} />)

  expect(screen.getByText('Test')).toBeInTheDocument()
  expect(screen.getByText(/429:/)).toBeInTheDocument()
  expect(screen.getByText(/Reason: monthly_budget_exceeded/)).toBeInTheDocument()
  expect(screen.getByText(/Correlation: corr-1/)).toBeInTheDocument()
  expect(screen.getByText(/window_resets_at/)).toBeInTheDocument()
})
