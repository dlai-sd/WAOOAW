import React from 'react';
import { View, Text, FlatList, ActivityIndicator, SafeAreaView } from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { useSearchAgents } from '../../hooks/useAgents';
import { AgentCard } from '../../components/AgentCard';
import type { DiscoverStackScreenProps } from '../../navigation/types';

const SearchResultsScreen: React.FC<DiscoverStackScreenProps<'SearchResults'>> = ({ route }) => {
  const { colors, spacing, typography } = useTheme();
  const { query } = route.params;
  const { data: agents, isLoading, error } = useSearchAgents(query);

  if (isLoading) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.black, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={colors.neonCyan} />
        <Text style={{ color: colors.textSecondary, marginTop: spacing.md }}>Searching for "{query}"...</Text>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.black, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ color: '#ef4444' }}>Failed to search agents. Please try again.</Text>
      </SafeAreaView>
    );
  }

  if (!agents?.length) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.black, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ color: colors.textSecondary }}>No agents found for "{query}"</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <View style={{ padding: spacing.md }}>
        <Text style={[typography.textVariants.body, { color: colors.white, marginBottom: spacing.md }]}>
          {agents.length} result{agents.length !== 1 ? 's' : ''} for "{query}"
        </Text>
      </View>
      <FlatList
        data={agents}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <AgentCard agent={item} />}
        contentContainerStyle={{ paddingHorizontal: spacing.md, paddingBottom: spacing.xl }}
      />
    </SafeAreaView>
  );
};

export default SearchResultsScreen;
