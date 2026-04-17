/**
 * useAgentTypes Hook Tests
 */

import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const mockListAgentTypes = jest.fn();

jest.mock('../../src/services/agents/agent.service', () => ({
  agentService: {
    listAgentTypes: () => mockListAgentTypes(),
  },
}));

import { useAgentTypes } from '../../src/hooks/useAgentTypes';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const MOCK_AGENT_TYPES = [
  { agent_type_id: 'marketing.digital_marketing.v1', display_name: 'Digital Marketing Agent' },
  { agent_type_id: 'education.math_tutor.v1', display_name: 'Math Tutor' },
];

describe('useAgentTypes', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches agent types successfully', async () => {
    mockListAgentTypes.mockResolvedValue(MOCK_AGENT_TYPES);
    const { result } = renderHook(() => useAgentTypes(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toHaveLength(2);
    expect(mockListAgentTypes).toHaveBeenCalled();
  });

  it('provides undefined data during loading', () => {
    mockListAgentTypes.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useAgentTypes(), { wrapper: createWrapper() });
    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });
});
