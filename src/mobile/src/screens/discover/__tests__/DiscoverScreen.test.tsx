import React from 'react';
import TestRenderer from 'react-test-renderer';

jest.mock('@shopify/flash-list', () => {
  const ReactLib = require('react');

  return {
    FlashList: (props: any) => ReactLib.createElement('FlashList', props),
  };
});

jest.mock('../../../hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe',
      card: '#18181b',
    },
    spacing: {
      sm: 8,
      md: 16,
      xl: 32,
      screenPadding: { horizontal: 16, vertical: 12 },
    },
    typography: {
      fontFamily: {
        display: 'Space Grotesk',
        body: 'Inter',
        bodyBold: 'Inter Bold',
      },
    },
  }),
}));

jest.mock('../../../hooks/useAgents', () => ({
  useAgents: jest.fn(),
}));

jest.mock('../../../components/AgentCard', () => ({
  AgentCard: () => null,
}));

jest.mock('../../../components/LoadingSpinner', () => ({
  LoadingSpinner: () => null,
}));

jest.mock('../../../components/ErrorView', () => ({
  ErrorView: () => null,
}));

jest.mock('../../../components/EmptyState', () => ({
  EmptyState: () => null,
}));

jest.mock('../../../components/voice/VoiceControl', () => ({
  VoiceControl: () => null,
}));

jest.mock('../../../components/voice/VoiceHelpModal', () => ({
  VoiceHelpModal: () => null,
}));

jest.mock('../../../hooks/usePerformanceMonitoring', () => ({
  usePerformanceMonitoring: jest.fn(),
}));

import { DiscoverScreen } from '../DiscoverScreen';

const { useAgents } = jest.requireMock('../../../hooks/useAgents') as {
  useAgents: jest.Mock;
};

describe('DiscoverScreen', () => {
  it('provides a RefreshControl on the agent list', () => {
    useAgents.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isFetching: false,
    });

    const tree = TestRenderer.create(
      <DiscoverScreen
        navigation={{ navigate: jest.fn() } as any}
        route={{ key: 'discover', name: 'Discover', params: {} } as any}
      />
    );

    const flashList = tree.root.findByType('FlashList');
    expect(flashList.props.refreshControl).toBeTruthy();
  });
});
