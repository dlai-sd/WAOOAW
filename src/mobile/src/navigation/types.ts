/**
 * Navigation Type Definitions
 * 
 * Type-safe navigation for React Navigation v6+
 */

import type { NavigatorScreenParams } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';

// ============================================================================
// Root Navigation
// ============================================================================

export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
};

export type RootStackScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;

// ============================================================================
// Auth Flow
// ============================================================================

export type AuthStackParamList = {
  SignIn: undefined;
  SignUp: undefined;
  OTPVerification: {
    registrationId: string;
    otpId: string;
    channel?: 'email' | 'sms';
    destinationMasked: string;
  };
};

export type AuthStackScreenProps<T extends keyof AuthStackParamList> =
  NativeStackScreenProps<AuthStackParamList, T>;

// ============================================================================
// Main App (Bottom Tabs)
// ============================================================================

export type MainTabParamList = {
  HomeTab: NavigatorScreenParams<HomeStackParamList>;
  DiscoverTab: NavigatorScreenParams<DiscoverStackParamList>;
  MyAgentsTab: NavigatorScreenParams<MyAgentsStackParamList>;
  ProfileTab: NavigatorScreenParams<ProfileStackParamList>;
};

export type MainTabScreenProps<T extends keyof MainTabParamList> =
  BottomTabScreenProps<MainTabParamList, T>;

// ============================================================================
// Home Stack
// ============================================================================

export type HomeStackParamList = {
  Home: undefined;
  AgentDetail: { agentId: string };
  TrialDashboard: { trialId: string };
};

export type HomeStackScreenProps<T extends keyof HomeStackParamList> =
  NativeStackScreenProps<HomeStackParamList, T>;

// ============================================================================
// Discover Stack
// ============================================================================

export type DiscoverStackParamList = {
  Discover: undefined;
  AgentDetail: { agentId: string };
  HireWizard: { agentId: string; step?: number };
  SearchResults: { query: string };
  FilterAgents: {
    industry?: string;
    minRating?: number;
    maxPrice?: number;
  };
};

export type DiscoverStackScreenProps<T extends keyof DiscoverStackParamList> =
  NativeStackScreenProps<DiscoverStackParamList, T>;

// ============================================================================
// My Agents Stack
// ============================================================================

export type MyAgentsStackParamList = {
  MyAgents: undefined;
  AgentDetail: { agentId: string };
  TrialDashboard: { trialId: string };
  ActiveTrialsList: undefined;
  HiredAgentsList: undefined;
};

export type MyAgentsStackScreenProps<T extends keyof MyAgentsStackParamList> =
  NativeStackScreenProps<MyAgentsStackParamList, T>;

// ============================================================================
// Profile Stack
// ============================================================================

export type ProfileStackParamList = {
  Profile: undefined;
  EditProfile: undefined;
  Settings: undefined;
  Notifications: undefined;
  PaymentMethods: undefined;
  SubscriptionManagement: undefined;
  HelpCenter: undefined;
  PrivacyPolicy: undefined;
  TermsOfService: undefined;
};

export type ProfileStackScreenProps<T extends keyof ProfileStackParamList> =
  NativeStackScreenProps<ProfileStackParamList, T>;

// ============================================================================
// Navigation Props Helpers
// ============================================================================

/**
 * Helper to get navigation prop for any screen
 * Usage: const navigation = useNavigation<NavigationProp<'SignIn'>>();
 */
export type NavigationProp<
  RouteName extends keyof AuthStackParamList |
    keyof HomeStackParamList |
    keyof DiscoverStackParamList |
    keyof MyAgentsStackParamList |
    keyof ProfileStackParamList
> =
  RouteName extends keyof AuthStackParamList
    ? AuthStackScreenProps<RouteName>['navigation']
    : RouteName extends keyof HomeStackParamList
    ? HomeStackScreenProps<RouteName>['navigation']
    : RouteName extends keyof DiscoverStackParamList
    ? DiscoverStackScreenProps<RouteName>['navigation']
    : RouteName extends keyof MyAgentsStackParamList
    ? MyAgentsStackScreenProps<RouteName>['navigation']
    : RouteName extends keyof ProfileStackParamList
    ? ProfileStackScreenProps<RouteName>['navigation']
    : never;

/**
 * Helper to get route prop for any screen
 */
export type RouteProp<
  RouteName extends keyof AuthStackParamList |
    keyof HomeStackParamList |
    keyof DiscoverStackParamList |
    keyof MyAgentsStackParamList |
    keyof ProfileStackParamList
> =
  RouteName extends keyof AuthStackParamList
    ? AuthStackScreenProps<RouteName>['route']
    : RouteName extends keyof HomeStackParamList
    ? HomeStackScreenProps<RouteName>['route']
    : RouteName extends keyof DiscoverStackParamList
    ? DiscoverStackScreenProps<RouteName>['route']
    : RouteName extends keyof MyAgentsStackParamList
    ? MyAgentsStackScreenProps<RouteName>['route']
    : RouteName extends keyof ProfileStackParamList
    ? ProfileStackScreenProps<RouteName>['route']
    : never;

// ============================================================================
// Deep Linking Config
// ============================================================================

export const linking = {
  prefixes: ['waooaw://', 'https://waooaw.com'],
  config: {
    screens: {
      Auth: {
        screens: {
          SignIn: 'sign-in',
          SignUp: 'sign-up',
          OTPVerification: 'verify-otp',
        },
      },
      Main: {
        screens: {
          HomeTab: {
            screens: {
              Home: 'home',
              AgentDetail: 'home/agent/:agentId',
              TrialDashboard: 'home/trial/:trialId',
            },
          },
          DiscoverTab: {
            screens: {
              Discover: 'discover',
              AgentDetail: 'discover/agent/:agentId',
              HireWizard: 'hire/:agentId',
              SearchResults: 'search',
              FilterAgents: 'filter',
            },
          },
          MyAgentsTab: {
            screens: {
              MyAgents: 'my-agents',
              AgentDetail: 'my-agents/agent/:agentId',
              TrialDashboard: 'my-agents/trial/:trialId',
              ActiveTrialsList: 'trials/active',
              HiredAgentsList: 'agents/hired',
            },
          },
          ProfileTab: {
            screens: {
              Profile: 'profile',
              EditProfile: 'profile/edit',
              Settings: 'settings',
              Notifications: 'notifications',
              PaymentMethods: 'payment-methods',
              SubscriptionManagement: 'subscriptions',
              HelpCenter: 'help',
              PrivacyPolicy: 'privacy',
              TermsOfService: 'terms',
            },
          },
        },
      },
    },
  },
};

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
