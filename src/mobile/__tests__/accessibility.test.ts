/**
 * Accessibility Utilities Tests
 */

import { hasGoodContrast, getContrastRatio, announceForAccessibility } from '../src/lib/accessibility';
import { AccessibilityInfo } from 'react-native';

// Mock AccessibilityInfo
jest.mock('react-native', () => ({
  AccessibilityInfo: {
    announceForAccessibility: jest.fn(),
  },
}));

describe('Accessibility Utilities', () => {
  describe('getContrastRatio', () => {
    it('should calculate contrast ratio between white and black', () => {
      const ratio = getContrastRatio('#ffffff', '#000000');
      expect(ratio).toBeCloseTo(21, 0); // White/black has 21:1 ratio
    });

    it('should calculate contrast ratio between same colors', () => {
      const ratio = getContrastRatio('#ffffff', '#ffffff');
      expect(ratio).toBe(1); // Same color has 1:1 ratio
    });

    it('should handle hex colors without #', () => {
      const ratio = getContrastRatio('ffffff', '000000');
      expect(ratio).toBeCloseTo(21, 0);
    });

    it('should handle 3-digit hex colors', () => {
      const ratio = getContrastRatio('#fff', '#000');
      expect(ratio).toBeCloseTo(21, 0);
    });

    it('should handle lowercase hex colors', () => {
      const ratio = getContrastRatio('#ffffff', '#000000');
      const ratioLower = getContrastRatio('#FFFFFF', '#000000');
      expect(ratio).toBe(ratioLower);
    });
  });

  describe('hasGoodContrast', () => {
    describe('WCAG AA standard', () => {
      it('should pass for white text on black background', () => {
        expect(hasGoodContrast('#ffffff', '#000000', 'AA')).toBe(true);
      });

      it('should pass for black text on white background', () => {
        expect(hasGoodContrast('#000000', '#ffffff', 'AA')).toBe(true);
      });

      it('should fail for light gray on white', () => {
        expect(hasGoodContrast('#cccccc', '#ffffff', 'AA')).toBe(false);
      });

      it('should pass for neon cyan on black (WAOOAW design)', () => {
        expect(hasGoodContrast('#00f2fe', '#0a0a0a', 'AA')).toBe(true);
      });

      it('should handle large text (3:1 ratio required)', () => {
        // A contrast that passes for large text but fails for normal
        const foreground = '#777777';
        const background = '#ffffff';
        
        expect(hasGoodContrast(foreground, background, 'AA', true)).toBe(true);
        expect(hasGoodContrast(foreground, background, 'AA', false)).toBe(false);
      });
    });

    describe('WCAG AAA standard', () => {
      it('should pass for white text on black background', () => {
        expect(hasGoodContrast('#ffffff', '#000000', 'AAA')).toBe(true);
      });

      it('should fail for medium contrast ratios', () => {
        expect(hasGoodContrast('#666666', '#ffffff', 'AAA')).toBe(false);
      });

      it('should have stricter requirements than AA', () => {
        const foreground = '#595959'; // ~7:1 with white
        const background = '#ffffff';
        
        expect(hasGoodContrast(foreground, background, 'AA')).toBe(true);
        expect(hasGoodContrast(foreground, background, 'AAA')).toBe(true);
      });
    });
  });

  describe('announceForAccessibility', () => {
    it('should call AccessibilityInfo.announceForAccessibility', () => {
      const message = 'Screen loaded successfully';
      announceForAccessibility(message);
      
      expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith(message);
    });

    it('should handle empty messages', () => {
      announceForAccessibility('');
      
      expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith('');
    });

    it('should handle long messages', () => {
      const longMessage = 'A'.repeat(500);
      announceForAccessibility(longMessage);
      
      expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith(longMessage);
    });
  });
});
