/**
 * OTPInput Component Tests
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { OTPInput } from '../src/components/OTPInput';

// Mock useTheme hook
jest.mock('../src/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      neonCyan: '#00f2fe',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      black: '#0a0a0a',
      error: '#ef4444',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
    },
  }),
}));

describe('OTPInput', () => {
  const mockOnComplete = jest.fn();
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render with default 6 inputs', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    expect(inputs).toHaveLength(6);
  });

  it('should render with custom length', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} length={4} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    expect(inputs).toHaveLength(4);
  });

  it('should call onChange when digit is entered', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} onChange={mockOnChange} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    fireEvent.changeText(inputs[0], '1');

    expect(mockOnChange).toHaveBeenCalledWith('1');
  });

  it('should call onComplete when all digits are entered', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} onChange={mockOnChange} length={4} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    
    fireEvent.changeText(inputs[0], '1');
    fireEvent.changeText(inputs[1], '2');
    fireEvent.changeText(inputs[2], '3');
    fireEvent.changeText(inputs[3], '4');

    expect(mockOnComplete).toHaveBeenCalledWith('1234');
  });

  it('should handle paste with full OTP', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} onChange={mockOnChange} length={6} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    fireEvent.changeText(inputs[0], '123456');

    expect(mockOnChange).toHaveBeenLastCalledWith('123456');
    expect(mockOnComplete).toHaveBeenCalledWith('123456');
  });

  it('should only accept numeric input', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} onChange={mockOnChange} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    
    fireEvent.changeText(inputs[0], 'a');
    expect(mockOnChange).toHaveBeenLastCalledWith('');
    
    fireEvent.changeText(inputs[0], '5');
    expect(mockOnChange).toHaveBeenLastCalledWith('5');
  });

  it('should handle backspace by clearing current input', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} onChange={mockOnChange} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    
    fireEvent.changeText(inputs[0], '1');
    expect(mockOnChange).toHaveBeenLastCalledWith('1');
    
    fireEvent.changeText(inputs[0], '');
    expect(mockOnChange).toHaveBeenLastCalledWith('');
  });

  it('should be disabled when disabled prop is true', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} disabled={true} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    
    inputs.forEach((input) => {
      expect(input.props.editable).toBe(false);
      expect(input.props.accessibilityState.disabled).toBe(true);
    });
  });

  it('should show error state when error prop is true', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} error={true} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    
    inputs.forEach((input) => {
      // Error styling is applied via borderColor, which we can check in style
      expect(input.props.style.borderColor).toBe('#ef4444'); // error color
    });
  });

  it('should have correct accessibility labels', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} length={4} />
    );

    expect(getAllByLabelText('OTP digit 1')).toBeTruthy();
    expect(getAllByLabelText('OTP digit 2')).toBeTruthy();
    expect(getAllByLabelText('OTP digit 3')).toBeTruthy();
    expect(getAllByLabelText('OTP digit 4')).toBeTruthy();
  });

  it('should apply custom styles', () => {
    const customContainerStyle = { marginTop: 20 };
    const customCellStyle = { width: 60 };
    const customTextStyle = { fontSize: 28 };

    const { getAllByLabelText } = render(
      <OTPInput
        onComplete={mockOnComplete}
        style={customContainerStyle}
        cellStyle={customCellStyle}
        textStyle={customTextStyle}
      />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    
    // Check if custom styles are applied
    expect(inputs[0].props.style.width).toBe(60);
    expect(inputs[0].props.style.fontSize).toBe(28);
  });

  it('should handle partial paste', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} onChange={mockOnChange} length={6} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    
    // Paste 3 digits starting from index 2
    fireEvent.changeText(inputs[2], '789');

    expect(mockOnChange).toHaveBeenLastCalledWith('00789');
    expect(mockOnComplete).not.toHaveBeenCalled(); // Not complete yet
  });

  it('should trim non-numeric characters from paste', () => {
    const { getAllByLabelText } = render(
      <OTPInput onComplete={mockOnComplete} onChange={mockOnChange} length={6} />
    );

    const inputs = getAllByLabelText(/OTP digit/);
    
    fireEvent.changeText(inputs[0], '12-34-56');

    expect(mockOnChange).toHaveBeenLastCalledWith('123456');
    expect(mockOnComplete).toHaveBeenCalledWith('123456');
  });
});
