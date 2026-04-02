import React from 'react';
import { render, screen } from '@testing-library/react-native';

jest.mock('../../../hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      white: '#ffffff',
      textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe',
    },
    spacing: {
      md: 16,
      xl: 32,
    },
    typography: {
      textVariants: {
        body: {},
      },
    },
  }),
}));

jest.mock('../../../hooks/useAgents', () => ({
  useSearchAgents: jest.fn(),
}));

jest.mock('../../../components/AgentCard', () => ({
  AgentCard: ({ agent }: any) => <>{agent.name}</>,
}));

import SearchResultsScreen from '../SearchResultsScreen';

const { useSearchAgents } = jest.requireMock('../../../hooks/useAgents') as {
  useSearchAgents: jest.Mock;
};

describe('SearchResultsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders agent cards from search results', () => {
    useSearchAgents.mockReturnValue({
      data: [
        { id: 'a1', name: 'Marketing Pro', industry: 'marketing', status: 'active', job_role_id: 'jr-1', entity_type: 'agent', created_at: '2026-04-02T00:00:00Z' },
        { id: 'a2', name: 'Sales Closer', industry: 'sales', status: 'active', job_role_id: 'jr-2', entity_type: 'agent', created_at: '2026-04-02T00:00:00Z' },
      ],
      isLoading: false,
      error: null,
    });

    render(
      <SearchResultsScreen
        navigation={{ navigate: jest.fn() } as any}
        route={{ key: 'search', name: 'SearchResults', params: { query: 'agent' } } as any}
      />
    );

    expect(screen.getByText('Marketing Pro')).toBeTruthy();
    expect(screen.getByText('Sales Closer')).toBeTruthy();
  });

  it('renders an empty state when no agents are found', () => {
    useSearchAgents.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    render(
      <SearchResultsScreen
        navigation={{ navigate: jest.fn() } as any}
        route={{ key: 'search', name: 'SearchResults', params: { query: 'ghost' } } as any}
      />
    );

    expect(screen.getByText('No agents found for "ghost"')).toBeTruthy();
  });

  it('renders a loading message while searching', () => {
    useSearchAgents.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    render(
      <SearchResultsScreen
        navigation={{ navigate: jest.fn() } as any}
        route={{ key: 'search', name: 'SearchResults', params: { query: 'marketing' } } as any}
      />
    );

    expect(screen.getByText('Searching for "marketing"...')).toBeTruthy();
  });
});
