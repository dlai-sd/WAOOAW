/**
 * Discover Screen
 * 
 * Browse and search for AI agents
 * Includes search bar, filters, agent list from API, and voice commands
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  RefreshControl,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../hooks/useTheme';
import { useAgents } from '../../hooks/useAgents';
import { AgentCard } from '../../components/AgentCard';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorView } from '../../components/ErrorView';
import { EmptyState } from '../../components/EmptyState';
import { VoiceControl } from '../../components/voice/VoiceControl';
import { VoiceHelpModal } from '../../components/voice/VoiceHelpModal';
import { usePerformanceMonitoring } from '../../hooks/usePerformanceMonitoring';
import type { Agent, AgentListParams, Industry } from '../../types/agent.types';

export const DiscoverScreen = () => {
  const { colors, spacing, typography } = useTheme();
  const navigation = useNavigation();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedIndustry, setSelectedIndustry] = React.useState<Industry | null>(null);
  const [showVoiceHelp, setShowVoiceHelp] = React.useState(false);

  // Performance monitoring
  usePerformanceMonitoring('Discover');

  // Build filter params
  const filterParams = React.useMemo<AgentListParams>(() => {
    const params: AgentListParams = {};
    if (selectedIndustry) {
      params.industry = selectedIndustry.toLowerCase() as Industry;
    }
    if (searchQuery.trim()) {
      params.q = searchQuery.trim();
    }
    return params;
  }, [selectedIndustry, searchQuery]);

  // Fetch agents with filters
  const {
    data: agents,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useAgents(filterParams);

  const onRefresh = React.useCallback(() => {
    refetch();
  }, [refetch]);

  const industries: Industry[] = ['marketing', 'education', 'sales'];

  // Voice command handlers
  const handleVoiceNavigate = React.useCallback(
    (screen: string) => {
      if (screen === 'Home') {
        navigation.navigate('Home' as never);
      } else if (screen === 'MyAgents') {
        navigation.navigate('MyAgents' as never);
      } else if (screen === 'Profile') {
        navigation.navigate('Profile' as never);
      }
    },
    [navigation]
  );

  const handleVoiceSearch = React.useCallback(
    (query: string, industry?: string) => {
      setSearchQuery(query);
      if (industry) {
        const validIndustry = industry.toLowerCase();
        if (industries.includes(validIndustry as Industry)) {
          setSelectedIndustry(validIndustry as Industry);
        }
      }
    },
    [industries]
  );

  const handleVoiceFilter = React.useCallback(
    (filters: Record<string, unknown>) => {
      if (filters.industry) {
        const industry = String(filters.industry).toLowerCase();
        if (industries.includes(industry as Industry)) {
          setSelectedIndustry(industry as Industry);
        }
      }
    },
    [industries]
  );

  const handleVoiceAction = React.useCallback(
    (action: string) => {
      if (action === 'refresh') {
        refetch();
      } else if (action === 'showHelp') {
        setShowVoiceHelp(true);
      }
    },
    [refetch]
  );

  const handleVoiceHelp = React.useCallback(() => {
    setShowVoiceHelp(true);
  }, []);

  // Loading state
  if (isLoading && !agents) {
    return <LoadingSpinner message="Loading agents..." />;
  }

  // Error state
  if (error && !agents) {
    return (
      <ErrorView
        message={error.message || 'Failed to load agents. Please try again.'}
        onRetry={refetch}
      />
    );
  }

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      {/* Header with Search and Filters */}
      <View
        style={[
          styles.header,
          {
            paddingHorizontal: spacing.screenPadding.horizontal,
            paddingVertical: spacing.screenPadding.vertical,
          },
        ]}
      >
        <Text
          style={[
            styles.title,
            {
              color: colors.textPrimary,
              fontSize: 28,
              fontFamily: typography.fontFamily.display,
              marginBottom: spacing.md,
            },
          ]}
        >
          Discover Agents
        </Text>

        {/* Search Bar */}
        <View
          style={[
            styles.searchContainer,
            {
              backgroundColor: colors.card,
              borderRadius: spacing.md,
              padding: spacing.md,
              marginBottom: spacing.md,
              flexDirection: 'row',
              alignItems: 'center',
            },
          ]}
        >
          <Text style={{ fontSize: 20, marginRight: spacing.sm }}>🔍</Text>
          <TextInput
            style={[
              styles.searchInput,
              {
                flex: 1,
                color: colors.textPrimary,
                fontSize: 16,
                fontFamily: typography.fontFamily.body,
              },
            ]}
            placeholder="Search agents by skill, industry..."
            placeholderTextColor={colors.textSecondary}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Text style={{ fontSize: 18, color: colors.textSecondary }}>✕</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Filter Chips */}
        <View style={[styles.filterContainer, { marginBottom: spacing.md }]}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={[styles.filterChips, { gap: spacing.sm }]}>
              {industries.map((industry) => (
                <TouchableOpacity
                  key={industry}
                  style={[
                    styles.filterChip,
                    {
                      backgroundColor:
                        selectedIndustry === industry
                          ? colors.neonCyan + '30'
                          : colors.card,
                      borderWidth: 1,
                      borderColor:
                        selectedIndustry === industry
                          ? colors.neonCyan
                          : 'transparent',
                      borderRadius: spacing.md,
                      paddingHorizontal: spacing.md,
                      paddingVertical: spacing.sm,
                    },
                  ]}
                  onPress={() =>
                    setSelectedIndustry(
                      selectedIndustry === industry ? null : industry
                    )
                  }
                >
                  <Text
                    style={[
                      styles.filterChipText,
                      {
                        color:
                          selectedIndustry === industry
                            ? colors.neonCyan
                            : colors.textPrimary,
                        fontSize: 14,
                        fontFamily: typography.fontFamily.bodyBold,
                        textTransform: 'capitalize',
                      },
                    ]}
                  >
                    {industry}
                  </Text>
                </TouchableOpacity>
              ))}
              <TouchableOpacity
                style={[
                  styles.filterChip,
                  {
                    backgroundColor: colors.card,
                    borderWidth: 1,
                    borderColor: colors.textSecondary + '40',
                    borderRadius: spacing.md,
                    paddingHorizontal: spacing.md,
                    paddingVertical: spacing.sm,
                  },
                ]}
              >
                <Text
                  style={[
                    styles.filterChipText,
                    {
                      color: colors.textSecondary,
                      fontSize: 14,
                      fontFamily: typography.fontFamily.bodyBold,
                    },
                  ]}
                >
                  + More Filters
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>

        {/* Results Count */}
        <View style={[styles.resultsHeader, { marginBottom: spacing.md }]}>
          <Text
            style={[
              styles.resultsCount,
              {
                color: colors.textSecondary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
              },
            ]}
          >
            {agents?.length || 0} agents found
            {selectedIndustry && ` in ${selectedIndustry}`}
            {searchQuery && ` for "${searchQuery}"`}
          </Text>
        </View>
      </View>

      {/* Agent List */}
      <FlashList
        data={agents || []}
        renderItem={({ item }: { item: Agent }) => <AgentCard agent={item} />}
        keyExtractor={(item: Agent) => item.id}
        contentContainerStyle={[
          styles.listContent,
          {
            paddingHorizontal: spacing.screenPadding.horizontal,
            paddingVertical: spacing.screenPadding.vertical,
            paddingTop: 0,
          },
        ]}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={onRefresh}
            tintColor={colors.neonCyan}
            colors={[colors.neonCyan]}
          />
        }
        ListEmptyComponent={
          <EmptyState
            icon="🔍"
            message="No agents found"
            subtitle={
              searchQuery || selectedIndustry
                ? 'Try adjusting your filters or search query'
                : 'No agents available at the moment'
            }
          />
        }
      />

      {/* Voice Control */}
      <VoiceControl
        callbacks={{
          onNavigate: handleVoiceNavigate,
          onSearch: handleVoiceSearch,
          onFilter: handleVoiceFilter,
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
  header: {},
  title: {},
  searchContainer: {},
  searchInput: {},
  filterContainer: {},
  filterChips: {
    flexDirection: 'row',
  },
  filterChip: {},
  filterChipText: {},
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  resultsCount: {},
  listContent: {
    paddingBottom: 40,
  },
});
