/**
 * Theme System Tests
 * Validates design tokens and theme utilities
 */

import { colors, ColorUtils } from '../src/theme/colors';
import { fontFamily, fontSize, textVariants } from '../src/theme/typography';
import { spacing, layout } from '../src/theme/spacing';
import { radius } from '../src/theme/radius';
import theme from '../src/theme/theme';

describe('Theme System', () => {
  describe('Colors', () => {
    it('should have all required brand colors', () => {
      expect(colors.black).toBe('#0a0a0a');
      expect(colors.neonCyan).toBe('#00f2fe');
      expect(colors.neonPurple).toBe('#667eea');
      expect(colors.brandPrimary).toBe('#0078d4');
    });

    it('should have all status colors', () => {
      expect(colors.statusOnline).toBe('#10b981');
      expect(colors.statusWorking).toBe('#f59e0b');
      expect(colors.statusOffline).toBe('#ef4444');
    });

    it('should have semantic colors', () => {
      expect(colors.success).toBe('#10b981');
      expect(colors.warning).toBe('#f59e0b');
      expect(colors.error).toBe('#ef4444');
      expect(colors.info).toBe('#00f2fe');
    });

    it('should return correct status color', () => {
      expect(ColorUtils.getStatusColor('online')).toBe(colors.statusOnline);
      expect(ColorUtils.getStatusColor('working')).toBe(colors.statusWorking);
      expect(ColorUtils.getStatusColor('offline')).toBe(colors.statusOffline);
    });

    it('should add opacity to colors', () => {
      const result = ColorUtils.withOpacity('#00f2fe', 0.5);
      expect(result).toBe('#00f2fe80');
    });
  });

  describe('Typography', () => {
    it('should have all font families', () => {
      expect(fontFamily.display).toBe('SpaceGrotesk_700Bold');
      expect(fontFamily.heading).toBe('Outfit_600SemiBold');
      expect(fontFamily.body).toBe('Inter_400Regular');
    });

    it('should have all font sizes', () => {
      expect(fontSize.xs).toBe(12);
      expect(fontSize.sm).toBe(14);
      expect(fontSize.md).toBe(16);
      expect(fontSize.lg).toBe(18);
      expect(fontSize.hero).toBe(40);
    });

    it('should have text variants', () => {
      expect(textVariants.hero).toMatchObject({
        fontFamily: fontFamily.display,
        fontSize: fontSize.hero,
      });
      expect(textVariants.body).toMatchObject({
        fontFamily: fontFamily.body,
        fontSize: fontSize.md,
      });
    });
  });

  describe('Spacing', () => {
    it('should have spacing scale', () => {
      expect(spacing.xxs).toBe(4);
      expect(spacing.xs).toBe(8);
      expect(spacing.md).toBe(16);
      expect(spacing.xl).toBe(24);
    });

    it('should have layout values', () => {
      expect(layout.iconSizeMedium).toBe(24);
      expect(layout.avatarSizeMedium).toBe(48);
      expect(layout.buttonHeightMedium).toBe(44);
    });
  });

  describe('Border Radius', () => {
    it('should have radius values', () => {
      expect(radius.none).toBe(0);
      expect(radius.sm).toBe(8);
      expect(radius.md).toBe(12);
      expect(radius.xl).toBe(20);
      expect(radius.full).toBe(9999);
    });
  });

  describe('Complete Theme', () => {
    it('should export complete theme object', () => {
      expect(theme.colors).toBeDefined();
      expect(theme.fontFamily).toBeDefined();
      expect(theme.spacing).toBeDefined();
      expect(theme.radius).toBeDefined();
    });

    it('should have shadows', () => {
      expect(theme.shadows.none).toBeDefined();
      expect(theme.shadows.small).toBeDefined();
      expect(theme.shadows.glow).toBeDefined();
    });

    it('should have animation config', () => {
      expect(theme.animation.duration.fast).toBe(150);
      expect(theme.animation.duration.normal).toBe(250);
    });

    it('should have z-index layers', () => {
      expect(theme.zIndex.base).toBe(0);
      expect(theme.zIndex.modal).toBe(100);
      expect(theme.zIndex.toast).toBe(300);
    });
  });
});
