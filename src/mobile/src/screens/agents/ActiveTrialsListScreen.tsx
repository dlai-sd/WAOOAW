/**
 * Active Trials List Screen (MOBILE-FUNC-1 S4)
 *
 * Shows all hired agents currently in active trial status.
 * Uses useHiredAgents() filtered by trial_status === 'active'.
 */

import React from 'react';
import {
  View,
  Text,
  FlatList,
  SafeAreaView,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { useHiredAgents } from '@/hooks/useHiredAgents';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import type { MyAgentsStackScreenProps } from '@/navigation/types';

type Props = MyAgentsStackScreenProps<'ActiveTrialsList'>;

export const ActiveTrialsListScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const { data: agents = [], isLoading } = useHiredAgents();
  const activeTrials = agents.filter((a) => a.trial_status === 'active');

  if (isLoading) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
        <LoadingSpinner />
      </SafeAreaView>
    );
  }

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
          Active Trials
        </Text>
        <Text
          style={{
            color: colors.textSecondary,
            fontFamily: typography.fontFamily.body,
            fontSize: 14,
            marginTop: spacing.xs,
          }}
        >
          {activeTrials.length} active trial{activeTrials.length !== 1 ? 's' : ''}
        </Text>
      </View>

      <FlatList
        data={activeTrials}
        keyExtractor={(item) => item.subscription_id}
        contentContainerStyle={{
          paddingHorizontal: spacing.screenPadding.horizontal,
          paddingBottom: spacing.xl,
        }}
        ListEmptyComponent={
          <View style={{ alignItems: 'center', marginTop: spacing.xl * 2 }}>
            <Text style={{ fontSize: 48 }}>🤖</Text>
            <Text
              style={{
                color: colors.textPrimary,
                fontFamily: typography.fontFamily.bodyBold,
                fontSize: 18,
                marginTop: spacing.md,
              }}
            >
              No Active Trials
            </Text>
            <Text
              style={{
                color: colors.textSecondary,
                fontFamily: typography.fontFamily.body,
                fontSize: 14,
                marginTop: spacing.sm,
                textAlign: 'center',
              }}
            >
              Start a 7-day trial with any agent to see it here.
            </Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={{
              backgroundColor: colors.card,
              borderRadius: spacing.md,
              padding: spacing.md,
              marginTop: spacing.sm,
              borderWidth: 1,
              borderColor: colors.neonCyan + '30',
            }}
            onPress={() =>
              navigation.navigate('TrialDashboard', {
                trialId: item.subscription_id,
              })
            }
          >
            <View
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <Text
                style={{
                  color: colors.textPrimary,
                  fontFamily: typography.fontFamily.bodyBold,
                  fontSize: 16,
                  flex: 1,
                }}
              >
                {item.nickname || item.agent_id}
              </Text>
              <View
                style={{
                  backgroundColor: colors.success + '20',
                  borderRadius: spacing.xs,
                  paddingHorizontal: spacing.sm,
                  paddingVertical: 2,
                }}
              >
                <Text
                  style={{
                    color: colors.success,
                    fontFamily: typography.fontFamily.body,
                    fontSize: 12,
                  }}
                >
                  Active
                </Text>
              </View>
            </View>
            <Text
              style={{
                color: colors.neonCyan,
                fontFamily: typography.fontFamily.body,
                fontSize: 12,
                marginTop: spacing.xs,
              }}
            >
              View trial dashboard →
            </Text>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
};
