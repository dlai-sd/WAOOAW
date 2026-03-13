import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import type { ReactNode } from 'react'

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  Link: ({ children, to, className }: { children: ReactNode; to: string; className?: string }) => (
    <a href={to} className={className}>{children}</a>
  ),
  useLocation: () => ({ pathname: '/' }),
}))

// Mock the logo image
vi.mock('../Waooaw-Logo.png', () => ({ default: 'logo.png' }))

import Layout from '../components/Layout'

function renderLayout() {
  return render(
    <Layout theme="dark" onThemeToggle={() => {}} showHelpBoxes={true} onHelpToggle={() => {}} onLogout={() => {}}>
      <div>content</div>
    </Layout>
  )
}

test('help toggle is rendered in the sidebar footer', () => {
  const onHelpToggle = vi.fn()

  render(
    <Layout theme="dark" onThemeToggle={() => {}} showHelpBoxes={true} onHelpToggle={onHelpToggle} onLogout={() => {}}>
      <div>content</div>
    </Layout>
  )

  expect(screen.getByTestId('pp-help-toggle')).toBeInTheDocument()
  expect(screen.getByText('Hide Help')).toBeInTheDocument()
})

test('E7-S1-T1: Nav shows "Usage Events" for /customers route', () => {
  renderLayout()
  expect(screen.getByText('Usage Events')).toBeInTheDocument()
})

test('E7-S1-T2: Nav shows "Governor Console" for /governor route', () => {
  renderLayout()
  expect(screen.getByText('Governor Console')).toBeInTheDocument()
})

test('E7-S1: "Customers" label is not present in nav (renamed to Usage Events)', () => {
  renderLayout()
  // The old label "Customers" should not appear as a standalone nav link
  const navLinks = screen.queryAllByRole('link', { name: /^Customers$/ })
  expect(navLinks).toHaveLength(0)
})

test('E7-S1: "Governor" label is not present in nav (renamed to Governor Console)', () => {
  renderLayout()
  const navLinks = screen.queryAllByRole('link', { name: /^Governor$/ })
  expect(navLinks).toHaveLength(0)
})

test('E8-S1-T1: Nav shows "Operations" section header', () => {
  renderLayout()
  expect(screen.getByText('Operations')).toBeInTheDocument()
})

test('E8-S1-T2: "Draft Review" present in nav; "Review Queue" not present as nav link', () => {
  renderLayout()
  expect(screen.getByText('Draft Review')).toBeInTheDocument()
  const reviewQueueLinks = screen.queryAllByRole('link', { name: /^Review Queue$/ })
  expect(reviewQueueLinks).toHaveLength(0)
})
