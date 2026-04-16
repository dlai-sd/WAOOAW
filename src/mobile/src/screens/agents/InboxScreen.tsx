/**
 * InboxScreen (MOB-PARITY-1 E1-S1)
 *
 * Standalone Inbox / Deliverables screen — shows all deliverables across all
 * hired agents. Supports status filtering (All / Pending / Approved / Rejected)
 * and voice-enabled approval via the mic FAB.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { useTheme } from '../../hooks/useTheme';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorView } from '../../components/ErrorView';
import { EmptyState } from '../../components/EmptyState';
import { VoiceFAB } from '../../components/voice/VoiceFAB';
import { useAllDeliverables, DeliverableWithStatus } from '../../hooks/useAllDeliverables';
import { useAgentVoiceOverlay } from '../../hooks/useAgentVoiceOverlay';
import type { MyAgentsStackScreenProps } from '../../navigation/types';

type FilterStatus = 'all' | 'pending' | 'approved' | 'rejected';

const FILTER_OPTIONS: { key: FilterStatus; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
];

// ─── Deliverable Card ─────────────────────────────────────────────────────────

interface DeliverableCardProps {
  item: DeliverableWithStatus;
  onApprove: (hiredAgentId: string, id: string) => void;
  onReject: (hiredAgentId: string, id: string) => void;
  onPress?: (item: DeliverableWithStatus) => void;
}

function DeliverableCard({ item, onApprove, onReject, onPress }: DeliverableCardProps) {
  const { colors, spacing, typography } = useTheme();

  const statusColor =
    item.status === 'approved'
      ? colors.success ?? '#10b981'
      : item.status === 'rejected'
      ? colors.error
      : colors.warning ?? '#f59e0b';

  function getTypeChipConfig(type: string): { label: string; color: string } {
    if (type === 'content_draft') return { label: 'Approval needed', color: colors.warning ?? '#f59e0b' };
    if (type === 'agent_update')  return { label: 'Agent update',     color: colors.neonCyan };
    if (type === 'billing_alert') return { label: 'Billing alert',    color: colors.error };
    return { label: 'Notification', color: colors.textSecondary };
  }

  const typeChip = getTypeChipConfig(item.type ?? '');

  return (
    <TouchableOpacity
      testID={`deliverable-card-${item.id}`}
      onPress={() => onPress?.(item)}
      activeOpacity={0.7}
      style={[
        styles.card,
        {
          backgroundColor: colors.card,
          borderRadius: spacing.md,
          marginBottom: spacing.sm,
          padding: spacing.md,
        },
      ]}
    >
      {/* Header row */}
      <View style={styles.cardHeader}>
        <View
          style={[
            styles.typeBadge,
            {
              backgroundColor: colors.neonCyan + '20',
              borderRadius: spacing.xs,
              paddingHorizontal: spacing.sm,
              paddingVertical: 2,
            },
          ]}
        >
          <Text
            style={{
              color: colors.neonCyan,
              fontSize: 11,
              fontFamily: typography.fontFamily.bodyBold,
              textTransform: 'uppercase',
            }}
          >
            {item.type ?? 'deliverable'}
          </Text>
        </View>
        <View
          style={[
            styles.statusBadge,
            {
              backgroundColor: statusColor + '20',
              borderRadius: spacing.xs,
              paddingHorizontal: spacing.sm,
              paddingVertical: 2,
            },
          ]}
        >
          <Text
            style={{
              color: statusColor,
              fontSize: 11,
              fontFamily: typography.fontFamily.bodyBold,
              textTransform: 'capitalize',
            }}
          >
            {item.status}
          </Text>
        </View>
      </View>

      {/* Title */}
      <Text
        style={{
          color: colors.textPrimary,
          fontSize: 16,
          fontFamily: typography.fontFamily.bodyBold,
          marginTop: spacing.sm,
          marginBottom: spacing.xs,
        }}
        numberOfLines={2}
        testID={`deliverable-title-${item.id}`}
      >
        {item.title ?? 'Untitled deliverable'}
      </Text>

      {/* Preview */}
      {item.content_preview && (
        <Text
          style={{
            color: colors.textSecondary,
            fontSize: 13,
            fontFamily: typography.fontFamily.body,
            marginBottom: spacing.sm,
          }}
          numberOfLines={2}
        >
          {item.content_preview}
        </Text>
      )}

      {/* Created at */}
      {item.created_at && (
        <Text
          style={{
            color: colors.textSecondary,
            fontSize: 12,
            fontFamily: typography.fontFamily.body,
            marginBottom: spacing.md,
          }}
        >
          {new Date(item.created_at).toLocaleDateString()}
        </Text>
      )}

      {/* Actions — only show for pending */}
      {item.status === 'pending' && (
        <View style={styles.actions}>
          <TouchableOpacity
            testID={`approve-btn-${item.id}`}
            onPress={() => onApprove(item.hired_agent_id, item.id)}
            style={[
              styles.actionBtn,
              {
                backgroundColor: (colors.success ?? '#10b981') + '20',
                borderRadius: spacing.sm,
                paddingHorizontal: spacing.lg,
                paddingVertical: spacing.sm,
                marginRight: spacing.sm,
              },
            ]}
          >
            <Text
              style={{
                color: colors.success ?? '#10b981',
                fontSize: 14,
                fontFamily: typography.fontFamily.bodyBold,
              }}
            >
              ✓ Approve
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            testID={`reject-btn-${item.id}`}
            onPress={() => onReject(item.hired_agent_id, item.id)}
            style={[
              styles.actionBtn,
              {
                backgroundColor: colors.error + '20',
                borderRadius: spacing.sm,
                paddingHorizontal: spacing.lg,
                paddingVertical: spacing.sm,
              },
            ]}
          >
            <Text
              style={{
                color: colors.error,
                fontSize: 14,
                fontFamily: typography.fontFamily.bodyBold,
              }}
            >
              ✕ Reject
            </Text>
          </TouchableOpacity>
        </View>
      )}
      {/* Type chip */}
      <View
        testID={`chip-${typeChip.label.toLowerCase().replace(/ /g, '-')}`}
        style={{
          marginTop: 8,
          alignSelf: 'flex-start',
          borderWidth: 1,
          borderColor: typeChip.color,
          backgroundColor: typeChip.color + '18',
          borderRadius: 4,
          paddingHorizontal: 6,
          paddingVertical: 2,
        }}
      >
        <Text style={{ color: typeChip.color, fontSize: 10,
          fontFamily: typography.fontFamily.bodyBold }}>
          {typeChip.label}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

