/**
 * ThemeProvider Tests
 * Validates theme context and hooks
 */

import React from 'react';
import { Text } from 'react-native';
import { render } from '@testing-library/react-native';
import { ThemeProvider, useTheme } from '../src/theme/ThemeProvider';

const TestComponent: React.FC = () => {
  const theme = useTheme();
  return <Text testID="test-text">{theme.colors.neonCyan}</Text>;
};

describe('ThemeProvider', () => {
  it('should provide theme to children', () => {
    const { getByTestId } = render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    const text = getByTestId('test-text');
    expect(text.props.children).toBe('#00f2fe');
  });

  it('should throw error when useTheme is used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useTheme must be used within a ThemeProvider');

    consoleSpy.mockRestore();
  });

  it('should merge custom theme', () => {
    const customTheme = {
      colors: {
        black: '#000000',
      },
    };

    const CustomTestComponent: React.FC = () => {
      const theme = useTheme();
      return <Text testID="custom-black">{theme.colors.black}</Text>;
    };

    const { getByTestId } = render(
      <ThemeProvider customTheme={customTheme}>
        <CustomTestComponent />
      </ThemeProvider>
    );

    const text = getByTestId('custom-black');
    expect(text.props.children).toBe('#000000');
  });
});
