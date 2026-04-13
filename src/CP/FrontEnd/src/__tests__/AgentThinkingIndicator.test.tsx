import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AgentThinkingIndicator } from '../components/rendering/AgentThinkingIndicator'

describe('AgentThinkingIndicator', () => {
  it('renders animated thinking indicator with default test id', () => {
    render(<AgentThinkingIndicator />)
    expect(screen.getByTestId('agent-thinking-indicator')).toBeInTheDocument()
  })

  it('renders with custom message', () => {
    render(<AgentThinkingIndicator message="DMA agent is analyzing your brief" />)
    expect(screen.getByText('DMA agent is analyzing your brief')).toBeInTheDocument()
  })

  it('renders animated SVG with aria label', () => {
    render(<AgentThinkingIndicator />)
    const svg = screen.getByLabelText('AI agent is thinking')
    expect(svg).toBeInTheDocument()
    expect(svg.tagName).toBe('svg')
  })

  it('renders three animated dots', () => {
    const { container } = render(<AgentThinkingIndicator />)
    // Find dots by their animation style
    const dots = container.querySelectorAll('span[style*="agentThinkingDot"]')
    expect(dots.length).toBe(3)
  })

  it('renders without message — no visible text content', () => {
    render(<AgentThinkingIndicator />)
    const indicator = screen.getByTestId('agent-thinking-indicator')
    expect(indicator).toBeInTheDocument()
    // Should not contain a message span (only the style tag and dots)
    expect(screen.queryByText('DMA agent is analyzing your brief')).not.toBeInTheDocument()
  })

  it('accepts custom data-testid', () => {
    render(<AgentThinkingIndicator data-testid="custom-thinking" />)
    expect(screen.getByTestId('custom-thinking')).toBeInTheDocument()
  })

  it('contains neural network animation elements', () => {
    const { container } = render(<AgentThinkingIndicator />)
    const svg = container.querySelector('svg')
    expect(svg).not.toBeNull()
    // Should have circles (core, rings, endpoint nodes)
    const circles = svg!.querySelectorAll('circle')
    expect(circles.length).toBeGreaterThan(5)
    // Should have connection lines
    const lines = svg!.querySelectorAll('line')
    expect(lines.length).toBe(8) // 8 neural connections
  })

  it('injects keyframe animation stylesheet', () => {
    const { container } = render(<AgentThinkingIndicator />)
    const style = container.querySelector('style')
    expect(style).not.toBeNull()
    expect(style!.textContent).toContain('agentThinkingDot')
  })
})
