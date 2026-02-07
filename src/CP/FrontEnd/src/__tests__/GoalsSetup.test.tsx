import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import GoalsSetup from '../pages/authenticated/GoalsSetup';

describe('GoalsSetup', () => {
  it('renders without crashing', () => {
    const { container } = render(<GoalsSetup />);
    expect(container).toBeTruthy();
  });

  it('renders component content', () => {
    const { container } = render(<GoalsSetup />);
    expect(container.firstChild).toBeTruthy();
  });

  it('renders exchange setup section', () => {
    const { getByText } = render(<GoalsSetup />)
    expect(getByText('Connect Exchange (Trading Setup)')).toBeTruthy()
  })
});
