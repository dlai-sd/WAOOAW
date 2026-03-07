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
}: ContentDraftApprovalCardProps) {
  const { colors, typography } = useTheme();

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

      {/* Action buttons */}
      <View style={styles.buttonsRow}>
        <TouchableOpacity
          style={[styles.btn, { backgroundColor: '#10b98122' }]}
          onPress={() => onApprove(deliverable.id)}
          accessibilityLabel={`Approve content draft ${deliverable.title ?? deliverable.id}`}
        >
          <Text style={{ color: '#10b981', fontSize: 13, fontWeight: '600' }}>✓ Approve</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.btn, { backgroundColor: '#ef444422' }]}
          onPress={() => onReject(deliverable.id)}
          accessibilityLabel={`Reject content draft ${deliverable.title ?? deliverable.id}`}
        >
          <Text style={{ color: '#ef4444', fontSize: 13, fontWeight: '600' }}>✕ Reject</Text>
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
  buttonsRow: { flexDirection: 'row', gap: 10 },
  btn: {
    flex: 1,
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
