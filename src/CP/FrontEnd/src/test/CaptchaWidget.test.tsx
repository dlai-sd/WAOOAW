import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, act } from '@testing-library/react'
import CaptchaWidget from '../components/auth/CaptchaWidget'

function flushMicrotasks() {
  return act(async () => {
    await Promise.resolve()
  })
}

describe('CaptchaWidget', () => {
  beforeEach(() => {
    ;(window as any).turnstile = {
      render: vi.fn(() => 'widget-1'),
      remove: vi.fn(),
      reset: vi.fn(),
    }
  })

  it('renders Turnstile only once across rerenders (prevents flicker)', async () => {
    const onToken = vi.fn()
    const onError = vi.fn()

    const view = render(<CaptchaWidget siteKey="test-site-key" onToken={onToken} onError={onError} />)
    await flushMicrotasks()

    view.rerender(<CaptchaWidget siteKey="test-site-key" onToken={onToken} onError={onError} />)
    await flushMicrotasks()

    expect((window as any).turnstile.render).toHaveBeenCalledTimes(1)
  })

  it('cleans up widget on unmount', async () => {
    const onToken = vi.fn()
    const onError = vi.fn()

    const view = render(<CaptchaWidget siteKey="test-site-key" onToken={onToken} onError={onError} />)
    await flushMicrotasks()

    view.unmount()
    expect((window as any).turnstile.remove).toHaveBeenCalledWith('widget-1')
  })
})
