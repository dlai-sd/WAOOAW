/**
 * OTP Input Component
 * Reusable 6-digit OTP input with auto-focus and validation
 */

import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  TextInput,
  StyleSheet,
  ViewStyle,
  TextStyle,
  Platform,
} from 'react-native';
import { useTheme } from '../hooks/useTheme';

export interface OTPInputProps {
  /**
   * Number of OTP digits (default: 6)
   */
  length?: number;
  
  /**
   * Callback when OTP is complete
   */
  onComplete: (code: string) => void;
  
  /**
   * Callback on OTP change
   */
  onChange?: (code: string) => void;
  
  /**
   * Whether the input is disabled
   */
  disabled?: boolean;
  
  /**
   * Whether to show error state
   */
  error?: boolean;
  
  /**
   * Auto-focus first input on mount
   */
  autoFocus?: boolean;
  
  /**
   * Custom container style
   */
  style?: ViewStyle;
  
  /**
   * Custom cell style
   */
  cellStyle?: ViewStyle;
  
  /**
   * Custom text style
   */
  textStyle?: TextStyle;
}

export const OTPInput: React.FC<OTPInputProps> = ({
  length = 6,
  onComplete,
  onChange,
  disabled = false,
  error = false,
  autoFocus = true,
  style,
  cellStyle,
  textStyle,
}) => {
  const { colors, spacing } = useTheme();
  const [otp, setOtp] = useState<string[]>(Array(length).fill(''));
  const inputRefs = useRef<(TextInput | null)[]>([]);

  // Initialize refs array
  useEffect(() => {
    inputRefs.current = inputRefs.current.slice(0, length);
  }, [length]);

  // Auto-focus first input
  useEffect(() => {
    if (autoFocus && !disabled) {
      setTimeout(() => {
        inputRefs.current[0]?.focus();
      }, 100);
    }
  }, [autoFocus, disabled]);

  const handleChangeText = (text: string, index: number) => {
    // Only accept digits
    const digit = text.replace(/[^0-9]/g, '');
    
    if (digit.length === 0) {
      // Handle backspace
      const newOtp = [...otp];
      newOtp[index] = '';
      setOtp(newOtp);
      onChange?.(newOtp.join(''));
      
      // Focus previous input
      if (index > 0) {
        inputRefs.current[index - 1]?.focus();
      }
      return;
    }

    // Handle single digit
    if (digit.length === 1) {
      const newOtp = [...otp];
      newOtp[index] = digit;
      setOtp(newOtp);
      onChange?.(newOtp.join(''));

      // Auto-focus next input
      if (index < length - 1) {
        inputRefs.current[index + 1]?.focus();
      } else {
        // Last digit entered, blur input and trigger onComplete
        inputRefs.current[index]?.blur();
      }

      // Check if OTP is complete
      if (newOtp.every((d) => d !== '')) {
        onComplete(newOtp.join(''));
      }
      return;
    }

    // Handle paste (multiple digits)
    if (digit.length > 1) {
      const digits = digit.slice(0, length).split('');
      const newOtp = [...otp];
      digits.forEach((d, i) => {
        if (index + i < length) {
          newOtp[index + i] = d;
        }
      });
      setOtp(newOtp);
      onChange?.(newOtp.join(''));

      // Focus last filled input or blur if complete
      const lastFilledIndex = Math.min(index + digits.length - 1, length - 1);
      if (lastFilledIndex < length - 1) {
        inputRefs.current[lastFilledIndex + 1]?.focus();
      } else {
        inputRefs.current[lastFilledIndex]?.blur();
      }

      // Check if OTP is complete
      if (newOtp.every((d) => d !== '')) {
        onComplete(newOtp.join(''));
      }
      return;
    }
  };

  const handleKeyPress = (e: any, index: number) => {
    // Handle backspace on empty input
    if (e.nativeEvent.key === 'Backspace' && otp[index] === '' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const getCellStyle = (index: number): ViewStyle => {
    const baseStyle: ViewStyle = {
      ...styles.cell,
      borderColor: error
        ? colors.error
        : otp[index]
        ? colors.neonCyan
        : colors.textSecondary + '40', // 40 = 25% opacity
      backgroundColor: disabled ? colors.black + '80' : colors.black,
    };
    return cellStyle ? { ...baseStyle, ...cellStyle } : baseStyle;
  };

  const getTextStyle = (): TextStyle => {
    const baseStyle: TextStyle = {
      ...styles.cellText,
      color: error ? colors.error : colors.textPrimary,
    };
    return textStyle ? { ...baseStyle, ...textStyle } : baseStyle;
  };

  return (
    <View style={[styles.container, style]}>
      {Array.from({ length }).map((_, index) => (
        <TextInput
          key={index}
          ref={(ref) => {
            inputRefs.current[index] = ref;
          }}
          value={otp[index]}
          onChangeText={(text) => handleChangeText(text, index)}
          onKeyPress={(e) => handleKeyPress(e, index)}
          keyboardType="number-pad"
          maxLength={1}
          editable={!disabled}
          selectTextOnFocus
          style={[getCellStyle(index), getTextStyle()]}
          textAlign="center"
          autoCapitalize="none"
          autoCorrect={false}
          autoComplete="off"
          contextMenuHidden
          secureTextEntry={false}
          accessibilityLabel={`OTP digit ${index + 1}`}
          accessibilityRole="text"
          accessibilityState={{
            disabled,
          }}
          // Platform-specific optimizations
          {...(Platform.OS === 'ios' && {
            textContentType: 'oneTimeCode', // iOS autofill
          })}
          {...(Platform.OS === 'android' && {
            importantForAutofill: 'yes', // Android autofill
          })}
        />
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  cell: {
    width: 48,
    height: 56,
    borderWidth: 2,
    borderRadius: 12,
    fontSize: 24,
    fontWeight: '600',
  },
  cellText: {
    fontSize: 24,
    fontWeight: '600',
  },
});
