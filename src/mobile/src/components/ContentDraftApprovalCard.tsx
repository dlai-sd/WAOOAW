/**
 * ContentDraftApprovalCard (CP-MOULD-1 E5-S2)
 *
 * Displays a content draft deliverable requiring customer approval.
 * Shows content preview (first 200 chars), target platform, Approve/Reject buttons.
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { DeliverableItem } from '@/hooks/useApprovalQueue';

interface ContentDraftApprovalCardProps {
  deliverable: DeliverableItem;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
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
  readinessLabel,
  readinessMessage,
  channelStatusLabel,
  approvalReference,
}: ContentDraftApprovalCardProps) {
  const { colors, typography } = useTheme();
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
        <TouchableOpacity
          style={[styles.btn, { backgroundColor: '#ef444422' }]}
          onPress={() => onReject(deliverable.id)}
          accessibilityLabel={`Reject content draft ${deliverable.title ?? deliverable.id}`}
        >
          <Text style={{ color: '#ef4444', fontSize: 13, fontWeight: '600' }}>✕ Reject and request revision</Text>
        </TouchableOpacity>
      </View>
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
});
