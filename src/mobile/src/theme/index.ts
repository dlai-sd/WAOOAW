/**
 * Theme System Exports
 * Central export point for all theme-related modules
 */

// Core theme
export { default as theme } from './theme';
export type { Theme } from './theme';

// Colors
export { colors, ColorUtils } from './colors';
export type { ColorKey, ColorValue } from './colors';

// Typography
export {
  fontFamily,
  fontSize,
  lineHeight,
  fontWeight,
  letterSpacing,
  textVariants,
} from './typography';
export type {
  FontFamilyKey,
  FontSizeKey,
  LineHeightKey,
  FontWeightKey,
  TextVariantKey,
} from './typography';

// Spacing
export { spacing, screenPadding, componentSpacing, layout } from './spacing';
export type { SpacingKey, SpacingValue } from './spacing';

// Radius
export { radius, componentRadius } from './radius';
export type { RadiusKey, RadiusValue } from './radius';

// Provider and hook
export { ThemeProvider, useTheme, ThemeContext } from './ThemeProvider';
