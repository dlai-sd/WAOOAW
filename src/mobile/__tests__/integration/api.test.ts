import { getAPIConfig } from '../../src/config/api.config';

describe('API Configuration Integration', () => {
  it('should expose separate Plant and CP base URLs', () => {
    const config = getAPIConfig();

    expect(config.apiBaseUrl).toBeTruthy();
    expect(config.cpApiBaseUrl).toBeTruthy();
    expect(config.apiBaseUrl).not.toBe(config.cpApiBaseUrl);
  });

  it('should keep CP routes on the CP host in demo-like environments', () => {
    const config = getAPIConfig();

    if (config.cpApiBaseUrl.includes('waooaw.com')) {
      expect(config.cpApiBaseUrl).toContain('cp.');
    }
  });

  it('should keep Plant routes on the Plant host in demo-like environments', () => {
    const config = getAPIConfig();

    if (config.apiBaseUrl.includes('waooaw.com')) {
      expect(config.apiBaseUrl).toContain('plant.');
    }
  });

  it('should keep timeout configured for mobile clients', () => {
    const config = getAPIConfig();
    expect(config.timeout).toBeGreaterThan(0);
  });
});
