import React, { useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView, TextInput } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { useTheme } from '../../hooks/useTheme';
import type { DiscoverStackScreenProps } from '../../navigation/types';

const industries = ['Marketing', 'Education', 'Sales'];

const FilterAgentsScreen: React.FC<DiscoverStackScreenProps<'FilterAgents'>> = ({ route }) => {
  const { colors, spacing, typography } = useTheme();
  const [selectedIndustry, setSelectedIndustry] = useState(route.params?.industry || '');
  const [minRating, setMinRating] = useState(route.params?.minRating || 0);
  const [maxPrice, setMaxPrice] = useState(route.params?.maxPrice || 20000);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <View style={styles.container}>
        <Text style={[typography.textVariants.body, { color: colors.white }]}>Filter Agents</Text>
        <Text style={[typography.textVariants.body, { color: colors.gray400, marginTop: spacing.md }]}>Industry</Text>
        {/* Picker for industry */}
        <Picker
          selectedValue={selectedIndustry}
          style={{ color: colors.white }}
          onValueChange={(itemValue: string) => setSelectedIndustry(itemValue)}
        >
          {industries.map((ind) => (
            <Picker.Item key={ind} label={ind} value={ind} />
          ))}
        </Picker>
        <Text style={[typography.textVariants.body, { color: colors.gray400, marginTop: spacing.md }]}>Min Rating</Text>
        <TextInput
          style={styles.input}
          keyboardType="numeric"
          value={minRating.toString()}
          onChangeText={(val) => setMinRating(Number(val))}
        />
        <Text style={[typography.textVariants.body, { color: colors.gray400, marginTop: spacing.md }]}>Max Price</Text>
        <TextInput
          style={styles.input}
          keyboardType="numeric"
          value={maxPrice.toString()}
          onChangeText={(val) => setMaxPrice(Number(val))}
        />
        {/* TODO: Add filter action button */}
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
  input: {
    width: 120,
    height: 40,
    backgroundColor: '#18181b',
    color: '#fff',
    borderRadius: 8,
    marginTop: 8,
    marginBottom: 8,
    paddingHorizontal: 12,
    fontSize: 16,
  },
});

export default FilterAgentsScreen;
