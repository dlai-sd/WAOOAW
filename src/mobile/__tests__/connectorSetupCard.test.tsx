/**
 * ConnectorSetupCard Component Tests (CP-MOULD-1 E4-S1)
 *
 * Coverage:
 * - Renders platform name
 * - Shows "Not connected" status and credentials list when isConnected=false
 * - Shows "Connect" button when isConnected=false
 * - Shows "Connected" status and "Disconnect" button when isConnected=true
 * - onConnect is called on button press
 * - onDisconnect is called on button press
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, fireEvent } from '@testing-library/react-native';
import { ConnectorSetupCard } from '@/components/ConnectorSetupCard';

describe('ConnectorSetupCard (CP-MOULD-1 E4-S1)', () => {
  const defaultProps = {
    platformName: 'Twitter / X',
    requiredCredentials: ['API Key', 'API Secret'],
    isConnected: false,
    onConnect: jest.fn(),
    onDisconnect: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders platform name', () => {
    const { getByText } = render(<ConnectorSetupCard {...defaultProps} />);
    expect(getByText('Twitter / X')).toBeTruthy();
  });

  it('shows "Not connected" status chip when isConnected=false', () => {
    const { getByText } = render(<ConnectorSetupCard {...defaultProps} />);
    expect(getByText('Not connected')).toBeTruthy();
  });

  it('shows required credentials list when isConnected=false', () => {
    const { getByText } = render(<ConnectorSetupCard {...defaultProps} />);
    expect(getByText("You'll need:")).toBeTruthy();
    expect(getByText('• API Key')).toBeTruthy();
    expect(getByText('• API Secret')).toBeTruthy();
  });

  it('shows connect button when isConnected=false', () => {
    const { getByText } = render(<ConnectorSetupCard {...defaultProps} />);
    expect(getByText('Connect Twitter / X')).toBeTruthy();
  });

  it('calls onConnect when connect button is pressed', () => {
    const { getByText } = render(<ConnectorSetupCard {...defaultProps} />);
    fireEvent.press(getByText('Connect Twitter / X'));
    expect(defaultProps.onConnect).toHaveBeenCalledTimes(1);
  });

  it('shows "Connected" status chip when isConnected=true', () => {
    const { getByText } = render(
      <ConnectorSetupCard {...defaultProps} isConnected={true} />
    );
    expect(getByText('Connected')).toBeTruthy();
  });

  it('shows disconnect button when isConnected=true', () => {
    const { getByText } = render(
      <ConnectorSetupCard {...defaultProps} isConnected={true} />
    );
    expect(getByText('Disconnect')).toBeTruthy();
  });

  it('does not show credentials list when isConnected=true', () => {
    const { queryByText } = render(
      <ConnectorSetupCard {...defaultProps} isConnected={true} />
    );
    expect(queryByText("You'll need:")).toBeNull();
    expect(queryByText('• API Key')).toBeNull();
  });

  it('calls onDisconnect when disconnect button is pressed', () => {
    const { getByText } = render(
      <ConnectorSetupCard {...defaultProps} isConnected={true} />
    );
    fireEvent.press(getByText('Disconnect'));
    expect(defaultProps.onDisconnect).toHaveBeenCalledTimes(1);
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
});
