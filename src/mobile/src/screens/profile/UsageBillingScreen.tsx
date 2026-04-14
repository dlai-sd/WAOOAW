/**
 * UsageBillingScreen (MOB-PARITY-1 E2-S1)
 *
 * Shows subscription summary, invoices (with download), and receipts (with view).
 * Mirrors CP Frontend UsageBilling.tsx.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { useTheme } from '../../hooks/useTheme';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorView } from '../../components/ErrorView';
import { EmptyState } from '../../components/EmptyState';
import { useBillingData } from '../../hooks/useBillingData';
import type { Invoice } from '../../services/invoices.service';
import type { Receipt } from '../../services/receipts.service';

// ─── Invoice Row ──────────────────────────────────────────────────────────────

function InvoiceRow({ invoice }: { invoice: Invoice }) {
  const { colors, spacing, typography } = useTheme();

  const statusColor =
    invoice.status === 'paid'
      ? colors.success ?? '#10b981'
      : invoice.status === 'overdue'
      ? colors.error
      : colors.warning ?? '#f59e0b';

  const handleDownload = async () => {
    const url = invoice.pdf_url ?? `${invoice.id}/html`;
    try {
      await Linking.openURL(url);
    } catch {
      // ignore
    }
  };

  return (
    <View
      testID={`invoice-row-${invoice.id}`}
      style={[
        styles.row,
        {
          backgroundColor: colors.card,
          borderRadius: spacing.sm,
          padding: spacing.md,
          marginBottom: spacing.sm,
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
        },
      ]}
    >
      <View style={{ flex: 1 }}>
        <Text style={{ color: colors.textPrimary, fontSize: 14, fontFamily: typography.fontFamily.bodyBold }}>
          {invoice.currency} {invoice.amount.toFixed(2)}
        </Text>
        <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body }}>
          {new Date(invoice.created_at).toLocaleDateString()}
        </Text>
        <View
          style={{
            backgroundColor: statusColor + '20',
            borderRadius: 4,
            paddingHorizontal: 6,
            paddingVertical: 1,
            alignSelf: 'flex-start',
            marginTop: 2,
          }}
        >
          <Text style={{ color: statusColor, fontSize: 10, fontFamily: typography.fontFamily.bodyBold, textTransform: 'capitalize' }}>
            {invoice.status}
          </Text>
        </View>
      </View>
      <TouchableOpacity
        testID={`invoice-download-${invoice.id}`}
        onPress={handleDownload}
        style={[
          styles.downloadBtn,
          {
            backgroundColor: colors.neonCyan + '20',
            borderRadius: spacing.sm,
            paddingHorizontal: spacing.md,
            paddingVertical: spacing.sm,
          },
        ]}
      >
        <Text style={{ color: colors.neonCyan, fontSize: 13, fontFamily: typography.fontFamily.bodyBold }}>
          Download
        </Text>
      </TouchableOpacity>
    </View>
  );
}

// ─── Receipt Row ──────────────────────────────────────────────────────────────

function ReceiptRow({ receipt }: { receipt: Receipt }) {
  const { colors, spacing, typography } = useTheme();

  const handleView = async () => {
    try {
      await Linking.openURL(`/cp/receipts/${receipt.id}/html`);
    } catch {
      // ignore
    }
  };

  return (
    <View
      testID={`receipt-row-${receipt.id}`}
      style={[
        styles.row,
        {
          backgroundColor: colors.card,
          borderRadius: spacing.sm,
          padding: spacing.md,
          marginBottom: spacing.sm,
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
        },
      ]}
    >
      <View style={{ flex: 1 }}>
        <Text style={{ color: colors.textPrimary, fontSize: 14, fontFamily: typography.fontFamily.bodyBold }}>
          {receipt.currency} {receipt.amount.toFixed(2)}
        </Text>
        <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body }}>
          {new Date(receipt.created_at).toLocaleDateString()}
        </Text>
        <Text style={{ color: colors.textSecondary, fontSize: 11, fontFamily: typography.fontFamily.body }}>
          Order: {receipt.order_id}
        </Text>
      </View>
      <TouchableOpacity
        testID={`receipt-view-${receipt.id}`}
        onPress={handleView}
        style={[
          styles.downloadBtn,
          {
            backgroundColor: colors.neonCyan + '20',
            borderRadius: spacing.sm,
            paddingHorizontal: spacing.md,
            paddingVertical: spacing.sm,
          },
        ]}
      >
        <Text style={{ color: colors.neonCyan, fontSize: 13, fontFamily: typography.fontFamily.bodyBold }}>
          View
        </Text>
      </TouchableOpacity>
    </View>
  );
}

// ─── UsageBillingScreen ───────────────────────────────────────────────────────

export function UsageBillingScreen() {
  const { colors, spacing, typography } = useTheme();
  const { invoices, receipts, isLoading, error, refetch } = useBillingData();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorView message="Failed to load billing data" onRetry={refetch} />;

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.black }]}
      testID="usage-billing-screen"
    >
      <ScrollView
        contentContainerStyle={{
          paddingHorizontal: spacing.screenPadding?.horizontal ?? spacing.lg,
          paddingVertical: spacing.lg,
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
          Billing & Usage
        </Text>
        <Text
          style={{
            color: colors.textPrimary,
            fontSize: 26,
            fontFamily: typography.fontFamily.display,
            marginBottom: spacing.xl,
          }}
        >
          Usage & Billing
        </Text>

        {/* Invoices Section */}
        <Text
          style={{
            color: colors.textPrimary,
            fontSize: 18,
            fontFamily: typography.fontFamily.bodyBold,
            marginBottom: spacing.md,
          }}
        >
          Invoices
        </Text>

        {invoices.length === 0 ? (
          <EmptyState message="No invoices yet" icon="🧾" />
        ) : (
          invoices.map((inv) => <InvoiceRow key={inv.id} invoice={inv} />)
        )}

        {/* Receipts Section */}
        <Text
          style={{
            color: colors.textPrimary,
            fontSize: 18,
            fontFamily: typography.fontFamily.bodyBold,
            marginTop: spacing.xl,
            marginBottom: spacing.md,
          }}
        >
          Receipts
        </Text>

        {receipts.length === 0 ? (
          <EmptyState message="No receipts yet" icon="🧾" />
        ) : (
          receipts.map((rec) => <ReceiptRow key={rec.id} receipt={rec} />)
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  row: {},
  downloadBtn: {},
});
