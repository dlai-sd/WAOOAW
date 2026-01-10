import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import UsageBilling from '../pages/authenticated/UsageBilling';

describe('UsageBilling', () => {
  it('renders without crashing', () => {
    const { container } = render(<UsageBilling />);
    expect(container).toBeTruthy();
  });

  it('renders component content', () => {
    const { container } = render(<UsageBilling />);
    expect(container.firstChild).toBeTruthy();
  });
});