// ─── InboxScreen ─────────────────────────────────────────────────────────────

export function InboxScreen({ navigation }: MyAgentsStackScreenProps<'Inbox'>) {
  const { colors, spacing, typography } = useTheme();
  const [filter, setFilter] = useState<FilterStatus>('all');

  const { deliverables, isLoading, error, approve, reject, refetch } = useAllDeliverables();

  const handleApprove = useCallback(
    (hiredAgentId: string, id: string) => {
      approve(hiredAgentId, id);
    },
    [approve]
  );

  const handleReject = useCallback(
    (hiredAgentId: string, id: string) => {
      reject(hiredAgentId, id);
    },
    [reject]
  );

  const handleCardPress = useCallback(
    (item: DeliverableWithStatus) => {
      navigation.navigate('DeliverableDetail', {
        deliverableId: item.id,
        hiredAgentId: item.hired_agent_id,
      });
    },
    [navigation]
  );

  const matchAndApprove = useCallback(
    (titleFragment: string) => {
      const match = deliverables.find(
        (d) =>
          d.status === 'pending' &&
          (d.title ?? '').toLowerCase().includes(titleFragment.toLowerCase())
      );
      if (match) handleApprove(match.hired_agent_id, match.id);
    },
    [deliverables, handleApprove]
  );

  const matchAndReject = useCallback(
    (titleFragment: string) => {
      const match = deliverables.find(
        (d) =>
          d.status === 'pending' &&
          (d.title ?? '').toLowerCase().includes(titleFragment.toLowerCase())
      );
      if (match) handleReject(match.hired_agent_id, match.id);
    },
    [deliverables, handleReject]
  );

  const { isListening, toggle, isAvailable } = useAgentVoiceOverlay({
    approve: matchAndApprove,
    reject: matchAndReject,
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorView message="Failed to load deliverables" onRetry={refetch} />;

  const filtered =
    filter === 'all' ? deliverables : deliverables.filter((d) => d.status === filter);

  const pendingCount = deliverables.filter((d) => d.status === 'pending').length;

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.black }]}
      testID="inbox-screen"
    >
      {/* Header */}
      <View
        style={{
          paddingHorizontal: spacing.screenPadding?.horizontal ?? spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: spacing.md,
        }}
      >
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
          Deliverables
        </Text>
        <Text
          style={{
            color: colors.textPrimary,
            fontSize: 26,
            fontFamily: typography.fontFamily.display,
          }}
        >
          Inbox{pendingCount > 0 ? ` (${pendingCount})` : ''}
        </Text>
      </View>

      {/* Filter chips */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: spacing.screenPadding?.horizontal ?? spacing.lg,
          paddingBottom: spacing.sm,
          gap: spacing.sm,
        }}
        testID="filter-chips"
      >
        {FILTER_OPTIONS.map((opt) => (
          <TouchableOpacity
            key={opt.key}
            testID={`filter-chip-${opt.key}`}
            onPress={() => setFilter(opt.key)}
            style={[
              styles.chip,
              {
                backgroundColor: filter === opt.key ? colors.neonCyan : colors.card,
                borderRadius: 999,
                paddingHorizontal: spacing.md,
                paddingVertical: spacing.xs,
              },
            ]}
          >
            <Text
              style={{
                color: filter === opt.key ? colors.black : colors.textSecondary,
                fontSize: 13,
                fontFamily: typography.fontFamily.bodyBold,
              }}
            >
              {opt.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* List */}
      <View style={{ flex: 1 }}>
        {filtered.length === 0 ? (
          <EmptyState message="No deliverables yet" icon="📭" />
        ) : (
          <FlashList
            data={filtered}
            keyExtractor={(item) => item.id}
            estimatedItemSize={160}
            contentContainerStyle={{
              paddingHorizontal: spacing.screenPadding?.horizontal ?? spacing.lg,
              paddingBottom: 100,
            }}
            renderItem={({ item }) => (
              <DeliverableCard
                item={item}
                onApprove={handleApprove}
                onReject={handleReject}
                onPress={handleCardPress}
              />
            )}
          />
        )}
      </View>

      {/* Voice FAB */}
      {isAvailable && (
        <VoiceFAB
          isListening={isListening}
          onPress={toggle}
          testID="voice-fab"
          position="bottom-right"
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  typeBadge: {},
  statusBadge: {},
  card: {},
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionBtn: {},
  chip: {},
});
