/**
 * Agent Detail Screen
 * 
 * Full agent information display with sections:
 * - Hero (avatar, name, specialty, rating)
 * - About (description)
 * - Specializations (skills)
 * - Pricing (price + trial info)
 * - CTA button (Start Trial - fixed bottom)
 * - Voice commands for hiring
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { useTheme } from '../../hooks/useTheme';
import { useAgentDetail } from '../../hooks/useAgentDetail';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorView } from '../../components/ErrorView';
import { VoiceControl } from '../../components/voice/VoiceControl';
import { VoiceHelpModal } from '../../components/voice/VoiceHelpModal';
import { usePerformanceMonitoring } from '../../hooks/usePerformanceMonitoring';

// Navigation types (will be properly defined in navigation)
type AgentDetailParams = {
  agentId: string;
};

type AgentDetailRouteProp = RouteProp<{ AgentDetail: AgentDetailParams }, 'AgentDetail'>;

/**
 * Rating Stars Component (reused from AgentCard)
 */
const RatingStars = ({
  rating,
  reviewCount,
}: {
  rating?: number;
  reviewCount?: number;
}) => {
  const { colors, spacing, typography } = useTheme();

  if (!rating) {
    return (
      <Text style={{ color: colors.textSecondary, fontSize: 14 }}>
No ratings yet
      </Text>
    );
  }

  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;

  return (
    <View style={styles.ratingContainer}>
      <Text style={{ color: '#fbbf24', fontSize: 20, marginRight: 8 }}>
        {'★'.repeat(fullStars)}
        {hasHalfStar ? '½' : ''}
        {'☆'.repeat(5 - fullStars - (hasHalfStar ? 1 : 0))}
      </Text>
      <Text style={{ color: colors.textPrimary, fontSize: 16 }}>
        {rating.toFixed(1)}
      </Text>
      {reviewCount !== undefined && reviewCount > 0 && (
        <Text style={{ color: colors.textSecondary, fontSize: 14, marginLeft: 8 }}>
          ({reviewCount} {reviewCount === 1 ? 'review' : 'reviews'})
        </Text>
      )}
    </View>
  );
};

/**
 * Section Component
 */
