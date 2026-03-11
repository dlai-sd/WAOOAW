import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

import { useTheme } from '@/hooks/useTheme';

type GoalSchemaField = {
  key: string;
  label: string;
  type: 'text' | 'number' | 'boolean' | 'enum' | 'list' | 'object';
  required?: boolean;
};

type Props = {
  title?: string;
  subtitle?: string;
  fields: GoalSchemaField[];
  values: Record<string, unknown>;
  emptyMessage?: string;
};

function hasValue(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0;
  if (value && typeof value === 'object') return Object.keys(value as Record<string, unknown>).length > 0;
  return String(value ?? '').trim().length > 0;
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(', ');
  if (value && typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return 'Structured response captured';
    }
  }
  return String(value ?? '').trim();
}

export const DigitalMarketingBriefSummaryCard = ({
  title = 'Structured brief summary',
  subtitle = 'This is the exact brief the agent will carry forward into draft creation.',
  fields,
  values,
  emptyMessage = 'Start answering the Theme Discovery prompts and the saved brief will appear here.',
}: Props) => {
  const { colors, spacing, typography } = useTheme();
  const completedRequired = fields.filter((field) => field.required && hasValue(values[field.key])).length;
  const totalRequired = fields.filter((field) => field.required).length;
  const filledFields = fields.filter((field) => hasValue(values[field.key]));

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: colors.card,
          borderColor: colors.textSecondary + '25',
          padding: spacing.md,
        },
      ]}
    >
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={[styles.title, { color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold }]}>{title}</Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary, fontFamily: typography.fontFamily.body }]}>{subtitle}</Text>
        </View>
        <View style={[styles.badge, { backgroundColor: colors.neonCyan + '18', borderColor: colors.neonCyan + '45' }]}>
          <Text style={[styles.badgeText, { color: colors.neonCyan, fontFamily: typography.fontFamily.bodyBold }]}>
            {completedRequired}/{totalRequired || fields.length} core details
          </Text>
        </View>
      </View>

      {filledFields.length === 0 ? (
        <View style={[styles.emptyState, { borderColor: colors.textSecondary + '35' }]}>
          <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body }}>{emptyMessage}</Text>
        </View>
      ) : (
        <View style={styles.fieldsList}>
          {fields.map((field) => {
            if (!hasValue(values[field.key])) return null;

            return (
              <View key={field.key} style={[styles.fieldCard, { borderColor: colors.textSecondary + '25' }]}>
                <Text style={[styles.fieldLabel, { color: colors.textSecondary, fontFamily: typography.fontFamily.bodyBold }]}>
                  {field.label}
                </Text>
                <Text style={[styles.fieldValue, { color: colors.textPrimary, fontFamily: typography.fontFamily.body }]}>
                  {formatValue(values[field.key])}
                </Text>
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderRadius: 16,
  },
  header: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  badge: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  badgeText: {
    fontSize: 11,
  },
  emptyState: {
    borderWidth: 1,
    borderStyle: 'dashed',
    borderRadius: 12,
    padding: 12,
  },
  fieldsList: {
    gap: 10,
  },
  fieldCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
  },
  fieldLabel: {
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  fieldValue: {
    fontSize: 14,
    lineHeight: 20,
  },
});

export default DigitalMarketingBriefSummaryCard;