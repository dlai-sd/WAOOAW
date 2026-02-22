/**
 * WAOOAW Border Radius System
 * Consistent border radius values for rounded corners
 */

/**
 * Border radius values (in pixels)
 */
export const radius = {
  none: 0,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  full: 9999, // Fully rounded (pill shape)
} as const;

/**
 * Component-specific border radius
 */
export const componentRadius = {
  // Buttons
  button: radius.lg,
  buttonSmall: radius.md,
  
  // Cards
  card: radius.xl,
  cardSmall: radius.md,
  
  // Inputs
  input: radius.md,
  
  // Chips/Badges
  chip: radius.full,
  badge: radius.sm,
  
  // Modals/Sheets
  modal: radius.xxl,
  bottomSheet: radius.xl,
  
  // Agent cards
  agentCard: radius.xl,
  agentAvatar: radius.full,
  
  // Images
  imageSmall: radius.sm,
  imageMedium: radius.md,
  imageLarge: radius.lg,
} as const;

export type RadiusKey = keyof typeof radius;
export type RadiusValue = typeof radius[RadiusKey];