const Section = ({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) => {
  const { colors, spacing, typography } = useTheme();

  return (
    <View style={[styles.section, { marginBottom: spacing.lg }]}>
      <Text
        style={[
          styles.sectionTitle,
          {
            color: colors.textPrimary,
            fontSize: 20,
            fontFamily: typography.fontFamily.bodyBold,
            marginBottom: spacing.md,
          },
        ]}
      >
        {title}
      </Text>
      {children}
    </View>
  );
};

/**
 * Agent Detail Screen Component
 */
export const AgentDetailScreen = () => {
  const route = useRoute<AgentDetailRouteProp>();
  const navigation = useNavigation();
  const { colors, spacing, typography } = useTheme();
  const { agentId } = route.params;
  const [showVoiceHelp, setShowVoiceHelp] = React.useState(false);

  const navigateToMainTab = React.useCallback(
    (
      tabName: 'HomeTab' | 'DiscoverTab' | 'MyAgentsTab' | 'ProfileTab',
      screen: 'Home' | 'Discover' | 'HireWizard' | 'MyAgents' | 'Profile',
      params?: Record<string, unknown>
    ) => {
      const parentNavigation = navigation.getParent() as any;
      parentNavigation?.navigate(tabName, { screen, params });
    },
    [navigation]
  );

  // Performance monitoring
  usePerformanceMonitoring('AgentDetail');

  const {
    data: agent,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useAgentDetail(agentId);

  const onRefresh = React.useCallback(() => {
    refetch();
  }, [refetch]);

  // Handle start trial
  const handleStartTrial = React.useCallback(() => {
    navigateToMainTab('DiscoverTab', 'HireWizard', { agentId: agent?.id ?? agentId });
  }, [navigateToMainTab, agent?.id, agentId]);

  // Voice command handlers
  const handleVoiceNavigate = React.useCallback(
    (screen: string) => {
      if (screen === 'Home') {
        navigateToMainTab('HomeTab', 'Home');
      } else if (screen === 'Discover') {
        navigateToMainTab('DiscoverTab', 'Discover');
      } else if (screen === 'MyAgents') {
        navigateToMainTab('MyAgentsTab', 'MyAgents');
      } else if (screen === 'Profile') {
        navigateToMainTab('ProfileTab', 'Profile');
      }
    },
    [navigateToMainTab]
  );

  const handleVoiceAction = React.useCallback(
    (action: string) => {
      if (action === 'hire') {
        handleStartTrial();
      } else if (action === 'refresh') {
        refetch();
      } else if (action === 'back') {
        navigation.goBack();
      } else if (action === 'showHelp') {
        setShowVoiceHelp(true);
      }
    },
    [handleStartTrial, refetch, navigation]
  );

  const handleVoiceHelp = React.useCallback(() => {
    setShowVoiceHelp(true);
  }, []);

  // Loading state
  if (isLoading && !agent) {
    return <LoadingSpinner message="Loading agent details..." />;
  }

  // Error state
  if (error && !agent) {
    return (
      <ErrorView
        message={error.message || 'Failed to load agent details'}
        onRetry={refetch}
      />
    );
  }

  // No agent found
  if (!agent) {
    return <ErrorView message="Agent not found" onRetry={refetch} />;
  }

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

  // Format price
  const formatPrice = (price?: number) => {
    if (!price) return 'Contact for pricing';
    return `₹${price.toLocaleString('en-IN')}`;
  };

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={{ paddingBottom: 100 }}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={onRefresh}
            tintColor={colors.neonCyan}
            colors={[colors.neonCyan]}
          />
        }
      >
        {/* Hero Section */}
        <View
          style={[
            styles.hero,
            {
              paddingHorizontal: spacing.screenPadding.horizontal,
              paddingVertical: spacing.screenPadding.vertical,
              alignItems: 'center',
              paddingTop: spacing.xl,
              paddingBottom: spacing.xl,
            },
          ]}
        >
          {/* Avatar */}
          <View
            style={[
              styles.avatar,
              {
                backgroundColor: colors.neonCyan + '20',
                width: 100,
                height: 100,
                borderRadius: 50,
                alignItems: 'center',
                justifyContent: 'center',
                borderWidth: 3,
                borderColor: colors.neonCyan + '40',
                marginBottom: spacing.lg,
              },
            ]}
          >
            <Text
              style={{
                color: colors.neonCyan,
                fontSize: 40,
                fontFamily: typography.fontFamily.display,
              }}
            >
              {agent.name.charAt(0).toUpperCase()}
            </Text>
          </View>

          {/* Name */}
          <Text
            style={[
              styles.name,
              {
                color: colors.textPrimary,
                fontSize: 28,
                fontFamily: typography.fontFamily.display,
                textAlign: 'center',
                marginBottom: spacing.sm,
              },
            ]}
          >
            {agent.name}
          </Text>

          {/* Specialization */}
          {agent.specialization && (
            <Text
              style={[
                styles.specialty,
                {
                  color: colors.neonCyan,
                  fontSize: 16,
                  fontFamily: typography.fontFamily.bodyBold,
                  textAlign: 'center',
                  marginBottom: spacing.sm,
                },
              ]}
            >
              {agent.specialization}
            </Text>
          )}

          {/* Industry Badge */}
          <View
            style={[
              styles.industryBadge,
              {
                flexDirection: 'row',
                alignItems: 'center',
                backgroundColor: colors.card,
                paddingHorizontal: spacing.md,
                paddingVertical: spacing.sm,
                borderRadius: spacing.sm,
                marginBottom: spacing.lg,
              },
            ]}
          >
            <Text style={{ fontSize: 18, marginRight: 6 }}>
              {getIndustryEmoji()}
            </Text>
            <Text
              style={{
                color: colors.textSecondary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
                textTransform: 'capitalize',
              }}
            >
              {agent.industry}
            </Text>
          </View>

          {/* Rating */}
          <View testID="agent-detail-rating" style={{ alignItems: 'center', marginBottom: spacing.sm }}>
            <RatingStars rating={agent.rating} reviewCount={agent.review_count} />
          </View>

          {/* Price badge */}
          <View
            testID="agent-detail-price"
            style={{
              backgroundColor: colors.card,
              paddingHorizontal: spacing.md,
              paddingVertical: spacing.sm,
              borderRadius: spacing.sm,
              marginBottom: spacing.sm,
              alignItems: 'center',
            }}
          >
            <Text style={{ color: colors.neonCyan, fontSize: 14, fontFamily: typography.fontFamily.bodyBold }}>
              {agent.price ? `₹${agent.price.toLocaleString('en-IN')}/mo` : 'Free trial'}
            </Text>
          </View>

          {/* Deliverables count */}
          <Text
            testID="agent-detail-deliverables-count"
            style={{ color: colors.textSecondary, fontSize: 13, fontFamily: typography.fontFamily.body, marginBottom: spacing.md }}
          >
            {(agent.total_deliverables ?? 0)} deliverables produced
          </Text>
        </View>

        {/* Content Sections */}
        <View
          style={{
            paddingHorizontal: spacing.screenPadding.horizontal,
            paddingVertical: spacing.screenPadding.vertical,
          }}
        >
          {/* About Section */}
          {agent.description && (
            <Section title="About">
              <Text
                style={{
                  color: colors.textSecondary,
                  fontSize: 15,
                  fontFamily: typography.fontFamily.body,
                  lineHeight: 24,
                }}
              >
                {agent.description}
              </Text>
            </Section>
          )}

          {/* Specializations Section */}
          {agent.job_role && (
            <Section title="Role & Seniority">
              <View
                style={[
                  styles.roleCard,
                  {
                    backgroundColor: colors.card,
                    padding: spacing.md,
                    borderRadius: spacing.md,
                  },
                ]}
              >
                <Text
                  style={{
                    color: colors.textPrimary,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                    marginBottom: spacing.xs,
                  }}
                >
                  {agent.job_role.name}
                </Text>
                {agent.job_role.description && (
                  <Text
                    style={{
                      color: colors.textSecondary,
                      fontSize: 14,
                      fontFamily: typography.fontFamily.body,
                    }}
                  >
                    {agent.job_role.description}
                  </Text>
                )}
                {agent.job_role.seniority_level && (
                  <View
                    style={{
                      marginTop: spacing.sm,
                      flexDirection: 'row',
                      alignItems: 'center',
                    }}
                  >
                    <Text
                      style={{
                        color: colors.textSecondary,
                        fontSize: 13,
                        fontFamily: typography.fontFamily.body,
                        marginRight: 6,
                      }}
                    >
                      Seniority:
                    </Text>
                    <Text
                      style={{
                        color: colors.neonCyan,
                        fontSize: 13,
                        fontFamily: typography.fontFamily.bodyBold,
                        textTransform: 'capitalize',
                      }}
                    >
                      {agent.job_role.seniority_level}
                    </Text>
                  </View>
                )}
              </View>
            </Section>
          )}

          {/* Pricing Section */}
          <Section title="Pricing">
            <View
              style={[
                styles.pricingCard,
                {
                  backgroundColor: colors.card,
                  padding: spacing.lg,
                  borderRadius: spacing.md,
                  borderWidth: 1,
                  borderColor: colors.neonCyan + '40',
                },
              ]}
            >
              <View style={styles.priceRow}>
                <View>
                  <Text
                    style={{
                      color: colors.textSecondary,
                      fontSize: 14,
                      fontFamily: typography.fontFamily.body,
                      marginBottom: spacing.xs,
                    }}
                  >
                    Monthly Rate
                  </Text>
                  <Text
                    style={{
                      color: colors.textPrimary,
                      fontSize: 32,
                      fontFamily: typography.fontFamily.display,
                    }}
                  >
                    {formatPrice(agent.price)}
                  </Text>
                  <Text
                    style={{
                      color: colors.textSecondary,
                      fontSize: 14,
                      fontFamily: typography.fontFamily.body,
                    }}
                  >
                    per month
                  </Text>
                </View>
              </View>

              <View
                style={[
                  styles.trialBadge,
                  {
                    backgroundColor: colors.neonCyan + '20',
                    padding: spacing.md,
                    borderRadius: spacing.sm,
                    marginTop: spacing.md,
                    alignItems: 'center',
                  },
                ]}
              >
                <Text style={{ fontSize: 24, marginBottom: spacing.xs }}>🎁</Text>
                <Text
                  style={{
                    color: colors.neonCyan,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                    textAlign: 'center',
                  }}
                >
                  {agent.trial_days || 7}-Day Free Trial
                </Text>
                <Text
                  style={{
                    color: colors.textSecondary,
                    fontSize: 13,
                    fontFamily: typography.fontFamily.body,
                    textAlign: 'center',
                    marginTop: spacing.xs,
                  }}
                >
                  Try risk-free. Keep all deliverables even if you don't hire.
                </Text>
              </View>
            </View>
          </Section>

          {/* Status & Availability */}
          <Section title="Availability">
            <View
              style={[
                styles.statusCard,
                {
                  backgroundColor: colors.card,
                  padding: spacing.md,
                  borderRadius: spacing.md,
                  flexDirection: 'row',
                  alignItems: 'center',
                },
              ]}
            >
              <View
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 6,
                  backgroundColor:
                    agent.status === 'active' ? '#10b981' : '#ef4444',
                  marginRight: spacing.md,
                }}
              />
              <View>
                <Text
                  style={{
                    color: colors.textPrimary,
                    fontSize: 16,
                    fontFamily: typography.fontFamily.bodyBold,
                    marginBottom: 2,
                    textTransform: 'capitalize',
                  }}
                >
                  {agent.status === 'active' ? 'Available Now' : 'Currently Unavailable'}
                </Text>
                <Text
                  style={{
                    color: colors.textSecondary,
                    fontSize: 13,
                    fontFamily: typography.fontFamily.body,
                  }}
                >
                  {agent.status === 'active'
                    ? 'Ready to start your 7-day trial'
                    : 'Check back later for availability'}
                </Text>
              </View>
            </View>
          </Section>
        </View>
      </ScrollView>

      {/* Fixed CTA Button */}
      {agent.status === 'active' && (
        <View
          style={[
            styles.ctaContainer,
            {
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              backgroundColor: colors.black,
              paddingHorizontal: spacing.screenPadding.horizontal,
              paddingVertical: spacing.screenPadding.vertical,
              borderTopWidth: 1,
              borderTopColor: colors.textSecondary + '20',
            },
          ]}
        >
          <TouchableOpacity
            testID="agent-detail-cta"
            activeOpacity={0.8}
            onPress={handleStartTrial}
            style={[
              styles.ctaButton,
              {
                backgroundColor: colors.neonCyan,
                borderRadius: spacing.sm,
                paddingVertical: spacing.md,
                alignItems: 'center',
              },
            ]}
          >
            <Text
              style={{
                color: colors.black,
                fontSize: 18,
                fontFamily: typography.fontFamily.bodyBold,
              }}
            >
              Start 7-Day Free Trial
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Voice Control */}
      <VoiceControl
        callbacks={{
          onNavigate: handleVoiceNavigate,
          onAction: handleVoiceAction,
          onHelp: handleVoiceHelp,
        }}
      />

      {/* Voice Help Modal */}
      <VoiceHelpModal
        visible={showVoiceHelp}
        onClose={() => setShowVoiceHelp(false)}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  hero: {},
  avatar: {},
  name: {},
  specialty: {},
  industryBadge: {},
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  section: {},
  sectionTitle: {},
  roleCard: {},
  pricingCard: {},
  priceRow: {},
  trialBadge: {},
  statusCard: {},
  ctaContainer: {},
  ctaButton: {},
});
