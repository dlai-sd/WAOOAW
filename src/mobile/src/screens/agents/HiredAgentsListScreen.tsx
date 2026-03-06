/**
 * Hired Agents List Screen (MOBILE-FUNC-1 S4)
 *
 * Shows all hired agents (not in trial — subscription_status active).
 * Uses useHiredAgents() filtered to exclude trial_status === 'active'.
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

type Props = MyAgentsStackScreenProps<'HiredAgentsList'>;

export const HiredAgentsListScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const { data: agents = [], isLoading } = useHiredAgents();
  // Hired agents are those no longer in active trial (subscribed)
  const hiredAgents = agents.filter((a) => a.trial_status !== 'active');

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
          Hired Agents
        </Text>
        <Text
          style={{
            color: colors.textSecondary,
            fontFamily: typography.fontFamily.body,
            fontSize: 14,
            marginTop: spacing.xs,
          }}
        >
          {hiredAgents.length} hired agent{hiredAgents.length !== 1 ? 's' : ''}
        </Text>
      </View>

      <FlatList
        data={hiredAgents}
        keyExtractor={(item) => item.subscription_id}
        contentContainerStyle={{
          paddingHorizontal: spacing.screenPadding.horizontal,
          paddingBottom: spacing.xl,
        }}
        ListEmptyComponent={
          <View style={{ alignItems: 'center', marginTop: spacing.xl * 2 }}>
            <Text style={{ fontSize: 48 }}>🤝</Text>
            <Text
              style={{
                color: colors.textPrimary,
                fontFamily: typography.fontFamily.bodyBold,
                fontSize: 18,
                marginTop: spacing.md,
              }}
            >
              No Hired Agents
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
              Convert a trial to hire your first agent.
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
              borderColor: colors.border,
            }}
            onPress={() =>
              navigation.navigate('AgentDetail', { agentId: item.agent_id })
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
                  backgroundColor: colors.neonCyan + '20',
                  borderRadius: spacing.xs,
                  paddingHorizontal: spacing.sm,
                  paddingVertical: 2,
                }}
              >
                <Text
                  style={{
                    color: colors.neonCyan,
                    fontFamily: typography.fontFamily.body,
                    fontSize: 12,
                  }}
                >
                  Hired
                </Text>
              </View>
            </View>
            <Text
              style={{
                color: colors.textSecondary,
                fontFamily: typography.fontFamily.body,
                fontSize: 12,
                marginTop: spacing.xs,
              }}
            >
              Subscription: {item.status}
            </Text>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
};
