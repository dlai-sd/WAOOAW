/**
 * TradePlanApprovalCard (CP-MOULD-1 E5-S2)
 *
 * Displays a trade plan deliverable requiring customer approval.
 * Shows symbol, action (BUY/SELL), price, quantity, risk rating + Approve/Reject.
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { DeliverableItem } from '@/hooks/useApprovalQueue';

interface TradePlanApprovalCardProps {
  deliverable: DeliverableItem;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

const riskColor = (rating?: string) => {
  switch (rating) {
    case 'low': return '#10b981';
    case 'medium': return '#f59e0b';
    case 'high': return '#ef4444';
    default: return '#a1a1aa';
  }
};

export function TradePlanApprovalCard({
  deliverable,
  onApprove,
  onReject,
}: TradePlanApprovalCardProps) {
  const { colors, typography } = useTheme();
  return (
    <View style={[styles.card, { borderColor: colors.textSecondary + '20' }]}>
      {/* Trade details row */}
      <View style={styles.detailsRow}>
        <Text style={[styles.symbol, { color: colors.textPrimary,
          fontFamily: typography.fontFamily.bodyBold }]}>
          {deliverable.symbol ?? '—'}
        </Text>
        <View style={[styles.actionChip,
          { backgroundColor: deliverable.action === 'BUY' ? '#10b98122' : '#ef444422' }]}>
          <Text style={{ color: deliverable.action === 'BUY' ? '#10b981' : '#ef4444',
            fontSize: 12, fontWeight: '600' }}>
            {deliverable.action ?? '—'}
          </Text>
        </View>
        {deliverable.risk_rating && (
          <View style={[styles.riskChip,
            { backgroundColor: riskColor(deliverable.risk_rating) + '22' }]}>
            <Text style={{ color: riskColor(deliverable.risk_rating),
              fontSize: 12, fontWeight: '600' }}>
              {deliverable.risk_rating.toUpperCase()} RISK
            </Text>
          </View>
        )}
      </View>

      {/* Price & Quantity */}
      <View style={styles.priceRow}>
        {deliverable.price != null && (
          <Text style={[styles.metaText, { color: colors.textSecondary }]}>
            Price: <Text style={{ color: colors.textPrimary }}>
              ₹{deliverable.price.toLocaleString('en-IN')}
            </Text>
          </Text>
        )}
        {deliverable.quantity != null && (
          <Text style={[styles.metaText, { color: colors.textSecondary, marginLeft: 16 }]}>
            Qty: <Text style={{ color: colors.textPrimary }}>{deliverable.quantity}</Text>
          </Text>
        )}
      </View>

      {/* Action buttons */}
      <View style={styles.buttonsRow}>
        <TouchableOpacity
          style={[styles.btn, { backgroundColor: '#10b98122' }]}
          onPress={() => onApprove(deliverable.id)}
          accessibilityLabel={`Approve trade ${deliverable.symbol}`}
        >
          <Text style={{ color: '#10b981', fontSize: 13, fontWeight: '600' }}>✓ Approve</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.btn, { backgroundColor: '#ef444422' }]}
          onPress={() => onReject(deliverable.id)}
          accessibilityLabel={`Reject trade ${deliverable.symbol}`}
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
  detailsRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  symbol: { fontSize: 16, marginRight: 4 },
  actionChip: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  riskChip: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  priceRow: { flexDirection: 'row', marginBottom: 12 },
  metaText: { fontSize: 13 },
  buttonsRow: { flexDirection: 'row', gap: 10 },
  btn: {
    flex: 1,
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
