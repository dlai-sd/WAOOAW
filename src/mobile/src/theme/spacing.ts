/**
 * WAOOAW Spacing System
 * Consistent spacing scale for margins, padding, gaps
 */

/**
 * Base spacing unit: 4px
 * All spacing values are multiples of 4
 */
const BASE_UNIT = 4;

/**
 * Spacing scale
 */
export const spacing = {
  xxs: BASE_UNIT * 1,      // 4px
  xs: BASE_UNIT * 2,       // 8px
  sm: BASE_UNIT * 3,       // 12px
  md: BASE_UNIT * 4,       // 16px
  lg: BASE_UNIT * 5,       // 20px
  xl: BASE_UNIT * 6,       // 24px
  xxl: BASE_UNIT * 8,      // 32px
  xxxl: BASE_UNIT * 10,    // 40px
  huge: BASE_UNIT * 12,    // 48px
  massive: BASE_UNIT * 16, // 64px
} as const;

/**
 * Screen padding (horizontal edges)
 */
export const screenPadding = {
  horizontal: spacing.md,  // 16px
  vertical: spacing.lg,    // 20px
} as const;

/**
 * Component-specific spacing
 */
export const componentSpacing = {
  // Cards
  cardPadding: spacing.md,
  cardGap: spacing.md,
  
  // Lists
  listItemGap: spacing.sm,
  listItemPadding: spacing.md,
  
  // Forms
  inputPadding: spacing.md,
  inputGap: spacing.sm,
  formFieldGap: spacing.lg,
  
  // Buttons
  buttonPaddingHorizontal: spacing.lg,
  buttonPaddingVertical: spacing.sm,
  buttonGap: spacing.xs,
  
  // Navigation
  tabBarHeight: BASE_UNIT * 16, // 64px
  headerHeight: BASE_UNIT * 14, // 56px
  
  // Agent cards
  agentCardPadding: spacing.md,
  agentCardGap: spacing.sm,
  
  // Bottom sheets
  bottomSheetPadding: spacing.xl,
} as const;

/**
 * Common layout values
 */
export const layout = {
  // Container widths
  maxContentWidth: 600,
  
  // Icon sizes
  iconSizeSmall: 16,
  iconSizeMedium: 24,
  iconSizeLarge: 32,
  iconSizeHero: 48,
  
  // Avatar sizes
  avatarSizeSmall: 32,
  avatarSizeMedium: 48,
  avatarSizeLarge: 64,
  avatarSizeHero: 96,
  
  // Button heights
  buttonHeightSmall: 36,
  buttonHeightMedium: 44,
  buttonHeightLarge: 52,
  
  // Input heights
  inputHeight: 44,
  
  // Card dimensions
  agentCardMinHeight: 180,
  agentCardImageHeight: 120,
} as const;

export type SpacingKey = keyof typeof spacing;
export type SpacingValue = typeof spacing[SpacingKey];
