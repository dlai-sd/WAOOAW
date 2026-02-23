/**
 * WAOOAW Color Palette
 * Dark-first design with neon accents
 * Ported from CP FrontEnd theme
 */

export const colors = {
  // Brand Colors
  black: '#0a0a0a',              // Primary background
  grayDark: '#18181b',           // Secondary background (card background)
  neonCyan: '#00f2fe',           // Primary accent
  neonPurple: '#667eea',         // Secondary accent
  neonPink: '#f093fb',           // Tertiary accent
  brandPrimary: '#0078d4',       // Primary brand color

  // Status Colors
  statusOnline: '#10b981',       // Green - Agent available
  statusWorking: '#f59e0b',      // Yellow - Agent working
  statusOffline: '#ef4444',      // Red - Agent offline

  // Neutral Grays
  gray100: '#f5f9ff',
  gray200: '#e6f2ff',
  gray300: '#c2e0ff',
  gray400: '#9dceff',
  gray500: '#78bcff',
  gray600: '#4da6ff',
  gray700: '#004080',
  gray800: '#003366',
  gray900: '#001933',

  // Semantic Colors
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#00f2fe',

  // UI Colors
  textPrimary: '#ffffff',         // Primary text on dark backgrounds
  textSecondary: '#a1a1aa',       // Secondary text, less emphasis
  textMuted: '#71717a',           // Muted text, hints
  textInverse: '#0a0a0a',         // Text on light backgrounds
  
  border: '#27272a',              // Default border
  borderLight: '#3f3f46',         // Lighter border variant
  borderFocus: '#00f2fe',         // Focus state border (neon cyan)
  
  card: '#18181b',                // Card background
  cardHover: '#27272a',           // Card hover state
  
  // Background variants
  background: '#0a0a0a',          // Primary background
  backgroundSecondary: '#18181b', // Secondary background
  backgroundTertiary: '#27272a',  // Tertiary background
  
  // Overlay & Shadow
  overlay: 'rgba(0, 0, 0, 0.7)',
  shadowLight: 'rgba(0, 242, 254, 0.1)',
  shadowMedium: 'rgba(0, 242, 254, 0.2)',
  shadowHeavy: 'rgba(0, 242, 254, 0.3)',
  
  // Transparent variants for gradients
  transparent: 'transparent',
  white: '#ffffff',
  blackOpacity50: 'rgba(10, 10, 10, 0.5)',
} as const;

export type ColorKey = keyof typeof colors;
export type ColorValue = typeof colors[ColorKey];

/**
 * Color utility functions
 */
export const ColorUtils = {
  /**
   * Get status color based on agent status
   */
  getStatusColor: (status: 'online' | 'working' | 'offline'): ColorValue => {
    switch (status) {
      case 'online':
        return colors.statusOnline;
      case 'working':
        return colors.statusWorking;
      case 'offline':
        return colors.statusOffline;
      default:
        return colors.textSecondary;
    }
  },

  /**
   * Get semantic color based on type
   */
  getSemanticColor: (type: 'success' | 'warning' | 'error' | 'info'): ColorValue => {
    switch (type) {
      case 'success':
        return colors.success;
      case 'warning':
        return colors.warning;
      case 'error':
        return colors.error;
      case 'info':
        return colors.info;
      default:
        return colors.textPrimary;
    }
  },

  /**
   * Add opacity to hex color
   */
  withOpacity: (color: string, opacity: number): string => {
    // Convert opacity (0-1) to hex (00-FF)
    const alpha = Math.round(opacity * 255).toString(16).padStart(2, '0');
    return `${color}${alpha}`;
  },
};
