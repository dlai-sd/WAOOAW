/**
 * ContentDraftApprovalCard (CP-MOULD-1 E5-S2)
 *
 * Displays a content draft deliverable requiring customer approval.
 * Shows content preview (first 200 chars), target platform, Approve/Reject buttons.
 */

import React from 'react';
import { View, Text, TouchableOpacity, TextInput, StyleSheet } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { DeliverableItem } from '@/hooks/useApprovalQueue';

interface ContentDraftApprovalCardProps {
  deliverable: DeliverableItem;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onRejectWithReason?: (id: string, reason: string) => void;
  readinessLabel?: string | null;
  readinessMessage?: string | null;
  channelStatusLabel?: string | null;
  approvalReference?: string | null;
}

const platformEmoji = (platform?: string): string => {
  if (!platform) return '📄';
  const p = platform.toLowerCase();
  if (p.includes('twitter') || p.includes('x')) return '🐦';
  if (p.includes('linkedin')) return '💼';
  if (p.includes('instagram')) return '📸';
  if (p.includes('facebook')) return '👥';
  return '📄';
};

export function ContentDraftApprovalCard({
  deliverable,
  onApprove,
  onReject,
  onRejectWithReason,
  readinessLabel,
  readinessMessage,
  channelStatusLabel,
  approvalReference,
}: ContentDraftApprovalCardProps) {
  const { colors, typography } = useTheme();
  const [rejectMode, setRejectMode] = React.useState(false);
  const [rejectReason, setRejectReason] = React.useState('');
  const isYouTube = String(deliverable.target_platform || '').trim().toLowerCase().includes('youtube');

  const preview = (deliverable.content_preview ?? deliverable.description ?? '')
    .slice(0, 200);

  return (
    <View style={[styles.card, { borderColor: colors.textSecondary + '20' }]}>
      {/* Platform & title row */}
      <View style={styles.headerRow}>
        <Text style={styles.platformEmoji}>
          {platformEmoji(deliverable.target_platform)}
        </Text>
        {deliverable.target_platform && (
          <Text style={[styles.platformLabel, { color: colors.textSecondary,
            fontFamily: typography.fontFamily.body }]}>
            {deliverable.target_platform}
          </Text>
        )}
        {deliverable.title && (
          <Text style={[styles.title, { color: colors.textPrimary,
            fontFamily: typography.fontFamily.bodyBold, flex: 1 }]} numberOfLines={1}>
            {deliverable.title}
          </Text>
        )}
      </View>

      {/* Content preview */}
      {preview.length > 0 && (
        <Text style={[styles.preview, { color: colors.textSecondary,
          fontFamily: typography.fontFamily.body }]}>
          {preview}{preview.length === 200 ? '…' : ''}
        </Text>
      )}

      {isYouTube && (
        <View style={[styles.infoCard, { borderColor: colors.textSecondary + '20' }]}> 
          <Text style={{ color: colors.textPrimary, fontSize: 13, fontFamily: typography.fontFamily.bodyBold, marginBottom: 4 }}>
            Exact approval required before YouTube action
          </Text>
          <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body, lineHeight: 18 }}>
            Approving this exact deliverable unlocks the next upload step, but it does not auto-publish anything externally.
          </Text>
        </View>
      )}

      {approvalReference ? (
        <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body, marginBottom: 8 }}>
          Approval reference: {approvalReference}
        </Text>
      ) : null}

      {channelStatusLabel ? (
        <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body, marginBottom: 6 }}>
          Channel status: {channelStatusLabel}
        </Text>
      ) : null}

      {readinessLabel ? (
        <View style={[styles.infoCard, { borderColor: colors.textSecondary + '20' }]}> 
          <Text style={{ color: colors.neonCyan, fontSize: 12, fontFamily: typography.fontFamily.bodyBold, marginBottom: 4 }}>
            Publish readiness: {readinessLabel}
          </Text>
          {readinessMessage ? (
            <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body, lineHeight: 18 }}>
              {readinessMessage}
            </Text>
          ) : null}
        </View>
      ) : null}

      {/* Action buttons */}
      <View style={styles.buttonsRow}>
        <TouchableOpacity
          style={[styles.btn, { backgroundColor: '#10b98122' }]}
          onPress={() => onApprove(deliverable.id)}
          accessibilityLabel={`Approve content draft ${deliverable.title ?? deliverable.id}`}
        >
          <Text style={{ color: '#10b981', fontSize: 13, fontWeight: '600' }}>✓ Approve exact deliverable</Text>
        </TouchableOpacity>
        {!rejectMode ? (
          <TouchableOpacity
            testID="reject-btn"
            style={[styles.btn, { backgroundColor: '#ef444422' }]}
            onPress={() => setRejectMode(true)}
            accessibilityLabel={`Reject content draft ${deliverable.title ?? deliverable.id}`}
          >
            <Text style={{ color: '#ef4444', fontSize: 13, fontWeight: '600' }}>✕ Reject and request revision</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {/* Reject-with-reason expansion */}
      {rejectMode && (
        <View style={{ marginTop: 10 }}>
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
          <View style={styles.rejectActions}>
            <TouchableOpacity
              testID="reject-reason-cancel"
              style={[styles.btn, { backgroundColor: '#27272a' }]}
              onPress={() => { setRejectMode(false); setRejectReason(''); }}
            >
              <Text style={{ color: colors.textSecondary, fontSize: 13 }}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID="reject-reason-confirm"
              disabled={rejectReason.trim().length === 0}
              style={[styles.btn, { backgroundColor: rejectReason.trim().length === 0 ? '#ef444411' : '#ef444422' }]}
              onPress={() => {
                if (onRejectWithReason) {
                  onRejectWithReason(deliverable.id, rejectReason.trim());
                } else {
                  onReject(deliverable.id);
                }
                setRejectMode(false);
                setRejectReason('');
              }}
            >
              <Text style={{ color: rejectReason.trim().length === 0 ? '#ef444466' : '#ef4444', fontSize: 13, fontWeight: '600' }}>
                Confirm Rejection
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    backgroundColor: '#18181b',
  },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  platformEmoji: { fontSize: 18 },
  platformLabel: { fontSize: 12 },
  title: { fontSize: 14 },
  preview: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 12,
  },
  infoCard: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 10,
    marginBottom: 10,
  },
  buttonsRow: { flexDirection: 'row', gap: 10 },
  btn: {
    flex: 1,
    borderRadius: 8,
    paddingVertical: 8,
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
  rejectActions: { flexDirection: 'row', gap: 10 },
});
