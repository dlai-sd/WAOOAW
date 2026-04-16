import React from 'react';
import TestRenderer from 'react-test-renderer';

const tabScreens: any[] = [];

jest.mock('@expo/vector-icons', () => {
  const ReactLib = require('react');

  return {
    Ionicons: (props: any) => ReactLib.createElement('Ionicons', props),
  };
});

jest.mock('@react-navigation/bottom-tabs', () => {
  const ReactLib = require('react');

  return {
    createBottomTabNavigator: () => ({
      Navigator: ({ children }: any) =>
        ReactLib.createElement(ReactLib.Fragment, null, children),
      Screen: (props: any) => {
        tabScreens.push(props);
        return ReactLib.createElement('TabScreen', props);
      },
    }),
  };
});

jest.mock('../../hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      textSecondary: '#71717a',
      neonCyan: '#00f2fe',
    },
  }),
}));

jest.mock('../../hooks/useHiredAgents', () => ({
  useAgentsNeedingSetup: jest.fn(),
}));

jest.mock('../../hooks/useAllDeliverables', () => ({
  useAllDeliverables: jest.fn(() => ({ deliverables: [], isLoading: false, error: null })),
}));

jest.mock('../../screens/home/HomeScreen', () => ({ HomeScreen: () => null }));
jest.mock('../../screens/discover/DiscoverScreen', () => ({ DiscoverScreen: () => null }));
jest.mock('../../screens/discover/AgentDetailScreen', () => ({ AgentDetailScreen: () => null }));
jest.mock('../../screens/discover/SearchResultsScreen', () => ({ __esModule: true, default: () => null }));
jest.mock('../../screens/discover/FilterAgentsScreen', () => ({ __esModule: true, default: () => null }));
jest.mock('../../screens/hire/HireWizardScreen', () => ({ HireWizardScreen: () => null }));
jest.mock('../../screens/agents', () => ({
  MyAgentsScreen: () => null,
  TrialDashboardScreen: () => null,
  ActiveTrialsListScreen: () => null,
  HiredAgentsListScreen: () => null,
  AgentOperationsScreen: () => null,
}));
jest.mock('../../screens/profile/ProfileScreen', () => ({ ProfileScreen: () => null }));
jest.mock('../../screens/profile/EditProfileScreen', () => ({ EditProfileScreen: () => null }));
jest.mock('../../screens/profile', () => ({
  SettingsScreen: () => null,
  NotificationsScreen: () => null,
  HelpCenterScreen: () => null,
  PrivacyPolicyScreen: () => null,
  TermsOfServiceScreen: () => null,
  PaymentMethodsScreen: () => null,
  SubscriptionManagementScreen: () => null,
}));

import { MainNavigator } from '../MainNavigator';

const { useAgentsNeedingSetup } = jest.requireMock('../../hooks/useHiredAgents') as {
  useAgentsNeedingSetup: jest.Mock;
};

describe('MainNavigator', () => {
  beforeEach(() => {
    tabScreens.length = 0;
    jest.clearAllMocks();
  });

  it('replaces emoji tab icons with Ionicons', () => {
    useAgentsNeedingSetup.mockReturnValue({ data: [] });

    TestRenderer.act(() => {
      TestRenderer.create(<MainNavigator />);
    });

    const iconConfig = [
      ['HomeTab', 'home'],
      ['DiscoverTab', 'search'],
      ['MyAgentsTab', 'grid'],
      ['ProfileTab', 'person'],
    ] as const;

    const renderedIcons = iconConfig.map(([name, iconName]) => {
      const screen = tabScreens.find((tab) => tab.name === name);
      expect(screen).toBeDefined();
      const icon = screen.options.tabBarIcon({ color: '#00f2fe', size: 24 });

      expect(icon.type).toBeDefined();
      expect(icon.props.name).toBe(iconName);
      expect(icon.props.color).toBe('#00f2fe');
      expect(icon.props.size).toBe(24);

      return icon;
    });

    expect(JSON.stringify(renderedIcons)).not.toContain('🏠');
    expect(JSON.stringify(renderedIcons)).not.toContain('🔍');
    expect(JSON.stringify(renderedIcons)).not.toContain('🤖');
    expect(JSON.stringify(renderedIcons)).not.toContain('👤');
  });

  it('shows a badge when agents need setup and hides it when none do', () => {
    useAgentsNeedingSetup.mockReturnValue({ data: [{ id: '1' }, { id: '2' }] });

    TestRenderer.act(() => {
      TestRenderer.create(<MainNavigator />);
    });

    let myAgentsTab = tabScreens.find((tab) => tab.name === 'MyAgentsTab');
    expect(myAgentsTab).toBeDefined();
    expect(myAgentsTab.options.tabBarBadge).toBe(2);
    expect(myAgentsTab.options.tabBarBadgeStyle).toEqual(
      expect.objectContaining({ backgroundColor: '#ef4444' })
    );

    tabScreens.length = 0;
    useAgentsNeedingSetup.mockReturnValue({ data: [] });

    TestRenderer.act(() => {
      TestRenderer.create(<MainNavigator />);
    });

    myAgentsTab = tabScreens.find((tab) => tab.name === 'MyAgentsTab');
    expect(myAgentsTab).toBeDefined();
    expect(myAgentsTab.options.tabBarBadge).toBeUndefined();
  });
});
