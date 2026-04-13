import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AgentContentRenderer } from '../components/rendering/AgentContentRenderer'

describe('AgentContentRenderer (Universal Markdown Pipeline)', () => {
  it('renders a GFM markdown table correctly', () => {
    const markdown = [
      '| # | Theme | Description |',
      '|---|-------|-------------|',
      '| 1 | Bridal Looks | Step-by-step tutorials |',
      '| 2 | Skincare | Daily skincare routines |',
    ].join('\n')

    render(<AgentContentRenderer content={markdown} />)

    expect(screen.getByTestId('agent-content-renderer')).toBeInTheDocument()
    expect(screen.getByText('Bridal Looks')).toBeInTheDocument()
    expect(screen.getByText('Skincare')).toBeInTheDocument()
    // Verify table element exists
    const table = screen.getByTestId('agent-content-renderer').querySelector('table')
    expect(table).not.toBeNull()
  })

  it('renders bold text in markdown', () => {
    render(<AgentContentRenderer content="**Master Theme:** Bridal beauty" />)

    expect(screen.getByText('Master Theme:')).toBeInTheDocument()
    expect(screen.getByText('Bridal beauty')).toBeInTheDocument()
  })

  it('renders inline code', () => {
    render(<AgentContentRenderer content="Use `npm install` to install" />)

    expect(screen.getByText('npm install')).toBeInTheDocument()
    const code = screen.getByTestId('agent-content-renderer').querySelector('code')
    expect(code).not.toBeNull()
  })

  it('returns null for empty content', () => {
    const { container } = render(<AgentContentRenderer content="" />)
    expect(container.firstChild).toBeNull()
  })

  it('applies variant styles correctly', () => {
    const { rerender } = render(
      <AgentContentRenderer content="Hello" variant="compact" />
    )
    const el = screen.getByTestId('agent-content-renderer')
    expect(el.style.fontSize).toBe('0.82rem')

    rerender(<AgentContentRenderer content="Hello" variant="full" />)
    const el2 = screen.getByTestId('agent-content-renderer')
    expect(el2.style.fontSize).toBe('0.95rem')
  })

  it('accepts custom data-testid', () => {
    render(<AgentContentRenderer content="test" data-testid="custom-id" />)
    expect(screen.getByTestId('custom-id')).toBeInTheDocument()
  })

  it('renders links with target="_blank" and rel="noopener noreferrer"', () => {
    render(<AgentContentRenderer content="[Click here](https://example.com)" />)

    const link = screen.getByText('Click here')
    expect(link.tagName).toBe('A')
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toBe('noopener noreferrer')
  })

  it('renders blockquotes with brand styling', () => {
    render(<AgentContentRenderer content="> Important note about the campaign" />)

    const blockquote = screen.getByTestId('agent-content-renderer').querySelector('blockquote')
    expect(blockquote).not.toBeNull()
    expect(screen.getByText('Important note about the campaign')).toBeInTheDocument()
  })

  it('renders ordered and unordered lists', () => {
    const markdown = '- Item 1\n- Item 2\n- Item 3'
    render(<AgentContentRenderer content={markdown} />)

    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
    expect(screen.getByText('Item 3')).toBeInTheDocument()
  })

  it('renders a complete content calendar (customer scenario)', () => {
    // Simulate: customer asks "show me a content calendar table for my bridal beauty business"
    // Backend responds with a GFM markdown table
    const contentCalendar = [
      '**Master Theme:** Bridal Beauty Transformations',
      '',
      '| # | Theme | Description | Frequency |',
      '|---|-------|-------------|-----------|',
      '| 1 | Bridal Tutorials | Step-by-step bridal makeup looks | weekly |',
      '| 2 | Skincare Prep | Pre-wedding skincare routines | weekly |',
      '| 3 | Behind the Scenes | Studio and shoot breakdowns | bi-weekly |',
      '| 4 | Client Stories | Real bride testimonials | monthly |',
    ].join('\n')

    render(<AgentContentRenderer content={contentCalendar} />)

    // Verify the full table rendered as a real HTML table, not plain text
    const renderer = screen.getByTestId('agent-content-renderer')
    const table = renderer.querySelector('table')
    expect(table).not.toBeNull()

    // Verify headers
    const headers = renderer.querySelectorAll('th')
    expect(headers.length).toBe(4)
    expect(headers[0].textContent).toBe('#')
    expect(headers[1].textContent).toBe('Theme')

    // Verify row data
    expect(screen.getByText('Bridal Tutorials')).toBeInTheDocument()
    expect(screen.getByText('Skincare Prep')).toBeInTheDocument()
    expect(screen.getByText('Behind the Scenes')).toBeInTheDocument()
    expect(screen.getByText('Client Stories')).toBeInTheDocument()

    // Verify all 4 data rows rendered
    const rows = renderer.querySelectorAll('tbody tr')
    expect(rows.length).toBe(4)
  })
})
