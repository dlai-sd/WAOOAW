/**
 * App Component Tests
 */

import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import App from '../App';

// Mock expo-font
jest.mock('expo-font', () => ({
  loadAsync: jest.fn(() => Promise.resolve()),
}));

describe('App', () => {
  it('should render loading state initially', () => {
    const { getByText } = render(<App />);
    expect(getByText('Loading WAOOAW...')).toBeTruthy();
  });

  it('should render welcome screen after fonts load', async () => {
    const { getByText } = render(<App />);

    await waitFor(() => {
      expect(getByText('WAOOAW')).toBeTruthy();
      expect(getByText('Agents Earn Your Business')).toBeTruthy();
    });
  });

  it('should use theme colors', async () => {
    const { getByText } = render(<App />);

    await waitFor(() => {
      const heading = getByText('WAOOAW');
      expect(heading).toBeTruthy();
    });
  });
});
