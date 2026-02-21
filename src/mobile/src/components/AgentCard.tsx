/**
 * Agent Card Component
 * 
 * Displays agent information in a card format
 * Used in agent list and search results
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { Image } from 'expo-image';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../hooks/useTheme';
import type { Agent } from '../types/agent.types';

interface AgentCardProps {
  agent: Agent;
}

/**
 * Status indicator dot component
 */
const StatusDot = ({ status }: { status: string }) => {
  const { colors } = useTheme();
  
  const getStatusColor = () => {
    switch (status) {
      case 'active':
        return '#10b981'; // green
      case 'inactive':
        return '#ef4444'; // red
      default:
        return '#f59e0b'; // yellow
    }
  };

  return (
    <View
      style={[
        styles.statusDot,
        {
          backgroundColor: getStatusColor(),
          width: 8,
          height: 8,
          borderRadius: 4,
        },
      ]}
    />
  );
};

/**
 * Rating stars component
 */
const RatingStars = ({ rating }: { rating?: number }) => {
  const { colors } = useTheme();
  
  if (!rating) {
    return (
      <Text style={[styles.ratingText, { color: colors.textSecondary }]}>
        No ratings yet
      </Text>
    );
  }

  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;
  
  return (
    <View style={styles.ratingContainer}>
      <Text style={[styles.starsText, { color: '#fbbf24' }]}>
        {'★'.repeat(fullStars)}
        {hasHalfStar ? '½' : ''}
        {'☆'.repeat(5 - fullStars - (hasHalfStar ? 1 : 0))}
      </Text>
      <Text style={[styles.ratingText, { color: colors.textSecondary }]}>
        {rating.toFixed(1)}
      </Text>
    </View>
  );
};

/**
 * Agent Card Component
 */
export const AgentCard = React.memo(({ agent }: AgentCardProps) => {
  const navigation = useNavigation();
  const { colors, spacing, typography } = useTheme();

  const handlePress = () => {
    // Navigate to AgentDetail screen
    (navigation as any).navigate('AgentDetail', { agentId: agent.id });
  };

  // Generate avatar placeholder from agent name
  const getAvatarPlaceholder = () => {
    return agent.name.charAt(0).toUpperCase();
  };

  // Format price
  const formatPrice = (price?: number) => {
    if (!price) return 'Contact for pricing';
    return `₹${price.toLocaleString('en-IN')}/month`;
  };

  // Get industry emoji
  const getIndustryEmoji = () => {
    switch (agent.industry) {
      case 'marketing':
        return '📢';
      case 'education':
        return '📚';
      case 'sales':
        return '💼';
      default:
        return '🤖';
    }
  };

  return (
    <TouchableOpacity
      activeOpacity={0.7}
      onPress={handlePress}
      style={[
        styles.card,
        {
          backgroundColor: colors.card,
          borderRadius: spacing.md,
          padding: spacing.lg,
          marginBottom: spacing.md,
          borderWidth: 1,
          borderColor: colors.textSecondary + '20',
        },
      ]}
    >
      {/* Header: Avatar, Name, Status */}
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <View
            style={[
              styles.avatar,
              {
                backgroundColor: colors.neonCyan + '20',
                width: 56,
                height: 56,
                borderRadius: 28,
                alignItems: 'center',
                justifyContent: 'center',
                borderWidth: 2,
                borderColor: colors.neonCyan + '40',
              },
            ]}
          >
            <Text
              style={[
                styles.avatarText,
                {
                  color: colors.neonCyan,
                  fontSize: 24,
                  fontFamily: typography.fontFamily.display,
                },
              ]}
            >
              {getAvatarPlaceholder()}
            </Text>
          </View>
        </View>

        <View style={[styles.info, { flex: 1, marginLeft: spacing.md }]}>
          <View style={styles.nameRow}>
            <Text
              style={[
                styles.name,
                {
                  color: colors.textPrimary,
                  fontSize: 18,
                  fontFamily: typography.fontFamily.bodyBold,
                  marginBottom: spacing.xs,
                },
              ]}
              numberOfLines={1}
            >
              {agent.name}
            </Text>
            <StatusDot status={agent.status} />
          </View>

          {agent.specialization && (
            <Text
              style={[
                styles.specialty,
                {
                  color: colors.textSecondary,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.body,
                  marginBottom: spacing.xs,
                },
              ]}
              numberOfLines={1}
            >
              {agent.specialization}
            </Text>
          )}

          {agent.description && (
            <Text
              style={[
                styles.description,
                {
                  color: colors.textSecondary,
                  fontSize: 13,
                  fontFamily: typography.fontFamily.body,
                },
              ]}
              numberOfLines={2}
            >
              {agent.description}
            </Text>
          )}
        </View>
      </View>

      {/* Meta: Rating, Industry */}
      <View
        style={[
          styles.meta,
          {
            marginTop: spacing.md,
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
          },
        ]}
      >
        <RatingStars rating={agent.rating} />
        
        <View style={styles.industryBadge}>
          <Text style={{ fontSize: 16, marginRight: 4 }}>
            {getIndustryEmoji()}
          </Text>
          <Text
            style={[
              styles.industryText,
              {
                color: colors.textSecondary,
                fontSize: 13,
                fontFamily: typography.fontFamily.body,
                textTransform: 'capitalize',
              },
            ]}
          >
            {agent.industry}
          </Text>
        </View>
      </View>

      {/* Footer: Price, Trial */}
      <View
        style={[
          styles.footer,
          {
            marginTop: spacing.md,
            paddingTop: spacing.md,
            borderTopWidth: 1,
            borderTopColor: colors.textSecondary + '20',
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
          },
        ]}
      >
        <View>
          <Text
            style={[
              styles.price,
              {
                color: colors.textPrimary,
                fontSize: 16,
                fontFamily: typography.fontFamily.bodyBold,
                marginBottom: 2,
              },
            ]}
          >
            {formatPrice(agent.price)}
          </Text>
          <Text
            style={[
              styles.trial,
              {
                color: colors.neonCyan,
                fontSize: 12,
                fontFamily: typography.fontFamily.body,
              },
            ]}
          >
            {agent.trial_days || 7}-day free trial
          </Text>
        </View>

        <View
          style={[
            styles.ctaButton,
            {
              backgroundColor: colors.neonCyan + '20',
              borderRadius: spacing.sm,
              paddingHorizontal: spacing.md,
              paddingVertical: spacing.sm,
              borderWidth: 1,
              borderColor: colors.neonCyan,
            },
          ]}
        >
          <Text
            style={[
              styles.ctaText,
              {
                color: colors.neonCyan,
                fontSize: 14,
                fontFamily: typography.fontFamily.bodyBold,
              },
            ]}
          >
            View Details
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
});

AgentCard.displayName = 'AgentCard';

const styles = StyleSheet.create({
  card: {},
  header: {
    flexDirection: 'row',
  },
  avatarContainer: {},
  avatar: {},
  avatarText: {},
  info: {},
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  name: {},
  statusDot: {},
  specialty: {},
  description: {},
  meta: {},
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  starsText: {
    fontSize: 14,
    marginRight: 6,
  },
  ratingText: {
    fontSize: 13,
  },
  industryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  industryText: {},
  footer: {},
  price: {},
  trial: {},
  ctaButton: {},
  ctaText: {},
});
