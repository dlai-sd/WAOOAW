/**
 * Help Center Screen (MOBILE-FUNC-1 S5)
 *
 * Static FAQ list with mailto contact support link.
 */

import React from 'react';
import {
  View,
  Text,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { ProfileStackScreenProps } from '@/navigation/types';

type Props = ProfileStackScreenProps<'HelpCenter'>;

const FAQ_ITEMS = [
  {
    question: 'What is a 7-day trial?',
    answer:
      'You get full access to an AI agent for 7 days, completely free. You keep all deliverables the agent produces, even if you decide not to continue.',
  },
  {
    question: 'How do I keep my deliverables?',
    answer:
      'All work produced during your trial is automatically saved to your account. You can download or access it at any time, even after the trial ends.',
  },
  {
    question: 'What happens after the trial?',
    answer:
      'You can choose to hire the agent by subscribing to a plan, or simply walk away — no charges, no commitments.',
  },
  {
    question: 'How do I cancel my subscription?',
    answer:
      'Go to Profile → Subscription Management and tap "Cancel Subscription". Your agent remains active until the end of the billing period.',
  },
  {
    question: 'Can I have multiple agents?',
    answer:
      'Yes! You can run trials and hire agents across different industries — marketing, education, sales, and more.',
  },
  {
    question: 'How is my data used?',
    answer:
      'Your data is used only to power your agent workflows. We never sell your data. See our Privacy Policy for full details.',
  },
];

export const HelpCenterScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const [expandedIndex, setExpandedIndex] = React.useState<number | null>(null);

  const handleContactSupport = () => {
    Linking.openURL('mailto:support@waooaw.com');
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <View
        style={{
          paddingHorizontal: spacing.screenPadding.horizontal,
          paddingTop: spacing.md,
          paddingBottom: spacing.sm,
        }}
      >
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={{ marginBottom: spacing.md }}
        >
          <Text
            style={{
              color: colors.neonCyan,
              fontFamily: typography.fontFamily.body,
              fontSize: 14,
            }}
          >
            ← Back
          </Text>
        </TouchableOpacity>
        <Text
          style={{
            color: colors.textPrimary,
            fontFamily: typography.fontFamily.display,
            fontSize: 24,
            fontWeight: 'bold',
          }}
        >
          Help Center
        </Text>
        <Text
          style={{
            color: colors.textSecondary,
            fontFamily: typography.fontFamily.body,
            fontSize: 14,
            marginTop: spacing.xs,
          }}
        >
          Frequently asked questions
        </Text>
      </View>

      <ScrollView
        contentContainerStyle={{
          paddingBottom: spacing.xl,
        }}
      >
        {FAQ_ITEMS.map((item, index) => (
          <TouchableOpacity
            key={index}
            onPress={() =>
              setExpandedIndex(expandedIndex === index ? null : index)
            }
            style={{
              borderBottomWidth: 1,
              borderBottomColor: colors.border + '40',
              paddingHorizontal: spacing.screenPadding.horizontal,
              paddingVertical: spacing.md,
            }}
          >
            <View
              style={{
                flexDirection: 'row',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
              }}
            >
              <Text
                style={{
                  color: colors.textPrimary,
                  fontFamily: typography.fontFamily.bodyBold,
                  fontSize: 15,
                  flex: 1,
                  marginRight: spacing.sm,
                }}
              >
                {item.question}
              </Text>
              <Text
                style={{
                  color: colors.neonCyan,
                  fontSize: 18,
                }}
              >
                {expandedIndex === index ? '−' : '+'}
              </Text>
            </View>
            {expandedIndex === index && (
              <Text
                style={{
                  color: colors.textSecondary,
                  fontFamily: typography.fontFamily.body,
                  fontSize: 14,
                  lineHeight: 22,
                  marginTop: spacing.sm,
                }}
              >
                {item.answer}
              </Text>
            )}
          </TouchableOpacity>
        ))}

        {/* Contact support */}
        <View
          style={{
            marginHorizontal: spacing.screenPadding.horizontal,
            marginTop: spacing.xl,
            backgroundColor: colors.neonCyan + '10',
            borderRadius: spacing.md,
            padding: spacing.lg,
            borderWidth: 1,
            borderColor: colors.neonCyan + '30',
          }}
        >
          <Text
            style={{
              color: colors.textPrimary,
              fontFamily: typography.fontFamily.bodyBold,
              fontSize: 16,
              marginBottom: spacing.sm,
            }}
          >
            Still need help?
          </Text>
          <Text
            style={{
              color: colors.textSecondary,
              fontFamily: typography.fontFamily.body,
              fontSize: 14,
              marginBottom: spacing.md,
            }}
          >
            Our team typically responds within 2 hours.
          </Text>
          <TouchableOpacity
            onPress={handleContactSupport}
            style={{
              backgroundColor: colors.neonCyan,
              borderRadius: spacing.sm,
              paddingVertical: spacing.sm,
              paddingHorizontal: spacing.md,
              alignSelf: 'flex-start',
            }}
          >
            <Text
              style={{
                color: colors.black,
                fontFamily: typography.fontFamily.bodyBold,
                fontSize: 14,
              }}
            >
              Contact Support: support@waooaw.com
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};
