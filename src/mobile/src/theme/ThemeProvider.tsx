/**
 * Theme Context Provider
 * Makes theme accessible throughout the app
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { theme, Theme } from './theme';

/**
 * Theme context
 */
const ThemeContext = createContext<Theme | undefined>(undefined);

/**
 * Theme provider props
 */
interface ThemeProviderProps {
  children: ReactNode;
  customTheme?: Partial<Theme>;
}

/**
 * Theme Provider Component
 * 
 * Wraps the app and provides theme to all children
 * 
 * @example
 * ```tsx
 * <ThemeProvider>
 *   <App />
 * </ThemeProvider>
 * ```
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  customTheme,
}) => {
  // Merge custom theme with default theme
  const mergedTheme = customTheme
    ? { ...theme, ...customTheme }
    : theme;

  return (
    <ThemeContext.Provider value={mergedTheme}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * Hook to access theme in components
 * 
 * @example
 * ```tsx
 * const MyComponent = () => {
 *   const theme = useTheme();
 *   
 *   return (
 *     <View style={{ backgroundColor: theme.colors.background }}>
 *       <Text style={{ color: theme.colors.textPrimary }}>
 *         Hello WAOOAW
 *       </Text>
 *     </View>
 *   );
 * };
 * ```
 * 
 * @throws Error if used outside ThemeProvider
 */
export const useTheme = (): Theme => {
  const context = useContext(ThemeContext);
  
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  
  return context;
};

/**
 * Export theme context for testing
 */
export { ThemeContext };
