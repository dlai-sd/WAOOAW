/**
 * ConnectorSetupCard Component Tests (MOBILE-COMP-1 E1-S2)
 *
 * Coverage:
 * - Renders platform name
 * - Shows "Setup after trial starts" guidance status
 * - Shows credentials list (preflight, not live)
 * - Shows guidance note explaining connection happens after runtime creation
 * - No fake connected/disconnected toggle or persisted state
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render } from '@testing-library/react-native';
import { ConnectorSetupCard } from '@/components/ConnectorSetupCard';

describe('ConnectorSetupCard (MOBILE-COMP-1 E1-S2)', () => {
  const defaultProps = {
    platformName: 'Twitter / X',
    requiredCredentials: ['API Key', 'API Secret'],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders platform name', () => {
    const { getByText } = render(<ConnectorSetupCard {...defaultProps} />);
    expect(getByText('Twitter / X')).toBeTruthy();
  });

  it('shows "Setup after trial starts" guidance status (not connected/disconnected)', () => {
    const { getByText } = render(<ConnectorSetupCard {...defaultProps} />);
    expect(getByText('Setup after trial starts')).toBeTruthy();
  });

  it('shows guidance note explaining real connection happens after runtime creation', () => {
    const { getByText } = render(<ConnectorSetupCard {...defaultProps} />);
    expect(getByText(/connection happens after/i)).toBeTruthy();
  });

  it('shows required credentials label and list as preflight guidance', () => {
    const { getByText } = render(<ConnectorSetupCard {...defaultProps} />);
    expect(getByText('You will need:')).toBeTruthy();
    expect(getByText('• API Key')).toBeTruthy();
    expect(getByText('• API Secret')).toBeTruthy();
  });

  it('renders all required credentials', () => {
    const multiCredProps = {
      ...defaultProps,
      requiredCredentials: ['API Key', 'API Secret', 'Access Token'],
    };
    const { getByText } = render(<ConnectorSetupCard {...multiCredProps} />);
    expect(getByText('• API Key')).toBeTruthy();
    expect(getByText('• API Secret')).toBeTruthy();
    expect(getByText('• Access Token')).toBeTruthy();
  });

  it('does NOT render a connect or disconnect button (no fake toggle)', () => {
    const { queryByText } = render(<ConnectorSetupCard {...defaultProps} />);
    expect(queryByText('Connect Twitter / X')).toBeNull();
    expect(queryByText('Disconnect')).toBeNull();
    expect(queryByText('Connected')).toBeNull();
    expect(queryByText('Not connected')).toBeNull();
  });
});
