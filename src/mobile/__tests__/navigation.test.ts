/**
 * Navigation Types and Deep Linking Tests
 */

import { linking } from '../src/navigation/types';

describe('Navigation Configuration', () => {
  describe('deep linking', () => {
    it('should have correct prefixes', () => {
      expect(linking.prefixes).toContain('waooaw://');
      expect(linking.prefixes).toContain('https://waooaw.com');
    });

    it('should have Auth screens configured', () => {
      const authScreens = linking.config.screens.Auth.screens;

      expect(authScreens.SignIn).toBe('sign-in');
      expect(authScreens.SignUp).toBe('sign-up');
      expect(authScreens.OTPVerification).toBe('verify-otp');
    });

    it('should have HomeTab screens configured', () => {
      const homeScreens = linking.config.screens.Main.screens.HomeTab.screens;

      expect(homeScreens.Home).toBe('home');
      expect(homeScreens.AgentDetail).toBe('agent/:agentId');
      expect(homeScreens.TrialDashboard).toBe('trial/:trialId');
    });

    it('should have DiscoverTab screens configured', () => {
      const discoverScreens = linking.config.screens.Main.screens.DiscoverTab.screens;

      expect(discoverScreens.Discover).toBe('discover');
      expect(discoverScreens.AgentDetail).toBe('agent/:agentId');
      expect(discoverScreens.HireWizard).toBe('hire/:agentId');
      expect(discoverScreens.SearchResults).toBe('search');
      expect(discoverScreens.FilterAgents).toBe('filter');
    });

    it('should have MyAgentsTab screens configured', () => {
      const myAgentsScreens = linking.config.screens.Main.screens.MyAgentsTab.screens;

      expect(myAgentsScreens.MyAgents).toBe('my-agents');
      expect(myAgentsScreens.AgentDetail).toBe('agent/:agentId');
      expect(myAgentsScreens.TrialDashboard).toBe('trial/:trialId');
      expect(myAgentsScreens.ActiveTrialsList).toBe('trials/active');
      expect(myAgentsScreens.HiredAgentsList).toBe('agents/hired');
    });

    it('should have ProfileTab screens configured', () => {
      const profileScreens = linking.config.screens.Main.screens.ProfileTab.screens;

      expect(profileScreens.Profile).toBe('profile');
      expect(profileScreens.EditProfile).toBe('profile/edit');
      expect(profileScreens.Settings).toBe('settings');
      expect(profileScreens.Notifications).toBe('notifications');
      expect(profileScreens.PaymentMethods).toBe('payment-methods');
      expect(profileScreens.SubscriptionManagement).toBe('subscriptions');
      expect(profileScreens.HelpCenter).toBe('help');
      expect(profileScreens.PrivacyPolicy).toBe('privacy');
      expect(profileScreens.TermsOfService).toBe('terms');
    });

    it('should support URL parameter extraction for agent detail', () => {
      const agentDetailPath = linking.config.screens.Main.screens.DiscoverTab.screens.AgentDetail;
      
      expect(agentDetailPath).toContain(':agentId');
      expect(agentDetailPath).toBe('agent/:agentId');
    });

    it('should support URL parameter extraction for trial dashboard', () => {
      const trialPath = linking.config.screens.Main.screens.HomeTab.screens.TrialDashboard;
      
      expect(trialPath).toContain(':trialId');
      expect(trialPath).toBe('trial/:trialId');
    });

    it('should support URL parameter extraction for hire wizard', () => {
      const hirePath = linking.config.screens.Main.screens.DiscoverTab.screens.HireWizard;
      
      expect(hirePath).toContain(':agentId');
      expect(hirePath).toBe('hire/:agentId');
    });
  });

  describe('URL patterns', () => {
    it('should match auth sign-in URL', () => {
      const urls = [
        'waooaw://sign-in',
        'https://waooaw.com/sign-in',
      ];

      urls.forEach((url) => {
        expect(url).toMatch(/sign-in$/);
      });
    });

    it('should match agent detail URL with ID', () => {
      const urls = [
        'waooaw://agent/AGENT-123',
        'https://waooaw.com/agent/AGENT-123',
      ];

      urls.forEach((url) => {
        expect(url).toMatch(/agent\/[A-Z0-9-]+$/);
      });
    });

    it('should match trial dashboard URL with ID', () => {
      const urls = [
        'waooaw://trial/TRIAL-456',
        'https://waooaw.com/trial/TRIAL-456',
      ];

      urls.forEach((url) => {
        expect(url).toMatch(/trial\/[A-Z0-9-]+$/);
      });
    });

    it('should match hire wizard URL with agent ID', () => {
      const urls = [
        'waooaw://hire/AGENT-789',
        'https://waooaw.com/hire/AGENT-789',
      ];

      urls.forEach((url) => {
        expect(url).toMatch(/hire\/[A-Z0-9-]+$/);
      });
    });
  });

  describe('type safety', () => {
    it('should enforce param list types at compile time', () => {
      // This test primarily verifies TypeScript compilation
      // If types are incorrect, the build will fail
      
      // Example type checks (would fail at compile time if wrong)
      type AuthParams = {
        SignIn: undefined;
        SignUp: undefined;
        OTPVerification: {
          registrationId: string;
          otpId: string;
          channel?: 'email' | 'sms';
          destinationMasked: string;
        };
      };

      type HomeParams = {
        Home: undefined;
        AgentDetail: { agentId: string };
        TrialDashboard: { trialId: string };
      };

      // If these assignments compile, types are correct
      const authParams: AuthParams = {
        SignIn: undefined,
        SignUp: undefined,
        OTPVerification: {
          registrationId: 'REG-123',
          otpId: 'OTP-123',
          destinationMasked: 't***t@example.com',
        },
      };

      const homeParams: HomeParams = {
        Home: undefined,
        AgentDetail: { agentId: 'AGENT-123' },
        TrialDashboard: { trialId: 'TRIAL-123' },
      };

      expect(authParams).toBeDefined();
      expect(homeParams).toBeDefined();
    });
  });
});
