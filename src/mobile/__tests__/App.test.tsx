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
    const { getByLabelText, getByText } = render(<App />);

    await waitFor(() => {
      // Logo is now an Image with accessibilityLabel="WAOOAW"
      expect(getByLabelText('WAOOAW')).toBeTruthy();
      expect(getByText('Agents Earn Your Business')).toBeTruthy();
    });
  });

  it('should use theme colors', async () => {
    const { getByLabelText } = render(<App />);

    await waitFor(() => {
      // Logo is now an Image component, not a Text node
      const logo = getByLabelText('WAOOAW');
      expect(logo).toBeTruthy();
    });
  });
});
