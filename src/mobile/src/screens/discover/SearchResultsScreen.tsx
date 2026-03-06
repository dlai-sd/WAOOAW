import React from 'react';
import { View, Text, StyleSheet, SafeAreaView } from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import type { DiscoverStackScreenProps } from '../../navigation/types';

const SearchResultsScreen: React.FC<DiscoverStackScreenProps<'SearchResults'>> = ({ route }) => {
  const { colors, spacing, typography } = useTheme();
  const { query } = route.params;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <View style={styles.container}>
        <Text style={[typography.textVariants.body, { color: colors.white }]}>Search Results</Text>
        <Text style={[typography.textVariants.body, { color: colors.gray400, marginTop: spacing.md }]}>Query: {query}</Text>
        {/* TODO: Render agent cards matching search query */}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
});

export default SearchResultsScreen;
