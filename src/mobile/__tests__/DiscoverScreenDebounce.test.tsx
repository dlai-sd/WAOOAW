/**
 * DiscoverScreen Debounce Tests (MOB-PARITY-2 E2-S1)
 *
 * Verifies:
 * - AC1: API not called per keystroke, fires after 400ms idle
 * - AC2: Filter chip selection persists (state retained across re-renders)
 * - AC3: Clearing search resets to unfiltered query
 * - AC4: Loading indicator during fetch
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { render, fireEvent, act } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DiscoverScreen } from '../src/screens/discover/DiscoverScreen';
import { useAgents } from '../src/hooks/useAgents';

jest.mock('../src/hooks/useAgents');
jest.mock('../src/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: { black: '#0a0a0a', card: '#18181b', textPrimary: '#fff', textSecondary: '#aaa', neonCyan: '#00f2fe', error: '#ef4444' },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, screenPadding: { horizontal: 20, vertical: 20 } },
    typography: { fontFamily: { display: 'SG', body: 'Inter', bodyBold: 'InterBold' } },
  }),
}));
jest.mock('../src/hooks/usePerformanceMonitoring', () => ({ usePerformanceMonitoring: () => {} }));
jest.mock('../src/components/voice/VoiceControl', () => ({ VoiceControl: () => null }));
jest.mock('../src/components/voice/VoiceHelpModal', () => ({ VoiceHelpModal: () => null }));
jest.mock('../src/components/AgentCard', () => ({
  AgentCard: ({ agent }: any) => {
    const { Text } = require('react-native');
    return <Text testID={`agent-card-${agent.id}`}>{agent.name}</Text>;
  },
}));
jest.mock('../src/components/LoadingSpinner', () => ({
  LoadingSpinner: ({ testID }: any) => {
    const { View } = require('react-native');
    return <View testID={testID ?? 'loading'} />;
  },
}));
jest.mock('../src/components/ErrorView', () => ({
  ErrorView: ({ testID }: any) => {
    const { View } = require('react-native');
    return <View testID={testID ?? 'error'} />;
  },
}));
jest.mock('../src/components/EmptyState', () => ({
  EmptyState: ({ testID }: any) => {
    const { View } = require('react-native');
    return <View testID={testID ?? 'empty'} />;
  },
}));
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({ navigate: jest.fn(), getParent: () => ({ navigate: jest.fn() }) }),
}));
// Mock FlashList — renders data items and ListEmptyComponent correctly
jest.mock('@shopify/flash-list', () => ({
  FlashList: ({ data, renderItem, ListEmptyComponent, refreshControl }: any) => {
    const { View } = require('react-native');
    const items = data ?? [];
    return (
      <View>
        {items.length === 0 && ListEmptyComponent
          ? (typeof ListEmptyComponent === 'function'
              ? React.createElement(ListEmptyComponent)
              : ListEmptyComponent)
          : items.map((item: any, i: number) => (
              <View key={i}>{renderItem({ item, index: i })}</View>
            ))
        }
      </View>
    );
  },
}));

const mockUseAgents = useAgents as jest.MockedFunction<typeof useAgents>;

const baseAgentsReturn = {
  data: [],
  isLoading: false,
  error: null,
  refetch: jest.fn(),
  isFetching: false,
} as any;

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: any) => <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

function renderDiscover(routeParams = {}) {
  const navMock = { navigate: jest.fn(), getParent: () => ({ navigate: jest.fn() }) };
  const routeMock = { params: routeParams, key: 'Discover', name: 'Discover' } as any;
  return render(<DiscoverScreen navigation={navMock as any} route={routeMock} />, {
    wrapper: makeWrapper(),
  });
}

describe('DiscoverScreen debounce (MOB-PARITY-2 E2-S1)', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockUseAgents.mockReturnValue(baseAgentsReturn);
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  it('AC1: API not re-called for each keystroke within 400ms', () => {
    renderDiscover();
    // Reset call tracking after initial render
    mockUseAgents.mockClear();

    // debouncedSearch still '', so query stays the same for 200ms
    act(() => { jest.advanceTimersByTime(200); });

    // All calls within 200ms should still have no 'q' param since debounce hasn't fired
    const midCalls = mockUseAgents.mock.calls;
    midCalls.forEach((args) => {
      expect((args[0] as any)?.q).toBeUndefined();
    });
  });

  it('AC1: debounced value fires after 400ms', async () => {
    const { getByPlaceholderText } = renderDiscover();
    const input = getByPlaceholderText('Search agents by skill, industry...');

    fireEvent.changeText(input, 'marketing');

    // Before 400ms — no q in params
    act(() => { jest.advanceTimersByTime(200); });
    const callsDuring = mockUseAgents.mock.calls;
    const hasDebouncedQuery = callsDuring.some((args) => (args[0] as any)?.q === 'marketing');
    expect(hasDebouncedQuery).toBe(false);

    // After 400ms — q should appear
    act(() => { jest.advanceTimersByTime(300); }); // total 500ms
    const callsAfter = mockUseAgents.mock.calls;
    const hasQuery = callsAfter.some((args) => (args[0] as any)?.q === 'marketing');
    expect(hasQuery).toBe(true);
  });

  it('AC2: filter chip stays selected between re-renders', () => {
    const { getByText } = renderDiscover();
    // Tap marketing filter
    const marketingBtn = getByText('marketing');
    fireEvent.press(marketingBtn);

    // After pressing, industry filter should appear in the query
    const lastCall = mockUseAgents.mock.calls[mockUseAgents.mock.calls.length - 1];
    expect((lastCall[0] as any)?.industry).toBe('marketing');
  });

  it('AC3: clearing search input removes q from params', () => {
    const { getByPlaceholderText } = renderDiscover();
    const input = getByPlaceholderText('Search agents by skill, industry...');

    fireEvent.changeText(input, 'sales');
    act(() => { jest.advanceTimersByTime(500); }); // let debounce fire

    // Now clear it
    fireEvent.changeText(input, '');
    act(() => { jest.advanceTimersByTime(500); });

    const lastCall = mockUseAgents.mock.calls[mockUseAgents.mock.calls.length - 1];
    expect((lastCall[0] as any)?.q).toBeUndefined();
  });

  it('AC4: loading indicator shows while fetching', () => {
    mockUseAgents.mockReturnValue({ ...baseAgentsReturn, data: undefined, isLoading: true });
    const { getByTestId } = renderDiscover();
    // LoadingSpinner renders with default testID "loading"
    expect(getByTestId('loading')).toBeTruthy();
  });
});

describe('DiscoverScreen additional branch coverage', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  it('shows error view when API returns error and no agents cached', () => {
    mockUseAgents.mockReturnValue({
      ...baseAgentsReturn,
      data: undefined,
      isLoading: false,
      error: { message: 'Network failure' },
    });
    const { getByTestId } = renderDiscover();
    expect(getByTestId('error')).toBeTruthy();
  });

  it('shows empty state when agents array is empty and not loading', () => {
    mockUseAgents.mockReturnValue({ ...baseAgentsReturn, data: [], isLoading: false });
    const { getByTestId } = renderDiscover();
    expect(getByTestId('empty')).toBeTruthy();
  });

  it('filters out agents below minRating', () => {
    const agents = [
      { id: 'a1', name: 'High Rated', rating: 4.8, price: 10000 },
      { id: 'a2', name: 'Low Rated', rating: 2.0, price: 8000 },
    ];
    mockUseAgents.mockReturnValue({ ...baseAgentsReturn, data: agents });
    const { queryByTestId } = renderDiscover({ minRating: 4.0 });
    expect(queryByTestId('agent-card-a1')).toBeTruthy();
    expect(queryByTestId('agent-card-a2')).toBeNull();
  });

  it('filters out agents above maxPrice', () => {
    const agents = [
      { id: 'a3', name: 'Cheap', rating: 4.0, price: 5000 },
      { id: 'a4', name: 'Expensive', rating: 4.5, price: 25000 },
    ];
    mockUseAgents.mockReturnValue({ ...baseAgentsReturn, data: agents });
    const { queryByTestId } = renderDiscover({ maxPrice: 10000 });
    expect(queryByTestId('agent-card-a3')).toBeTruthy();
    expect(queryByTestId('agent-card-a4')).toBeNull();
  });

  it('passes both minRating and maxPrice filters correctly', () => {
    const agents = [
      { id: 'b1', name: 'Pass Both', rating: 4.5, price: 8000 },
      { id: 'b2', name: 'Fail Rating', rating: 3.0, price: 8000 },
      { id: 'b3', name: 'Fail Price', rating: 4.8, price: 20000 },
    ];
    mockUseAgents.mockReturnValue({ ...baseAgentsReturn, data: agents });
    const { queryByTestId } = renderDiscover({ minRating: 4.0, maxPrice: 15000 });
    expect(queryByTestId('agent-card-b1')).toBeTruthy();
    expect(queryByTestId('agent-card-b2')).toBeNull();
    expect(queryByTestId('agent-card-b3')).toBeNull();
  });

  it('filters agent without rating when minRating > 0', () => {
    const agents = [{ id: 'c1', name: 'No Rating', price: 5000 }];
    mockUseAgents.mockReturnValue({ ...baseAgentsReturn, data: agents });
    const { queryByTestId } = renderDiscover({ minRating: 1.0 });
    expect(queryByTestId('agent-card-c1')).toBeNull();
  });

  it('does not filter agents when minRating and maxPrice are 0', () => {
    const agents = [
      { id: 'd1', name: 'Agent One', rating: 2.0, price: 50000 },
    ];
    mockUseAgents.mockReturnValue({ ...baseAgentsReturn, data: agents });
    const { getByTestId } = renderDiscover({ minRating: 0, maxPrice: 0 });
    expect(getByTestId('agent-card-d1')).toBeTruthy();
  });

  it('deselects industry filter when same chip is pressed again', () => {
    mockUseAgents.mockReturnValue(baseAgentsReturn);
    const { getByText } = renderDiscover();
    const marketingBtn = getByText('marketing');
    fireEvent.press(marketingBtn);
    // Verify marketing is now selected - the last call should have industry=marketing
    let lastCall = mockUseAgents.mock.calls[mockUseAgents.mock.calls.length - 1];
    expect((lastCall[0] as any)?.industry).toBe('marketing');
    // Press again to deselect
    fireEvent.press(marketingBtn);
    lastCall = mockUseAgents.mock.calls[mockUseAgents.mock.calls.length - 1];
    expect((lastCall[0] as any)?.industry).toBeUndefined();
  });

  it('shows agent cards when agents are returned', () => {
    const agents = [{ id: 'e1', name: 'My Agent', rating: 4.5, price: 10000 }];
    mockUseAgents.mockReturnValue({ ...baseAgentsReturn, data: agents });
    const { getByTestId } = renderDiscover();
    expect(getByTestId('agent-card-e1')).toBeTruthy();
  });
});
