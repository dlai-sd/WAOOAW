import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

// jsdom does not provide ResizeObserver; Fluent UI uses it for layout reflow.
if (typeof (globalThis as any).ResizeObserver === 'undefined') {
  ;(globalThis as any).ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}

// Cleanup after each test
afterEach(() => {
  cleanup()
})
