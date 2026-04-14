/**
 * PlatformConnectionsScreen (MOB-PARITY-1 E4-S1)
 *
 * Lists all platform connections for a hired agent with status badges.
 * YouTube uses OAuth; other platforms use credential input form.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Modal,
} from 'react-native';
import { useRoute, RouteProp } from '@react-navigation/native';
import * as WebBrowser from 'expo-web-browser';
import { makeRedirectUri } from 'expo-auth-session';
import { useTheme } from '../../hooks/useTheme';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorView } from '../../components/ErrorView';
import { EmptyState } from '../../components/EmptyState';
import { usePlatformConnections } from '../../hooks/usePlatformConnections';
import type { PlatformConnection, CreateConnectionBody } from '../../services/platformConnections.service';
import type { MyAgentsStackParamList } from '../../navigation/types';

type PlatformConnectionsRouteProp = RouteProp<MyAgentsStackParamList, 'PlatformConnections'>;

const PLATFORM_LABELS: Record<string, string> = {
  youtube: 'YouTube',
  instagram: 'Instagram',
  facebook: 'Facebook',
  linkedin: 'LinkedIn',
  x: 'X (Twitter)',
};

function getPlatformLabel(key: string) {
  return PLATFORM_LABELS[key.toLowerCase()] ?? key;
}

function getStatusColor(status: string | undefined, successColor: string, warningColor: string, errorColor: string) {
  const s = String(status ?? '').toLowerCase();
  if (s === 'connected' || s === 'active') return successColor;
  if (s === 'pending') return warningColor;
  return errorColor;
}

// ─── Credential Form Modal ────────────────────────────────────────────────────

interface CredentialFormProps {
  platformKey: string;
  skillId: string;
  visible: boolean;
  onSubmit: (body: CreateConnectionBody) => void;
  onCancel: () => void;
}

function CredentialFormModal({ platformKey, skillId, visible, onSubmit, onCancel }: CredentialFormProps) {
  const { colors, spacing, typography } = useTheme();
  const [apiKey, setApiKey] = useState('');

  const handleSubmit = () => {
    onSubmit({
      skill_id: skillId,
      platform_key: platformKey,
      credentials: { api_key: apiKey },
    });
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onCancel}>
      <View style={{ flex: 1, backgroundColor: '#000000aa', justifyContent: 'flex-end' }}>
        <View
          testID="credential-form-modal"
          style={{
            backgroundColor: colors.card,
            borderTopLeftRadius: spacing.lg,
            borderTopRightRadius: spacing.lg,
            padding: spacing.lg,
            paddingBottom: spacing.xxl ?? 48,
          }}
        >
          <Text
            style={{
              color: colors.textPrimary,
              fontSize: 18,
              fontFamily: typography.fontFamily.bodyBold,
              marginBottom: spacing.md,
            }}
          >
            Connect {getPlatformLabel(platformKey)}
          </Text>
          <TextInput
            testID="credential-input-api-key"
            value={apiKey}
            onChangeText={setApiKey}
            placeholder="API Key / Access Token"
            placeholderTextColor={colors.textSecondary}
            secureTextEntry
            style={{
              backgroundColor: colors.black,
              color: colors.textPrimary,
              borderRadius: spacing.sm,
              padding: spacing.md,
              fontFamily: typography.fontFamily.body,
              fontSize: 14,
              marginBottom: spacing.md,
            }}
          />
          <TouchableOpacity
            testID="credential-submit-btn"
            onPress={handleSubmit}
            style={{
              backgroundColor: colors.neonCyan,
              borderRadius: spacing.sm,
              padding: spacing.md,
              alignItems: 'center',
              marginBottom: spacing.sm,
            }}
          >
            <Text style={{ color: colors.black, fontSize: 15, fontFamily: typography.fontFamily.bodyBold }}>
              Connect
            </Text>
          </TouchableOpacity>
          <TouchableOpacity testID="credential-cancel-btn" onPress={onCancel} style={{ alignItems: 'center' }}>
            <Text style={{ color: colors.textSecondary, fontSize: 14, fontFamily: typography.fontFamily.body }}>
              Cancel
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

// ─── Platform Card ────────────────────────────────────────────────────────────

interface PlatformCardProps {
  platformKey: string;
  connection: PlatformConnection | null;
  hiredAgentId: string;
  onConnect: (platformKey: string) => void;
  onConnectYouTube: () => void;
  onDisconnect: (connectionId: string) => void;
}

function PlatformCard({
  platformKey,
  connection,
  onConnect,
  onConnectYouTube,
  onDisconnect,
}: PlatformCardProps) {
  const { colors, spacing, typography } = useTheme();

  const statusColor = connection
    ? getStatusColor(
        connection.status,
        colors.success ?? '#10b981',
        colors.warning ?? '#f59e0b',
        colors.error
      )
    : colors.textSecondary;

  const isConnected = connection && (connection.status === 'connected' || connection.status === 'active');
  const isYouTube = platformKey.toLowerCase() === 'youtube';

  return (
    <View
      testID={`platform-card-${platformKey}`}
      style={[
        styles.platformCard,
        {
          backgroundColor: colors.card,
          borderRadius: spacing.md,
          padding: spacing.md,
          marginBottom: spacing.sm,
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
        },
      ]}
    >
      <View style={{ flex: 1 }}>
        <Text
          style={{
            color: colors.textPrimary,
            fontSize: 16,
            fontFamily: typography.fontFamily.bodyBold,
            marginBottom: spacing.xs,
          }}
        >
          {getPlatformLabel(platformKey)}
        </Text>
        {connection?.last_verified_at && (
          <Text style={{ color: colors.textSecondary, fontSize: 11, fontFamily: typography.fontFamily.body }}>
            Verified {new Date(connection.last_verified_at).toLocaleDateString()}
          </Text>
        )}
        <View
          testID={`status-badge-${platformKey}`}
          style={{
            backgroundColor: statusColor + '20',
            borderRadius: 4,
            paddingHorizontal: 6,
            paddingVertical: 1,
            alignSelf: 'flex-start',
            marginTop: spacing.xs,
          }}
        >
          <Text
            style={{
              color: statusColor,
              fontSize: 11,
              fontFamily: typography.fontFamily.bodyBold,
              textTransform: 'capitalize',
            }}
          >
            {connection?.status ?? 'Disconnected'}
          </Text>
        </View>
      </View>

      {isConnected ? (
        <TouchableOpacity
          testID={`disconnect-btn-${platformKey}`}
          onPress={() => connection && onDisconnect(connection.id)}
          style={{
            backgroundColor: colors.error + '20',
            borderRadius: spacing.sm,
            paddingHorizontal: spacing.md,
            paddingVertical: spacing.sm,
          }}
        >
          <Text style={{ color: colors.error, fontSize: 13, fontFamily: typography.fontFamily.bodyBold }}>
            Disconnect
          </Text>
        </TouchableOpacity>
      ) : isYouTube ? (
        <TouchableOpacity
          testID={`connect-youtube-btn`}
          onPress={onConnectYouTube}
          style={{
            backgroundColor: '#FF0000' + '20',
            borderRadius: spacing.sm,
            paddingHorizontal: spacing.md,
            paddingVertical: spacing.sm,
          }}
        >
          <Text style={{ color: '#FF0000', fontSize: 13, fontFamily: typography.fontFamily.bodyBold }}>
            Connect via Google
          </Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity
          testID={`connect-btn-${platformKey}`}
          onPress={() => onConnect(platformKey)}
          style={{
            backgroundColor: colors.neonCyan + '20',
            borderRadius: spacing.sm,
            paddingHorizontal: spacing.md,
            paddingVertical: spacing.sm,
          }}
        >
          <Text style={{ color: colors.neonCyan, fontSize: 13, fontFamily: typography.fontFamily.bodyBold }}>
            Connect
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

// ─── PlatformConnectionsScreen ────────────────────────────────────────────────

const SUPPORTED_PLATFORMS = ['youtube', 'instagram', 'facebook', 'linkedin', 'x'];
const DEFAULT_SKILL_ID = 'digital_marketing';

export function PlatformConnectionsScreen() {
  const { colors, spacing, typography } = useTheme();
  const route = useRoute<PlatformConnectionsRouteProp>();
  const { hiredAgentId } = route.params ?? {};

  const { connections, isLoading, error, refetch, connect, connectYouTube, disconnect } =
    usePlatformConnections(hiredAgentId);

  const [formPlatform, setFormPlatform] = useState<string | null>(null);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorView message="Failed to load connections" onRetry={refetch} />;

  const connectionMap: Record<string, PlatformConnection | null> = {};
  SUPPORTED_PLATFORMS.forEach((pk) => {
    connectionMap[pk] = connections.find((c) => c.platform_key.toLowerCase() === pk) ?? null;
  });

  const connectedCount = connections.filter(
    (c) => c.status === 'connected' || c.status === 'active'
  ).length;

  const handleConnect = (platformKey: string) => {
    setFormPlatform(platformKey);
  };

  const handleConnectYouTube = async () => {
    const redirectUri = makeRedirectUri({ path: 'youtube-callback' });
    const { authorization_url } = await connectYouTube(redirectUri);
    await WebBrowser.openBrowserAsync(authorization_url);
    refetch();
  };

  const handleFormSubmit = async (body: CreateConnectionBody) => {
    await connect(body);
    setFormPlatform(null);
    refetch();
  };

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.black }]}
      testID="platform-connections-screen"
    >
      <ScrollView
        contentContainerStyle={{
          paddingHorizontal: spacing.screenPadding?.horizontal ?? spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: 40,
        }}
      >
        {/* Header */}
        <Text
          style={{
            color: colors.neonCyan,
            fontSize: 11,
            fontFamily: typography.fontFamily.bodyBold,
            textTransform: 'uppercase',
            letterSpacing: 1,
            marginBottom: spacing.xs,
          }}
        >
          Integrations
        </Text>
        <Text
          style={{
            color: colors.textPrimary,
            fontSize: 26,
            fontFamily: typography.fontFamily.display,
            marginBottom: spacing.xs,
          }}
        >
          Platform Connections
        </Text>
        <Text
          testID="connections-summary"
          style={{
            color: colors.textSecondary,
            fontSize: 14,
            fontFamily: typography.fontFamily.body,
            marginBottom: spacing.xl,
          }}
        >
          {connectedCount} of {SUPPORTED_PLATFORMS.length} platforms connected
        </Text>

        {/* Platform Cards */}
        {SUPPORTED_PLATFORMS.length === 0 ? (
          <EmptyState message="No platforms configured" icon="🔌" />
        ) : (
          SUPPORTED_PLATFORMS.map((pk) => (
            <PlatformCard
              key={pk}
              platformKey={pk}
              connection={connectionMap[pk]}
              hiredAgentId={hiredAgentId ?? ''}
              onConnect={handleConnect}
              onConnectYouTube={handleConnectYouTube}
              onDisconnect={disconnect}
            />
          ))
        )}
      </ScrollView>

      {/* Credential form modal */}
      {formPlatform && (
        <CredentialFormModal
          platformKey={formPlatform}
          skillId={DEFAULT_SKILL_ID}
          visible={!!formPlatform}
          onSubmit={handleFormSubmit}
          onCancel={() => setFormPlatform(null)}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  platformCard: {},
});
