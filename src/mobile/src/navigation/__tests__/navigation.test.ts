/**
 * Navigation Tests
 * 
 * Validates navigation configuration for duplicate routes
 */

import { linking } from '../types';

describe('Navigation Configuration', () => {
  it('should not have duplicate URL patterns', () => {
    const patterns: string[] = [];
    const config = linking.config.screens;

    // Extract all patterns from Main tabs
    if (config.Main && typeof config.Main === 'object' && 'screens' in config.Main) {
      const mainScreens = config.Main.screens as Record<string, any>;
      
      Object.keys(mainScreens).forEach(tabName => {
        const tab = mainScreens[tabName];
        if (tab && typeof tab === 'object' && 'screens' in tab) {
          const tabScreens = tab.screens as Record<string, string>;
          Object.values(tabScreens).forEach(pattern => {
            if (typeof pattern === 'string') {
              patterns.push(pattern);
            }
          });
        }
      });
    }

    // Check for duplicates
    const duplicates = patterns.filter((pattern, index) => 
      patterns.indexOf(pattern) !== index
    );

    expect(duplicates).toEqual([]);
    
    if (duplicates.length > 0) {
      console.error('Duplicate patterns found:', duplicates);
    }
  });

  it('should have unique patterns for AgentDetail across tabs', () => {
    const config = linking.config.screens;
    
    if (config.Main && typeof config.Main === 'object' && 'screens' in config.Main) {
      const mainScreens = config.Main.screens as Record<string, any>;
      
      const homeAgent = mainScreens.HomeTab?.screens?.AgentDetail;
      const discoverAgent = mainScreens.DiscoverTab?.screens?.AgentDetail;
      const myAgentsAgent = mainScreens.MyAgentsTab?.screens?.AgentDetail;

      // All should be different
      expect(homeAgent).not.toEqual(discoverAgent);
      expect(homeAgent).not.toEqual(myAgentsAgent);
      expect(discoverAgent).not.toEqual(myAgentsAgent);

      // Should contain tab-specific prefixes
      expect(homeAgent).toContain('home/');
      expect(discoverAgent).toContain('discover/');
      expect(myAgentsAgent).toContain('my-agents/');
    }
  });

  it('should have unique patterns for TrialDashboard across tabs', () => {
    const config = linking.config.screens;
    
    if (config.Main && typeof config.Main === 'object' && 'screens' in config.Main) {
      const mainScreens = config.Main.screens as Record<string, any>;
      
      const homeTrial = mainScreens.HomeTab?.screens?.TrialDashboard;
      const myAgentsTrial = mainScreens.MyAgentsTab?.screens?.TrialDashboard;

      // Should be different
      expect(homeTrial).not.toEqual(myAgentsTrial);

      // Should contain tab-specific prefixes
      expect(homeTrial).toContain('home/');
      expect(myAgentsTrial).toContain('my-agents/');
    }
  });
});
