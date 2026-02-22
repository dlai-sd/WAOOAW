/**
 * E2E Test: App Launch and Basic Navigation
 * 
 * This test would have caught the white screen crash issue.
 * 
 * Run: npm run test:e2e
 */

describe('WAOOAW App Launch', () => {
  beforeAll(async () => {
    await device.launchApp({
      newInstance: true,
      launchArgs: {
        detoxPrintBusyIdleResources: 'YES',
      },
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  /**
   * CRITICAL TEST #1: App launches without crashing
   * 
   * Would catch:
   * - Missing fonts
   * - Missing assets
   * - JS bundle errors
   * - Native module crashes
   */
  it('should launch successfully and show welcome screen', async () => {
    // Wait for app to load (fonts, assets, initialization)
    await waitFor(element(by.text('WAOOAW')))
      .toBeVisible()
      .withTimeout(10000);
    
    // Should NOT see error boundary
    await expect(element(by.text('Something went wrong'))).not.toBeVisible();
    
    // Should see welcome content
    await expect(element(by.text('Welcome Back'))).toBeVisible();
    await expect(element(by.text('Agents Earn Your Business'))).toBeVisible();
  });

  /**
   * CRITICAL TEST #2: Skip sign-in works
   */
  it('should allow skipping sign-in in dev mode', async () => {
    // Wait for skip button (only visible in __DEV__)
    await waitFor(element(by.text('Skip Sign In (Demo Mode)')))
      .toBeVisible()
      .withTimeout(5000);
    
    await element(by.text('Skip Sign In (Demo Mode)')).tap();
    
    // Should navigate to main app
    await waitFor(element(by.id('home-screen')))
      .toBeVisible()
      .withTimeout(5000);
  });

  /**
   * CRITICAL TEST #3: Agent discovery loads
   */
  it('should load agent discovery screen', async () => {
    // Skip sign-in
    await element(by.text('Skip Sign In (Demo Mode)')).tap();
    
    // Navigate to discover tab
    await element(by.id('discover-tab')).tap();
    
    // Should load agents from API
    await waitFor(element(by.id('agent-card')))
      .toBeVisible()
      .withTimeout(10000);
    
    // Should connect to correct backend
    // (Would fail if API URL wrong)
  });

  /**
   * CRITICAL TEST #4: Network connectivity
   */
  it('should handle offline gracefully', async () => {
    // Skip sign-in
    await element(by.text('Skip Sign In (Demo Mode)')).tap();
    
    // Simulate offline
    await device.setURLBlacklist(['*']);
    
    // Should show offline banner
    await expect(element(by.text('No Internet Connection'))).toBeVisible();
    
    // Re-enable network
    await device.setURLBlacklist([]);
  });

  /**
   * CRITICAL TEST #5: Fonts load correctly
   */
  it('should render custom fonts without crashing', async () => {
    // App should be visible (fonts loaded)
    await expect(element(by.text('WAOOAW'))).toBeVisible();
    
    // Take screenshot to verify font rendering
    await device.takeScreenshot('fonts-loaded');
  });
});

/**
 * Helper function to add testID to components
 * 
 * Usage in code:
 * <View testID="home-screen">...</View>
 * <TouchableOpacity testID="discover-tab">...</TouchableOpacity>
 */
