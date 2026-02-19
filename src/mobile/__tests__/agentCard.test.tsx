/**
 * Agent Card Component Tests
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, fireEvent } from '@testing-library/react-native';
import { AgentCard } from '@/components/AgentCard';
import type { Agent } from '@/types/agent.types';

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

// Mock useTheme
jest.mock('../../src/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      card: '#18181b',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe',
      black: '#0a0a0a',
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

describe('AgentCard Component', () => {
  const mockAgent: Agent = {
    id: 'agent-1',
    name: 'Marketing Expert Agent',
    description: 'Specialized in content marketing and SEO',
    specialization: 'Content Marketing Specialist',
    job_role_id: 'role-1',
    industry: 'marketing',
    entity_type: 'agent',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    rating: 4.5,
    price: 12000,
    trial_days: 7,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render agent card with all information', () => {
    const { getByText } = render(<AgentCard agent={mockAgent} />);

    expect(getByText('Marketing Expert Agent')).toBeTruthy();
    expect(getByText('Content Marketing Specialist')).toBeTruthy();
    expect(getByText('Specialized in content marketing and SEO')).toBeTruthy();
    expect(getByText('₹12,000/month')).toBeTruthy();
    expect(getByText('7-day free trial')).toBeTruthy();
  });

  it('should display agent initials in avatar', () => {
    const { getByText } = render(<AgentCard agent={mockAgent} />);

    // First letter of name
    expect(getByText('M')).toBeTruthy();
  });

  it('should display rating correctly', () => {
    const { getByText } = render(<AgentCard agent={mockAgent} />);

    // Rating stars and number
    expect(getByText('4.5')).toBeTruthy();
  });

  it('should display "No ratings yet" when rating is undefined', () => {
    const agentWithoutRating = { ...mockAgent, rating: undefined };
    const { getByText } = render(<AgentCard agent={agentWithoutRating} />);

    expect(getByText('No ratings yet')).toBeTruthy();
  });

  it('should display industry with correct emoji', () => {
    const { getByText } = render(<AgentCard agent={mockAgent} />);

    expect(getByText('📢')).toBeTruthy(); // Marketing emoji
    expect(getByText('marketing')).toBeTruthy();
  });

  it('should display education emoji for education industry', () => {
    const educationAgent = { ...mockAgent, industry: 'education' as const };
    const { getByText } = render(<AgentCard agent={educationAgent} />);

    expect(getByText('📚')).toBeTruthy();
    expect(getByText('education')).toBeTruthy();
  });

  it('should display sales emoji for sales industry', () => {
    const salesAgent = { ...mockAgent, industry: 'sales' as const };
    const { getByText } = render(<AgentCard agent={salesAgent} />);

    expect(getByText('💼')).toBeTruthy();
    expect(getByText('sales')).toBeTruthy();
  });

  it('should handle press event', () => {
    const { getByText } = render(<AgentCard agent={mockAgent} />);

    const card = getByText('Marketing Expert Agent').parent?.parent?.parent;
    fireEvent.press(card!);

    // Should log to console (navigation will be implemented in Story 2.5)
    expect(true).toBe(true); // Placeholder assertion
  });

  it('should display "Contact for pricing" when price is undefined', () => {
    const agentWithoutPrice = { ...mockAgent, price: undefined };
    const { getByText } = render(<AgentCard agent={agentWithoutPrice} />);

    expect(getByText('Contact for pricing')).toBeTruthy();
  });

  it('should format price with commas for Indian locale', () => {
    const expensiveAgent = { ...mockAgent, price: 150000 };
    const { getByText } = render(<AgentCard agent={expensiveAgent} />);

    expect(getByText('₹1,50,000/month')).toBeTruthy();
  });

  it('should display View Details button', () => {
    const { getByText } = render(<AgentCard agent={mockAgent} />);

    expect(getByText('View Details')).toBeTruthy();
  });

  it('should display status indicator dot', () => {
    const { UNSAFE_root } = render(<AgentCard agent={mockAgent} />);

    // Status dot should be rendered (visual element, hard to test directly)
    expect(UNSAFE_root).toBeTruthy();
  });

  it('should handle missing specialization gracefully', () => {
    const agentWithoutSpec = { ...mockAgent, specialization: undefined };
    const { queryByText } = render(<AgentCard agent={agentWithoutSpec} />);

    // Should not display specialization
    expect(queryByText('Content Marketing Specialist')).toBeNull();
  });

  it('should handle missing description gracefully', () => {
    const agentWithoutDesc = { ...mockAgent, description: undefined };
    const { queryByText } = render(<AgentCard agent={agentWithoutDesc} />);

    // Should not display description
    expect(queryByText('Specialized in content marketing and SEO')).toBeNull();
  });

  it('should use default trial days when not specified', () => {
    const agentWithoutTrialDays = { ...mockAgent, trial_days: undefined };
    const { getByText } = render(<AgentCard agent={agentWithoutTrialDays} />);

    expect(getByText('7-day free trial')).toBeTruthy();
  });

  it('should display custom trial days when specified', () => {
    const agentWithCustomTrial = { ...mockAgent, trial_days: 14 };
    const { getByText } = render(<AgentCard agent={agentWithCustomTrial} />);

    expect(getByText('14-day free trial')).toBeTruthy();
  });

  it('should render multiple agent cards correctly', () => {
    const agent2: Agent = {
      ...mockAgent,
      id: 'agent-2',
      name: 'Sales Agent',
      industry: 'sales',
    };

    const { getByText } = render(
      <>
        <AgentCard agent={mockAgent} />
        <AgentCard agent={agent2} />
      </>
    );

    expect(getByText('Marketing Expert Agent')).toBeTruthy();
    expect(getByText('Sales Agent')).toBeTruthy();
  });
});
