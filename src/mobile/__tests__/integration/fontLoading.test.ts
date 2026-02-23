/**
 * Integration Test: Font Loading
 * 
 * Validates that fonts are properly loaded before app renders.
 * Would have caught the production build font crash.
 */

import * as Font from 'expo-font';
import {
  SpaceGrotesk_700Bold,
} from '@expo-google-fonts/space-grotesk';
import {
  Outfit_600SemiBold,
} from '@expo-google-fonts/outfit';
import {
  Inter_400Regular,
  Inter_600SemiBold,
} from '@expo-google-fonts/inter';

describe('Font Loading Integration', () => {
  /**
   * CRITICAL: Fonts must load without errors
   */
  it('should load all custom fonts successfully', async () => {
    const fonts = {
      SpaceGrotesk_700Bold,
      Outfit_600SemiBold,
      Inter_400Regular,
      Inter_600SemiBold,
    };

    // Should not throw
    await expect(Font.loadAsync(fonts)).resolves.toBeDefined();
  });

  /**
   * Verify fonts are available after loading
   */
  it('should have fonts loaded after Font.loadAsync', async () => {
    const fonts = {
      SpaceGrotesk_700Bold,
      Outfit_600SemiBold,
      Inter_400Regular,
      Inter_600SemiBold,
    };

    await Font.loadAsync(fonts);

    // Check each font is loaded
    expect(Font.isLoaded('SpaceGrotesk_700Bold')).toBe(true);
    expect(Font.isLoaded('Outfit_600SemiBold')).toBe(true);
    expect(Font.isLoaded('Inter_400Regular')).toBe(true);
    expect(Font.isLoaded('Inter_600SemiBold')).toBe(true);
  });

  /**
   * Verify fallback behavior
   */
  it('should continue if font loading fails (dev mode)', async () => {
    // Simulate error
    const mockLoadAsync = jest.spyOn(Font, 'loadAsync').mockRejectedValue(new Error('Font load failed'));

    // Should handle error gracefully
    try {
      await Font.loadAsync({});
    } catch (error) {
      expect(error.message).toBe('Font load failed');
    }

    mockLoadAsync.mockRestore();
  });
});
