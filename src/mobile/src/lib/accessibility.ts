/**
 * Accessibility Utilities
 * Helper functions and hooks for improving app accessibility
 * 
 * Features:
 * - Screen reader announcements
 * - Focus management
 * - Contrast checking
 * - Touch target validation
 */

import { AccessibilityInfo, findNodeHandle, Platform } from 'react-native';

/**
 * Make an accessibility announcement
 */
export function announceForAccessibility(message: string): void {
  AccessibilityInfo.announceForAccessibility(message);
}

/**
 * Check if screen reader is enabled
 */
export async function isScreenReaderEnabled(): Promise<boolean> {
  return await AccessibilityInfo.isScreenReaderEnabled();
}

/**
 * Check if reduce motion is enabled
 */
export async function isReduceMotionEnabled(): Promise<boolean> {
  if (Platform.OS === 'ios') {
    return await AccessibilityInfo.isReduceMotionEnabled();
  }
  return false;
}

/**
 * Check if bold text is enabled
 */
export async function isBoldTextEnabled(): Promise<boolean> {
  if (Platform.OS === 'ios') {
    return await AccessibilityInfo.isBoldTextEnabled();
  }
  return false;
}

/**
 * Check if grayscale is enabled
 */
export async function isGrayscaleEnabled(): Promise<boolean> {
  if (Platform.OS === 'ios') {
    return await AccessibilityInfo.isGrayscaleEnabled();
  }
  return false;
}

/**
 * Set accessibility focus to an element
 */
export function setAccessibilityFocus(ref: React.RefObject<any>): void {
  if (ref.current) {
    const reactTag = findNodeHandle(ref.current);
    if (reactTag) {
      AccessibilityInfo.setAccessibilityFocus(reactTag);
    }
  }
}

/**
 * Check color contrast ratio
 * Returns true if contrast meets WCAG AA standards (4.5:1 for normal text)
 */
export function hasGoodContrast(
  foreground: string,
  background: string,
  largeText: boolean = false
): boolean {
  const ratio = getContrastRatio(foreground, background);
  const minRatio = largeText ? 3 : 4.5; // WCAG AA standards
  return ratio >= minRatio;
}

/**
 * Calculate contrast ratio between two colors
 */
export function getContrastRatio(foreground: string, background: string): number {
  const l1 = getRelativeLuminance(foreground);
  const l2 = getRelativeLuminance(background);

  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Get relative luminance of a color
 */
function getRelativeLuminance(color: string): number {
  const rgb = hexToRgb(color);
  if (!rgb) return 0;

  const [r, g, b] = rgb.map((val) => {
    const normalized = val / 255;
    return normalized <= 0.03928
      ? normalized / 12.92
      : Math.pow((normalized + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Convert hex color to RGB
 */
function hexToRgb(hex: string): [number, number, number] | null {
  // Remove # if present
  hex = hex.replace(/^#/, '');

  // Handle shorthand hex (#fff -> #ffffff)
  if (hex.length === 3) {
    hex = hex
      .split('')
      .map((char) => char + char)
      .join('');
  }

  if (hex.length !== 6) {
    return null;
  }

  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  return [r, g, b];
}

/**
 * Validate touch target size
 * Returns true if meets accessibility guidelines (minimum 44x44 points)
 */
export function isValidTouchTarget(width: number, height: number): boolean {
  const MIN_TOUCH_TARGET = 44;
  return width >= MIN_TOUCH_TARGET && height >= MIN_TOUCH_TARGET;
}

/**
 * Get accessibility label for rating
 */
export function getRatingAccessibilityLabel(rating: number, maxRating: number = 5): string {
  return `${rating} out of ${maxRating} stars`;
}

/**
 * Get accessibility label for price
 */
export function getPriceAccessibilityLabel(price: number, currency: string = 'INR'): string {
  return `${price} ${currency} per month`;
}

/**
 * Get accessibility label for status
 */
export function getStatusAccessibilityLabel(status: string): string {
  switch (status.toLowerCase()) {
    case 'active':
      return 'Active trial, available now';
    case 'expired':
      return 'Trial expired';
    case 'converted':
      return 'Converted to paid subscription';
    case 'canceled':
      return 'Trial canceled';
    default:
      return status;
  }
}

/**
 * Get accessibility hint for action
 */
export function getActionAccessibilityHint(action: string): string {
  switch (action.toLowerCase()) {
    case 'hire':
      return 'Double tap to start 7-day trial';
    case 'cancel':
      return 'Double tap to cancel trial';
    case 'refresh':
      return 'Double tap to refresh data';
    case 'search':
      return 'Double tap to search';
    case 'filter':
      return 'Double tap to apply filters';
    default:
      return `Double tap to ${action}`;
  }
}

/**
 * Accessibility constants
 */
export const A11Y_CONSTANTS = {
  MIN_TOUCH_TARGET: 44,
  MIN_CONTRAST_RATIO: 4.5,
  MIN_CONTRAST_RATIO_LARGE_TEXT: 3,
  WCAG_AA: 4.5,
  WCAG_AAA: 7,
} as const;

/**
 * Accessibility traits/roles
 */
export const A11Y_ROLES = {
  BUTTON: 'button',
  LINK: 'link',
  SEARCH: 'search',
  IMAGE: 'image',
  KEY_OPTION: 'keyboardkey',
  TEXT: 'text',
  ADJUSTABLE: 'adjustable',
  IMAGE_BUTTON: 'imagebutton',
  HEADER: 'header',
  SUMMARY: 'summary',
  NONE: 'none',
} as const;
