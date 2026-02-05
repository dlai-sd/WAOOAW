import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { expect, test } from 'vitest'

import { AuthProvider, useAuth } from './AuthContext'

function Probe() {
  const { isLoading } = useAuth()
  return <div>{isLoading ? 'loading' : 'ready'}</div>
}

test('AuthProvider clears isLoading after initial storage sync', async () => {
  localStorage.removeItem('pp_access_token')

  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  )

  await waitFor(() => {
    expect(screen.getByText('ready')).toBeInTheDocument()
  })
})
