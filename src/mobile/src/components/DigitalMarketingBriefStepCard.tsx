import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Switch,
} from 'react-native';

import { useTheme } from '@/hooks/useTheme';

type GoalSchemaField = {
  key: string;
  label: string;
  type: 'text' | 'number' | 'boolean' | 'enum' | 'list' | 'object';
  required?: boolean;
  description?: string;
  options?: string[];
};

type Props = {
  title: string;
  description: string;
  prompt: string;
  fields: GoalSchemaField[];
  values: Record<string, unknown>;
  stepIndex: number;
  stepCount: number;
  canGoBack: boolean;
  canContinue: boolean;
  isSaving: boolean;
  isLastStep: boolean;
  missingFieldLabels: string[];
  onChange: (key: string, value: unknown) => void;
  onBack: () => void;
  onNext: () => void;
  onSave: () => void;
};

function inputValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(', ');
  if (value && typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return '';
    }
  }
  return String(value ?? '');
}

export const DigitalMarketingBriefStepCard = ({
  title,
  description,
  prompt,
  fields,
  values,
  stepIndex,
  stepCount,
  canGoBack,
  canContinue,
  isSaving,
  isLastStep,
  missingFieldLabels,
  onChange,
  onBack,
  onNext,
  onSave,
}: Props) => {
  const { colors, spacing, typography } = useTheme();
  const progress = stepCount > 0 ? ((stepIndex + 1) / stepCount) * 100 : 0;

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
      <View style={{ marginBottom: spacing.md }}>
        <View style={styles.progressHeader}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.kicker, { color: colors.neonCyan, fontFamily: typography.fontFamily.bodyBold }]}>
              Theme Discovery step {stepIndex + 1} of {stepCount}
            </Text>
            <Text style={[styles.title, { color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold }]}>{title}</Text>
          </View>
          <Text style={[styles.progressValue, { color: colors.textSecondary, fontFamily: typography.fontFamily.body }]}>
            {Math.round(progress)}%
          </Text>
        </View>

        <View style={[styles.progressTrack, { backgroundColor: colors.textSecondary + '20' }]}>
          <View style={[styles.progressFill, { width: `${progress}%`, backgroundColor: colors.neonCyan }]} />
        </View>

        <Text style={[styles.description, { color: colors.textSecondary, fontFamily: typography.fontFamily.body }]}>{description}</Text>
        <View style={[styles.promptCard, { backgroundColor: colors.black, borderColor: colors.textSecondary + '25' }]}>
          <Text style={[styles.promptText, { color: colors.textPrimary, fontFamily: typography.fontFamily.body }]}>{prompt}</Text>
        </View>
      </View>

      <View style={styles.fieldsList}>
        {fields.map((field) => {
          const label = `${field.label}${field.required ? ' *' : ''}`;
          const currentValue = values[field.key];

          if (field.type === 'boolean') {
            const booleanValue = Boolean(currentValue);
            return (
              <View key={field.key} style={styles.fieldBlock}>
                <View style={styles.booleanRow}>
                  <View style={{ flex: 1, paddingRight: 12 }}>
                    <Text style={[styles.fieldLabel, { color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold }]}>{label}</Text>
                    {field.description ? (
                      <Text style={[styles.fieldDescription, { color: colors.textSecondary, fontFamily: typography.fontFamily.body }]}>
                        {field.description}
                      </Text>
                    ) : null}
                  </View>
                  <Switch
                    value={booleanValue}
                    onValueChange={(next) => onChange(field.key, next)}
                    thumbColor={booleanValue ? colors.black : colors.textSecondary}
                    trackColor={{ false: colors.textSecondary + '55', true: colors.neonCyan }}
                  />
                </View>
              </View>
            );
          }

          if (field.options && field.options.length > 0) {
            return (
              <View key={field.key} style={styles.fieldBlock}>
                <Text style={[styles.fieldLabel, { color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold }]}>{label}</Text>
                {field.description ? (
                  <Text style={[styles.fieldDescription, { color: colors.textSecondary, fontFamily: typography.fontFamily.body }]}>
                    {field.description}
                  </Text>
                ) : null}
                <View style={styles.optionRow}>
                  {field.options.map((option) => {
                    const selected = String(currentValue || '') === option;
                    return (
                      <TouchableOpacity
                        key={option}
                        style={[
                          styles.optionChip,
                          {
                            backgroundColor: selected ? colors.neonCyan + '22' : colors.black,
                            borderColor: selected ? colors.neonCyan : colors.textSecondary + '35',
                          },
                        ]}
                        onPress={() => onChange(field.key, option)}
                      >
                        <Text
                          style={{
                            color: selected ? colors.neonCyan : colors.textPrimary,
                            fontFamily: typography.fontFamily.body,
                            fontSize: 13,
                          }}
                        >
                          {option}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>
            );
          }

          return (
            <View key={field.key} style={styles.fieldBlock}>
              <Text style={[styles.fieldLabel, { color: colors.textPrimary, fontFamily: typography.fontFamily.bodyBold }]}>{label}</Text>
              {field.description ? (
                <Text style={[styles.fieldDescription, { color: colors.textSecondary, fontFamily: typography.fontFamily.body }]}>
                  {field.description}
                </Text>
              ) : null}
              <TextInput
                accessibilityLabel={label}
                value={inputValue(currentValue)}
                onChangeText={(text) => onChange(field.key, text)}
                placeholder={`Add ${field.label.toLowerCase()}`}
                placeholderTextColor={colors.textSecondary}
                multiline={field.type === 'object' || field.type === 'list' || field.type === 'text'}
                style={[
                  styles.input,
                  {
                    color: colors.textPrimary,
                    borderColor: colors.textSecondary + '35',
                    backgroundColor: colors.black,
                    fontFamily: typography.fontFamily.body,
                    minHeight: field.type === 'object' || field.type === 'list' || field.type === 'text' ? 88 : 48,
                  },
                ]}
              />
            </View>
          );
        })}
      </View>

      {missingFieldLabels.length > 0 ? (
        <View style={[styles.warningCard, { backgroundColor: '#f59e0b18', borderColor: '#f59e0b55' }]}>
          <Text style={{ color: '#f59e0b', fontFamily: typography.fontFamily.body }}>
            Add the remaining details for this step before continuing: {missingFieldLabels.join(', ')}.
          </Text>
        </View>
      ) : null}

      <View style={styles.actionsRow}>
        <TouchableOpacity
          style={[styles.secondaryButton, { borderColor: colors.textSecondary + '35', opacity: canGoBack ? 1 : 0.45 }]}
          disabled={!canGoBack}
          onPress={onBack}
        >
          <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.body }}>Back</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.primaryButton, { backgroundColor: canContinue ? colors.neonCyan : colors.textSecondary + '45' }]}
          disabled={!canContinue || isSaving}
          onPress={isLastStep ? onSave : onNext}
        >
          <Text style={{ color: colors.black, fontFamily: typography.fontFamily.bodyBold }}>
            {isLastStep ? (isSaving ? 'Saving brief...' : 'Save Theme Discovery brief') : 'Continue'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderRadius: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'flex-start',
  },
  kicker: {
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
    marginBottom: 4,
  },
  title: {
    fontSize: 20,
  },
  progressValue: {
    fontSize: 12,
    marginTop: 2,
  },
  progressTrack: {
    height: 8,
    borderRadius: 999,
    overflow: 'hidden',
    marginTop: 12,
    marginBottom: 12,
  },
  progressFill: {
    height: '100%',
    borderRadius: 999,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 10,
  },
  promptCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
  },
  promptText: {
    fontSize: 14,
    lineHeight: 20,
  },
  fieldsList: {
    gap: 14,
  },
  fieldBlock: {
    gap: 6,
  },
  fieldLabel: {
    fontSize: 14,
  },
  fieldDescription: {
    fontSize: 12,
    lineHeight: 17,
  },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    textAlignVertical: 'top',
  },
  booleanRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  optionChip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  warningCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    marginTop: 14,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
  },
  secondaryButton: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  primaryButton: {
    flex: 1,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default DigitalMarketingBriefStepCard;