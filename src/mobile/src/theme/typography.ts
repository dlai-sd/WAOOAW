/**
 * WAOOAW Typography System
 * Font families, sizes, weights, line heights
 */

/**
 * Font Families
 * Using Google Fonts via expo-google-fonts
 */
export const fontFamily = {
  display: 'SpaceGrotesk_700Bold',     // Display text (hero, large titles)
  heading: 'Outfit_600SemiBold',       // Headings
  body: 'Inter_400Regular',            // Body text
  bodyBold: 'Inter_600SemiBold',       // Bold body text
  code: 'Courier',                     // System monospace for code/IDs
} as const;

/**
 * Font Sizes (in pixels)
 */
export const fontSize = {
  xs: 12,       // Captions, minor labels
  sm: 14,       // Small text, badges
  md: 16,       // Default body text
  lg: 18,       // Emphasized text, large body
  xl: 20,       // Small headings
  xxl: 24,      // Medium headings
  display: 32,  // Large headings
  hero: 40,     // Hero sections
} as const;

/**
 * Line Heights (multipliers)
 */
export const lineHeight = {
  tight: 1.2,    // Headings, buttons
  normal: 1.5,   // Body text
  relaxed: 1.75, // Long-form content
} as const;

/**
 * Font Weights
 */
export const fontWeight = {
  regular: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
} as const;

/**
 * Letter Spacing (in pixels)
 */
export const letterSpacing = {
  tight: -0.5,
  normal: 0,
  wide: 0.5,
  wider: 1,
} as const;

/**
 * Typography presets for common text styles
 */
export const textVariants = {
  hero: {
    fontFamily: fontFamily.display,
    fontSize: fontSize.hero,
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.bold,
    letterSpacing: letterSpacing.tight,
  },
  displayLarge: {
    fontFamily: fontFamily.display,
    fontSize: fontSize.display,
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.bold,
    letterSpacing: letterSpacing.tight,
  },
  h1: {
    fontFamily: fontFamily.heading,
    fontSize: fontSize.xxl,
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.semibold,
  },
  h2: {
    fontFamily: fontFamily.heading,
    fontSize: fontSize.xl,
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.semibold,
  },
  h3: {
    fontFamily: fontFamily.heading,
    fontSize: fontSize.lg,
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.semibold,
  },
  bodyLarge: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.lg,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.regular,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.md,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.regular,
  },
  bodySmall: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.sm,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.regular,
  },
  bodyBold: {
    fontFamily: fontFamily.bodyBold,
    fontSize: fontSize.md,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.semibold,
  },
  caption: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.xs,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.regular,
  },
  button: {
    fontFamily: fontFamily.bodyBold,
    fontSize: fontSize.md,
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.semibold,
    letterSpacing: letterSpacing.wide,
  },
  label: {
    fontFamily: fontFamily.bodyBold,
    fontSize: fontSize.sm,
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.medium,
  },
} as const;

export type FontFamilyKey = keyof typeof fontFamily;
export type FontSizeKey = keyof typeof fontSize;
export type LineHeightKey = keyof typeof lineHeight;
export type FontWeightKey = keyof typeof fontWeight;
export type TextVariantKey = keyof typeof textVariants;
