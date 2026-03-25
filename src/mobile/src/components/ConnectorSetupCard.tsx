/**
 * ConnectorSetupCard Component (MOBILE-COMP-1 E1-S2)
 *
 * Preflight guidance card shown in HireWizard step 2.
 * Shows required credentials and explains that real platform connection
 * happens after the runtime (hired agent instance) is created — not before.
 * This replaces the previous fake local-state toggle.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface ConnectorSetupCardProps {
  platformName: string;
  requiredCredentials: string[];
}

export function ConnectorSetupCard({
  platformName,
  requiredCredentials,
}: ConnectorSetupCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.platformName}>{platformName}</Text>
        <View style={[styles.statusChip, styles.statusPending]}>
          <Text style={styles.statusText}>Setup after trial starts</Text>
        </View>
      </View>

      <Text style={styles.guidanceNote}>
        Your {platformName} connection happens after your trial runtime is created. No credentials are stored before you start.
      </Text>

      <Text style={styles.credentialsLabel}>You will need:</Text>
      {requiredCredentials.map((cred) => (
        <Text key={cred} style={styles.credentialItem}>
          • {cred}
        </Text>
      ))}
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
  statusPending: {
    backgroundColor: '#f59e0b22',
  },
  statusText: {
    color: '#f59e0b',
    fontSize: 12,
  },
  guidanceNote: {
    color: '#a1a1aa',
    fontSize: 13,
    marginBottom: 12,
    lineHeight: 18,
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
});
