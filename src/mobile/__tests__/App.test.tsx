import React from 'react';
import { render } from '@testing-library/react-native';
import App from '../App';

describe('App', () => {
  it('renders without crashing', () => {
    const { getByText } = render(<App />);
    // Basic smoke test - just verify app renders
    expect(getByText(/open up app\.tsx/i)).toBeTruthy();
  });

  it('renders the correct text content', () => {
    const { getByText } = render(<App />);
    expect(getByText(/to start working on your app/i)).toBeTruthy();
  });
});
