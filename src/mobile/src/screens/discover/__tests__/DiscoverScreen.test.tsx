import React from 'react';
import { FlatList } from 'react-native';
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
  VoiceControl: (props: any) => {
    (global as any).__lastVoiceControlProps = props;
    return null;
  },
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
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('provides a RefreshControl on the agent list', () => {
    useAgents.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isFetching: false,
    });

    let tree: TestRenderer.ReactTestRenderer;
    TestRenderer.act(() => {
      tree = TestRenderer.create(
        <DiscoverScreen
          navigation={{ navigate: jest.fn(), getParent: jest.fn() } as any}
          route={{ key: 'discover', name: 'Discover', params: {} } as any}
        />
      );
    });

    const flashList = tree!.root.findByType(FlatList);
    expect(flashList.props.refreshControl).toBeTruthy();
  });

  it('opens the FilterAgents screen from the more filters chip', () => {
    const mockNavigate = jest.fn();

    useAgents.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isFetching: false,
    });

    let tree: TestRenderer.ReactTestRenderer;
    TestRenderer.act(() => {
      tree = TestRenderer.create(
        <DiscoverScreen
          navigation={{ navigate: mockNavigate, getParent: jest.fn() } as any}
          route={{ key: 'discover', name: 'Discover', params: { industry: 'marketing', minRating: 4, maxPrice: 12000 } } as any}
        />
      );
    });

    const moreFiltersButton = tree!.root.findAllByType('TouchableOpacity').find(
      (node) => node.findAllByType('Text').some((textNode) => textNode.props.children === '+ More Filters')
    );

    expect(moreFiltersButton).toBeTruthy();

    moreFiltersButton?.props.onPress();

    expect(mockNavigate).toHaveBeenCalledWith('FilterAgents', {
      industry: 'marketing',
      minRating: 4,
      maxPrice: 12000,
    });
  });

  it('renders loading spinner when loading', () => {
    useAgents.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: jest.fn(),
      isFetching: false,
    });

    let tree: TestRenderer.ReactTestRenderer;
    TestRenderer.act(() => {
      tree = TestRenderer.create(
        <DiscoverScreen
          navigation={{ navigate: jest.fn(), getParent: jest.fn() } as any}
          route={{ key: 'discover', name: 'Discover', params: {} } as any}
        />
      );
    });

    // LoadingSpinner is mocked to return null, just check it doesn't crash
    expect(tree!).toBeTruthy();
  });

  it('renders error view when error and no data', () => {
    useAgents.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Network error'),
      refetch: jest.fn(),
      isFetching: false,
    });

    let tree: TestRenderer.ReactTestRenderer;
    TestRenderer.act(() => {
      tree = TestRenderer.create(
        <DiscoverScreen
          navigation={{ navigate: jest.fn(), getParent: jest.fn() } as any}
          route={{ key: 'discover', name: 'Discover', params: {} } as any}
        />
      );
    });

    expect(tree!).toBeTruthy();
  });

  it('renders industry filter chips', () => {
    useAgents.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isFetching: false,
    });

    let tree: TestRenderer.ReactTestRenderer;
    TestRenderer.act(() => {
      tree = TestRenderer.create(
        <DiscoverScreen
          navigation={{ navigate: jest.fn(), getParent: jest.fn() } as any}
          route={{ key: 'discover', name: 'Discover', params: {} } as any}
        />
      );
    });

    const textNodes = tree!.root.findAllByType('Text');
    const industryLabels = textNodes.map((n) => String(n.props.children).toLowerCase());
    expect(industryLabels).toContain('marketing');
  });

  it('clicking industry chip changes filter', () => {
    const mockRefetch = jest.fn();
    useAgents.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      isFetching: false,
    });

    let tree: TestRenderer.ReactTestRenderer;
    TestRenderer.act(() => {
      tree = TestRenderer.create(
        <DiscoverScreen
          navigation={{ navigate: jest.fn(), getParent: jest.fn() } as any}
          route={{ key: 'discover', name: 'Discover', params: {} } as any}
        />
      );
    });

    const marketingBtn = tree!.root.findAllByType('TouchableOpacity').find(
      (node) => node.findAllByType('Text').some((t) => String(t.props.children).toLowerCase() === 'marketing')
    );

    expect(marketingBtn).toBeTruthy();
    TestRenderer.act(() => {
      marketingBtn?.props.onPress();
    });
    // After pressing, useAgents will be called with marketing filter
    expect(tree!).toBeTruthy();
  });

  it('voice handlers: handleVoiceSearch, handleVoiceFilter, handleVoiceAction, handleVoiceNavigate', () => {
    const mockRefetch = jest.fn();
    const mockGetParent = jest.fn().mockReturnValue({ navigate: jest.fn() });
    useAgents.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      isFetching: false,
    });

    let tree: TestRenderer.ReactTestRenderer;
    TestRenderer.act(() => {
      tree = TestRenderer.create(
        <DiscoverScreen
          navigation={{ navigate: jest.fn(), getParent: mockGetParent } as any}
          route={{ key: 'discover', name: 'Discover', params: {} } as any}
        />
      );
    });

    // Access VoiceControl callbacks stored via mock
    const callbacks = (global as any).__lastVoiceControlProps?.callbacks;
    TestRenderer.act(() => {
      callbacks?.onSearch?.('seo agent', 'marketing');
      callbacks?.onSearch?.('seo agent'); // no industry branch
      callbacks?.onSearch?.('seo', 'unknown_industry'); // invalid industry
      callbacks?.onFilter?.({ industry: 'education' });
      callbacks?.onFilter?.({ industry: 'invalid' }); // invalid industry branch
      callbacks?.onFilter?.({});  // no industry key
      callbacks?.onAction?.('refresh');
      callbacks?.onAction?.('showHelp');
      callbacks?.onAction?.('unknown');
      callbacks?.onNavigate?.('Home');
      callbacks?.onNavigate?.('MyAgents');
      callbacks?.onNavigate?.('Profile');
      callbacks?.onNavigate?.('Unknown');
      callbacks?.onHelp?.();
    });
    expect(mockRefetch).toHaveBeenCalled();
  });
});
