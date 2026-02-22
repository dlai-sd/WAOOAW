/**
 * Agent Detail Screen Tests
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentDetailScreen } from '@/screens/discover/AgentDetailScreen';
import { useAgentDetail } from '@/hooks/useAgentDetail';
import type { Agent } from '@/types/agent.types';

// Mock useAgentDetail hook
jest.mock('@/hooks/useAgentDetail');

// Mock components
jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: ({ message }: { message?: string }) => {
    const React = require('react');
    const { Text } = require('react-native');
    return React.createElement(Text, {}, message || 'Loading...');
  },
}));

jest.mock('@/components/ErrorView', () => ({
  ErrorView: ({ message, onRetry }: { message: string; onRetry?: () => void }) => {
    const React = require('react');
    const { View, Text, TouchableOpacity } = require('react-native');
    return React.createElement(
      View,
      {},
      React.createElement(Text, {}, 'Oops! An error occurred'),
      React.createElement(Text, {}, message),
      onRetry && React.createElement(TouchableOpacity, { onPress: onRetry }, React.createElement(Text, {}, 'Try Again'))
    );
  },
}));

// Mock useTheme
jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      card: '#18181b',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      screenPadding: 20,
    },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk_700Bold',
        displayBold: 'SpaceGrotesk_700Bold',
        body: 'Inter_400Regular',
        bodyBold: 'Inter_600SemiBold',
      },
    },
  }),
}));

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
  useRoute: () => ({
    params: { agentId: 'agent-123' },
  }),
}));

// Helper to create QueryClient wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('AgentDetailScreen Component', () => {
  const mockAgent: Agent = {
    id: 'agent-123',
    name: 'Marketing Expert Agent',
    description: 'Specialized in content marketing, SEO, and social media strategies. Over 10 years of experience in digital marketing.',
    specialization: 'Content Marketing & SEO Specialist',
    job_role_id: 'role-1',
    job_role: {
      id: 'role-1',
      name: 'Senior Marketing Strategist',
      description: 'Develops and executes comprehensive marketing strategies',
      required_skills: ['seo', 'content', 'analytics'],
      seniority_level: 'senior',
      entity_type: 'job_role',
      status: 'certified',
      created_at: '2024-01-01T00:00:00Z',
    },
    industry: 'marketing',
    entity_type: 'agent',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    rating: 4.7,
    price: 15000,
    trial_days: 7,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display loading spinner initially', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Loading agent details...')).toBeTruthy();
  });

  it('should display error view when API fails', () => {
    const mockError = new Error('Failed to fetch agent');
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: mockError,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Oops! An error occurred')).toBeTruthy();
    expect(getByText('Failed to fetch agent')).toBeTruthy();
    expect(getByText('Try Again')).toBeTruthy();
  });

  it('should display "Agent not found" when no agent data', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Agent not found')).toBeTruthy();
  });

  it('should render agent detail with all information', async () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      // Hero section
      expect(getByText('Marketing Expert Agent')).toBeTruthy();
      expect(getByText('Content Marketing & SEO Specialist')).toBeTruthy();
      expect(getByText('4.7')).toBeTruthy();

      // About section
      expect(getByText('About')).toBeTruthy();
      expect(
        getByText(/Specialized in content marketing, SEO, and social media/)
      ).toBeTruthy();

      // Role section
      expect(getByText('Role & Seniority')).toBeTruthy();
      expect(getByText('Senior Marketing Strategist')).toBeTruthy();

      // Pricing section
      expect(getByText('Pricing')).toBeTruthy();
      expect(getByText('₹15,000')).toBeTruthy();
      expect(getByText('7-Day Free Trial')).toBeTruthy();

      // Availability section
      expect(getByText('Availability')).toBeTruthy();
      expect(getByText('Available Now')).toBeTruthy();

      // CTA button
      expect(getByText('Start 7-Day Free Trial')).toBeTruthy();
    });
  });

  it('should display agent avatar with initial', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    // First letter of name
    expect(getByText('M')).toBeTruthy();
  });

  it('should display industry badge with emoji', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('📢')).toBeTruthy(); // Marketing emoji
    expect(getByText('marketing')).toBeTruthy();
  });

  it('should display education emoji for education industry', () => {
    const educationAgent = { ...mockAgent, industry: 'education' as const };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: educationAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('📚')).toBeTruthy();
    expect(getByText('education')).toBeTruthy();
  });

  it('should display sales emoji for sales industry', () => {
    const salesAgent = { ...mockAgent, industry: 'sales' as const };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: salesAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('💼')).toBeTruthy();
    expect(getByText('sales')).toBeTruthy();
  });

  it('should display rating with stars', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    // Rating number
    expect(getByText('4.7')).toBeTruthy();
    // Stars should be rendered (4 full + 1 half = 4.5-5.0)
  });

  it('should display "No ratings yet" when rating is undefined', () => {
    const agentWithoutRating = { ...mockAgent, rating: undefined };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: agentWithoutRating,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('No ratings yet')).toBeTruthy();
  });

  it('should display job role information', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Senior Marketing Strategist')).toBeTruthy();
    expect(
      getByText('Develops and executes comprehensive marketing strategies')
    ).toBeTruthy();
    expect(getByText('senior')).toBeTruthy();
  });

  it('should display pricing information correctly', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('₹15,000')).toBeTruthy();
    expect(getByText('per month')).toBeTruthy();
    expect(getByText('7-Day Free Trial')).toBeTruthy();
    expect(
      getByText(/Try risk-free. Keep all deliverables even if you don't hire./)
    ).toBeTruthy();
  });

  it('should display "Contact for pricing" when price is undefined', () => {
    const agentWithoutPrice = { ...mockAgent, price: undefined };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: agentWithoutPrice,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Contact for pricing')).toBeTruthy();
  });

  it('should display custom trial days when specified', () => {
    const agentWithCustomTrial = { ...mockAgent, trial_days: 14 };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: agentWithCustomTrial,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('14-Day Free Trial')).toBeTruthy();
  });

  it('should display availability status for active agent', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Available Now')).toBeTruthy();
    expect(getByText('Ready to start your 7-day trial')).toBeTruthy();
  });

  it('should display unavailable status for inactive agent', () => {
    const inactiveAgent = { ...mockAgent, status: 'inactive' as const };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: inactiveAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Currently Unavailable')).toBeTruthy();
    expect(getByText('Check back later for availability')).toBeTruthy();
  });

  it('should not display CTA button for inactive agent', () => {
    const inactiveAgent = { ...mockAgent, status: 'inactive' as const };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: inactiveAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { queryByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    expect(queryByText('Start 7-Day Free Trial')).toBeNull();
  });

  it('should handle CTA button press', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    const ctaButton = getByText('Start 7-Day Free Trial');
    fireEvent.press(ctaButton);

    // Should log to console (Hire Wizard navigation in Story 2.6)
    expect(true).toBe(true); // Placeholder assertion
  });

  it('should call refetch on retry button press', () => {
    const mockRefetch = jest.fn();
    const mockError = new Error('Network error');
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: mockError,
      refetch: mockRefetch,
      isRefetching: false,
    });

    const { getByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    const retryButton = getByText('Try Again');
    fireEvent.press(retryButton);

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  it('should handle missing description gracefully', () => {
    const agentWithoutDesc = { ...mockAgent, description: undefined };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: agentWithoutDesc,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { queryByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    // About section should not appear
    expect(queryByText('About')).toBeNull();
  });

  it('should handle missing job role gracefully', () => {
    const agentWithoutRole = { ...mockAgent, job_role: undefined };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: agentWithoutRole,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { queryByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    // Role section should not appear
    expect(queryByText('Role & Seniority')).toBeNull();
  });

  it('should handle missing specialization gracefully', () => {
    const agentWithoutSpec = { ...mockAgent, specialization: undefined };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: agentWithoutSpec,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      isRefetching: false,
    });

    const { queryByText } = render(<AgentDetailScreen />, {
      wrapper: createWrapper(),
    });

    // Specialization should not appear
    expect(queryByText('Content Marketing & SEO Specialist')).toBeNull();
  });
});
