/**
 * DeliverableDetailScreen (MOB-PARITY-2 E7-S1)
 *
 * Full-content view of a single deliverable with approve/reject actions.
 * Reject uses the same reject-with-reason pattern as E5-S1.
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import cpApiClient from '@/lib/cpApiClient';
import { useTheme } from '@/hooks/useTheme';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorView } from '@/components/ErrorView';
import type { MyAgentsStackScreenProps } from '@/navigation/types';
import type { DeliverableItem } from '@/hooks/useApprovalQueue';

// ─── data fetching ────────────────────────────────────────────────────────────

async function fetchDeliverable(hiredAgentId: string, deliverableId: string): Promise<DeliverableItem> {
  const response = await cpApiClient.get<DeliverableItem>(
    `/cp/hired-agents/${hiredAgentId}/approval-queue/${deliverableId}`
  );
  return response.data;
}

async function approveDeliverable(hiredAgentId: string, deliverableId: string): Promise<void> {
  await cpApiClient.post(
    `/cp/hired-agents/${hiredAgentId}/approval-queue/${deliverableId}/approve`
  );
}

async function rejectDeliverableWithReason(
  hiredAgentId: string,
  deliverableId: string,
  reason: string
): Promise<void> {
  await cpApiClient.post(
    `/cp/hired-agents/${hiredAgentId}/approval-queue/${deliverableId}/reject`,
    { reason }
  );
}

// ─── Screen ──────────────────────────────────────────────────────────────────

export function DeliverableDetailScreen({
  route,
  navigation,
}: MyAgentsStackScreenProps<'DeliverableDetail'>) {
  const { deliverableId, hiredAgentId } = route.params;
  const { colors, spacing, typography } = useTheme();
  const queryClient = useQueryClient();

  const [rejectMode, setRejectMode] = React.useState(false);
  const [rejectReason, setRejectReason] = React.useState('');

  const queryKey = ['deliverable', hiredAgentId, deliverableId];

  const { data: deliverable, isLoading, error, refetch } = useQuery({
    queryKey,
    queryFn: () => fetchDeliverable(hiredAgentId, deliverableId),
  });

  const approveMutation = useMutation({
    mutationFn: () => approveDeliverable(hiredAgentId, deliverableId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['approvalQueue', hiredAgentId] });
      navigation.goBack();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (reason: string) => rejectDeliverableWithReason(hiredAgentId, deliverableId, reason),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['approvalQueue', hiredAgentId] });
      navigation.goBack();
    },
  });

  if (isLoading) return <LoadingSpinner testID="detail-loading" />;
  if (error || !deliverable) return <ErrorView message="Could not load deliverable" onRetry={refetch} testID="detail-error" />;

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.black }]}>
      <ScrollView
        testID="deliverable-detail-screen"
        contentContainerStyle={{ padding: spacing.lg, paddingBottom: 60 }}
      >
        {/* Back */}
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginBottom: spacing.md }}>
          <Text style={{ color: colors.neonCyan, fontSize: 13, fontFamily: typography.fontFamily.body }}>
            ← Back
          </Text>
        </TouchableOpacity>

        {/* Meta row */}
        <View style={{ flexDirection: 'row', gap: 12, marginBottom: spacing.md }}>
          {deliverable.target_platform && (
            <Text testID="detail-platform" style={{ color: colors.textSecondary,
              fontSize: 12, fontFamily: typography.fontFamily.body }}>
              {deliverable.target_platform}
            </Text>
          )}
          {deliverable.type && (
            <Text testID="detail-type" style={{ color: colors.textSecondary,
              fontSize: 12, fontFamily: typography.fontFamily.body }}>
              {deliverable.type}
            </Text>
          )}
          {deliverable.created_at && (
            <Text testID="detail-created-at" style={{ color: colors.textSecondary,
              fontSize: 12, fontFamily: typography.fontFamily.body }}>
              {new Date(deliverable.created_at).toLocaleDateString()}
            </Text>
          )}
        </View>

        {/* Title */}
        {deliverable.title && (
          <Text style={{ color: colors.textPrimary, fontSize: 20,
            fontFamily: typography.fontFamily.display, marginBottom: spacing.md }}>
            {deliverable.title}
          </Text>
        )}

        {/* Full content — no truncation */}
        {(deliverable.content_preview || deliverable.description) && (
          <Text style={{ color: colors.textPrimary, fontSize: 14,
            fontFamily: typography.fontFamily.body, lineHeight: 22, marginBottom: spacing.lg }}>
            {deliverable.content_preview ?? deliverable.description}
          </Text>
        )}

        {/* Actions */}
        <View style={{ flexDirection: 'row', gap: 12, marginBottom: spacing.md }}>
          <TouchableOpacity
            testID="detail-approve-btn"
            disabled={approveMutation.isPending}
            onPress={() => approveMutation.mutate()}
            style={[styles.actionBtn, { backgroundColor: '#10b98122' }]}
          >
            {approveMutation.isPending
              ? <ActivityIndicator size="small" color="#10b981" />
              : <Text style={{ color: '#10b981', fontSize: 14, fontWeight: '600' }}>✓ Approve</Text>}
          </TouchableOpacity>

          {!rejectMode && (
            <TouchableOpacity
              testID="detail-reject-btn"
              onPress={() => setRejectMode(true)}
              style={[styles.actionBtn, { backgroundColor: '#ef444422' }]}
            >
              <Text style={{ color: '#ef4444', fontSize: 14, fontWeight: '600' }}>✕ Reject</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Reject-with-reason expansion */}
        {rejectMode && (
          <View>
            <TextInput
              testID="reject-reason-input"
              value={rejectReason}
              onChangeText={setRejectReason}
              placeholder="Reason for rejection…"
              placeholderTextColor={colors.textSecondary}
              multiline
              style={[styles.reasonInput, { borderColor: '#ef4444', color: colors.textPrimary,
                fontFamily: typography.fontFamily.body }]}
            />
            <View style={{ flexDirection: 'row', gap: 10 }}>
              <TouchableOpacity
                testID="reject-reason-cancel"
                style={[styles.actionBtn, { backgroundColor: '#27272a' }]}
                onPress={() => { setRejectMode(false); setRejectReason(''); }}
              >
                <Text style={{ color: colors.textSecondary, fontSize: 13 }}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                testID="reject-reason-confirm"
                disabled={rejectReason.trim().length === 0 || rejectMutation.isPending}
                onPress={() => rejectMutation.mutate(rejectReason.trim())}
                style={[styles.actionBtn, {
                  backgroundColor: rejectReason.trim().length === 0 ? '#ef444411' : '#ef444422',
                }]}
              >
                {rejectMutation.isPending
                  ? <ActivityIndicator size="small" color="#ef4444" />
                  : <Text style={{ color: rejectReason.trim().length === 0 ? '#ef444466' : '#ef4444',
                      fontSize: 13, fontWeight: '600' }}>
                      Confirm Rejection
                    </Text>}
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  actionBtn: {
    flex: 1,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  reasonInput: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    fontSize: 13,
    minHeight: 64,
    backgroundColor: '#18181b',
    textAlignVertical: 'top',
    marginBottom: 8,
  },
});
