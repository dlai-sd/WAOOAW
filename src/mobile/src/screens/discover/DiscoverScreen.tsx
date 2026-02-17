/**
 * Discover Screen
 * 
 * Browse and search for AI agents
 * Includes search bar, filters, and agent list
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
import { useTheme } from '../../hooks/useTheme';

export const DiscoverScreen = () => {
  const { colors, spacing, typography } = useTheme();
  const [refreshing, setRefreshing] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState('');

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    // TODO: Fetch agents from API
    setTimeout(() => setRefreshing(false), 1000);
  }, []);

  const industries = ['Marketing', 'Education', 'Sales'];
  const [selectedIndustry, setSelectedIndustry] = React.useState<string | null>(null);

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.black }]}>
      <View style={[styles.header, { padding: spacing.screenPadding }]}>
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
            {selectedIndustry
              ? `Showing ${selectedIndustry} agents`
              : 'Showing all agents'}
          </Text>
          <TouchableOpacity>
            <Text
              style={[
                styles.sortButton,
                {
                  color: colors.neonCyan,
                  fontSize: 14,
                  fontFamily: typography.fontFamily.bodyBold,
                },
              ]}
            >
              Sort by ↓
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.content,
          { padding: spacing.screenPadding, paddingTop: 0 },
        ]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.neonCyan}
            colors={[colors.neonCyan]}
          />
        }
      >
        {/* Agent List Placeholder */}
        <View
          style={[
            styles.placeholderCard,
            {
              backgroundColor: colors.card,
              borderRadius: spacing.md,
              padding: spacing.xl,
              alignItems: 'center',
              marginBottom: spacing.md,
            },
          ]}
        >
          <Text style={{ fontSize: 64, marginBottom: spacing.md }}>🤖</Text>
          <Text
            style={[
              styles.placeholderTitle,
              {
                color: colors.textPrimary,
                fontSize: 18,
                fontFamily: typography.fontFamily.bodyBold,
                marginBottom: spacing.sm,
                textAlign: 'center',
              },
            ]}
          >
            19+ AI Agents Ready to Work
          </Text>
          <Text
            style={[
              styles.placeholderText,
              {
                color: colors.textSecondary,
                fontSize: 14,
                fontFamily: typography.fontFamily.body,
                textAlign: 'center',
                marginBottom: spacing.md,
              },
            ]}
          >
            Agent cards and details will appear here
          </Text>
          <Text
            style={[
              styles.placeholderSubtext,
              {
                color: colors.textSecondary + '80',
                fontSize: 12,
                fontFamily: typography.fontFamily.body,
                textAlign: 'center',
              },
            ]}
          >
            Coming in Story 2.2-2.3
          </Text>
        </View>

        {/* Industry Breakdown */}
        <View style={[styles.industrySection, { marginTop: spacing.lg }]}>
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
            Browse by Industry
          </Text>
          {industries.map((industry, index) => (
            <TouchableOpacity
              key={industry}
              style={[
                styles.industryCard,
                {
                  backgroundColor: colors.card,
                  borderRadius: spacing.md,
                  padding: spacing.lg,
                  marginBottom: spacing.md,
                  flexDirection: 'row',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                },
              ]}
            >
              <View style={styles.industryInfo}>
                <Text
                  style={[
                    styles.industryName,
                    {
                      color: colors.textPrimary,
                      fontSize: 18,
                      fontFamily: typography.fontFamily.bodyBold,
                      marginBottom: spacing.xs,
                    },
                  ]}
                >
                  {industry}
                </Text>
                <Text
                  style={[
                    styles.agentCount,
                    {
                      color: colors.textSecondary,
                      fontSize: 14,
                      fontFamily: typography.fontFamily.body,
                    },
                  ]}
                >
                  {index === 0 ? '7' : index === 1 ? '7' : '5'} agents available
                </Text>
              </View>
              <Text style={{ fontSize: 24, color: colors.textSecondary }}>→</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
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
  sortButton: {},
  scrollView: {
    flex: 1,
  },
  content: {
    paddingBottom: 40,
  },
  placeholderCard: {},
  placeholderTitle: {},
  placeholderText: {},
  placeholderSubtext: {},
  industrySection: {},
  sectionTitle: {},
  industryCard: {},
  industryInfo: {},
  industryName: {},
  agentCount: {},
});
