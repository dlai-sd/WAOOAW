/**
 * WAOOAW Theme System
 * Combined theme object with all design tokens
 */

import { colors, ColorUtils } from './colors';
import {
  fontFamily,
  fontSize,
  lineHeight,
  fontWeight,
  letterSpacing,
  textVariants,
} from './typography';
import { spacing, screenPadding, componentSpacing, layout } from './spacing';
import { radius, componentRadius } from './radius';

/**
 * Complete theme object
 */
export const theme = {
  // Color system
  colors,
  colorUtils: ColorUtils,

  // Typography
  fontFamily,
  fontSize,
  lineHeight,
  fontWeight,
  letterSpacing,
  textVariants,

  // Spacing
  spacing,
  screenPadding,
  componentSpacing,
  layout,

  // Border radius
  radius,
  componentRadius,

  // Shadows
  shadows: {
    none: {
      shadowColor: 'transparent',
      shadowOffset: { width: 0, height: 0 },
      shadowOpacity: 0,
      shadowRadius: 0,
      elevation: 0,
    },
    small: {
      shadowColor: colors.neonCyan,
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 2,
    },
    medium: {
      shadowColor: colors.neonCyan,
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 4,
    },
    large: {
      shadowColor: colors.neonCyan,
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.2,
      shadowRadius: 16,
      elevation: 8,
    },
    glow: {
      // Neon glow effect for focus/hover states
      shadowColor: colors.neonCyan,
      shadowOffset: { width: 0, height: 0 },
      shadowOpacity: 0.3,
      shadowRadius: 20,
      elevation: 10,
    },
  },

  // Animations
  animation: {
    duration: {
      fast: 150,
      normal: 250,
      slow: 350,
    },
    easing: {
      easeIn: 'ease-in',
      easeOut: 'ease-out',
      easeInOut: 'ease-in-out',
    },
  },

  // Z-index layers
  zIndex: {
    base: 0,
    elevated: 10,
    modal: 100,
    overlay: 200,
    toast: 300,
  },
} as const;

/**
 * Theme type
 */
export type Theme = typeof theme;

/**
 * Default export
 */
export default theme;
