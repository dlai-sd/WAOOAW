import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import Performance from '../pages/authenticated/Performance';

describe('Performance', () => {
  it('renders without crashing', () => {
    const { container } = render(<Performance />);
    expect(container).toBeTruthy();
  });

  it('renders component content', () => {
    const { container } = render(<Performance />);
    expect(container.firstChild).toBeTruthy();
  });
});
