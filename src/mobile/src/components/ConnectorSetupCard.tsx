/**
 * ConnectorSetupCard Component (CP-MOULD-1 E4-S1)
 *
 * Shows platform connection status in the HireWizard "Connect Platform" step.
 * Displays required credentials and connect / disconnect actions.
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface ConnectorSetupCardProps {
  platformName: string;
  requiredCredentials: string[];
  isConnected: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

export function ConnectorSetupCard({
  platformName,
  requiredCredentials,
  isConnected,
  onConnect,
  onDisconnect,
}: ConnectorSetupCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.platformName}>{platformName}</Text>
        <View
          style={[
            styles.statusChip,
            isConnected ? styles.statusConnected : styles.statusDisconnected,
          ]}
        >
          <Text style={styles.statusText}>
            {isConnected ? 'Connected' : 'Not connected'}
          </Text>
        </View>
      </View>

      {!isConnected && (
        <>
          <Text style={styles.credentialsLabel}>You'll need:</Text>
          {requiredCredentials.map((cred) => (
            <Text key={cred} style={styles.credentialItem}>
              • {cred}
            </Text>
          ))}
          <TouchableOpacity style={styles.connectButton} onPress={onConnect}>
            <Text style={styles.connectButtonText}>Connect {platformName}</Text>
          </TouchableOpacity>
        </>
      )}

      {isConnected && (
        <TouchableOpacity style={styles.disconnectButton} onPress={onDisconnect}>
          <Text style={styles.disconnectButtonText}>Disconnect</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#18181b',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#27272a',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  platformName: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  statusChip: {
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  statusConnected: {
    backgroundColor: '#10b98122',
  },
  statusDisconnected: {
    backgroundColor: '#ef444422',
  },
  statusText: {
    color: '#ffffff',
    fontSize: 12,
  },
  credentialsLabel: {
    color: '#a1a1aa',
    fontSize: 13,
    marginBottom: 6,
  },
  credentialItem: {
    color: '#a1a1aa',
    fontSize: 13,
    marginBottom: 4,
  },
  connectButton: {
    backgroundColor: '#00f2fe22',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#00f2fe',
  },
  connectButtonText: {
    color: '#00f2fe',
    fontSize: 14,
    fontWeight: '600',
  },
  disconnectButton: {
    backgroundColor: '#ef444422',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  disconnectButtonText: {
    color: '#ef4444',
    fontSize: 14,
    fontWeight: '600',
  },
});
