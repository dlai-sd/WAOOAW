/**
 * VoiceHelpModal Component
 * Modal showing all available voice commands with examples
 * 
 * Features:
 * - Categorized command list
 * - Example commands for each category
 * - Try example button for each command
 * - Search/filter commands
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  TextInput,
  SafeAreaView,
} from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { voiceCommandParser } from '../../services/voice/voiceCommandParser.service';
import { VoiceCommandType } from '../../types/voice.types';

export interface VoiceHelpModalProps {
  visible: boolean;
  onClose: () => void;
  onTryCommand?: (command: string) => void;
}

const COMMAND_DESCRIPTIONS: Record<VoiceCommandType, string> = {
  navigate: 'Navigate to different screens in the app',
  search: 'Search for agents by name, specialty, or industry',
  filter: 'Apply filters to the agent list',
  action: 'Perform actions like hiring, refreshing, or going back',
  help: 'Show this help screen',
  unknown: '',
};

export function VoiceHelpModal({
  visible,
  onClose,
  onTryCommand,
}: VoiceHelpModalProps): React.JSX.Element {
  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState('');

  const allCommands = voiceCommandParser.getExampleCommands();

  const filteredCommands = Object.entries(allCommands).reduce(
    (acc, [type, commands]) => {
      if (type === 'unknown') return acc;
      
      const filtered = commands.filter((cmd) =>
        cmd.toLowerCase().includes(searchQuery.toLowerCase())
      );

      if (filtered.length > 0) {
        acc[type as VoiceCommandType] = filtered;
      }

      return acc;
    },
    {} as Record<VoiceCommandType, string[]>
  );

  const handleTryCommand = (command: string) => {
    onTryCommand?.(command);
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
        {/* Header */}
        <View style={[styles.header, { borderBottomColor: theme.colors.border }]}>
          <View>
            <Text style={[styles.title, { color: theme.colors.textPrimary }]}> 
              Voice Commands
            </Text>
            <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
              Say any of these commands
            </Text>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={[styles.closeButtonText, { color: theme.colors.neonCyan }]}> 
              Done
            </Text>
          </TouchableOpacity>
        </View>

        {/* Search Bar */}
        <View style={[styles.searchContainer, { backgroundColor: theme.colors.card }]}>
          <Text style={[styles.searchIcon, { color: theme.colors.textSecondary }]}>
            🔍
          </Text>
          <TextInput
            style={[styles.searchInput, { color: theme.colors.textPrimary }]}
            placeholder="Search commands..."
            placeholderTextColor={theme.colors.textSecondary}
            value={searchQuery}
            onChangeText={setSearchQuery}
            autoCapitalize="none"
            autoCorrect={false}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Text style={[styles.clearButton, { color: theme.colors.textSecondary }]}>
                ✕
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Command List */}
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {Object.entries(filteredCommands).map(([type, commands]) => (
            <View key={type} style={styles.categorySection}>
              {/* Category Header */}
              <View style={styles.categoryHeader}>
                <Text style={[styles.categoryIcon, { color: theme.colors.neonCyan }]}> 
                  {getCategoryIcon(type as VoiceCommandType)}
                </Text>
                <View style={styles.categoryTitleContainer}>
                  <Text style={[styles.categoryTitle, { color: theme.colors.textPrimary }]}> 
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </Text>
                  <Text style={[styles.categoryDescription, { color: theme.colors.textSecondary }]}>
                    {COMMAND_DESCRIPTIONS[type as VoiceCommandType]}
                  </Text>
                </View>
              </View>

              {/* Command List */}
              <View style={styles.commandList}>
                {commands.map((command, index) => (
                  <View
                    key={index}
                    style={[styles.commandCard, { backgroundColor: theme.colors.card }]}
                  >
                    <Text style={[styles.commandText, { color: theme.colors.textPrimary }]}> 
                      "{command}"
                    </Text>
                    {onTryCommand && (
                      <TouchableOpacity
                        style={[styles.tryButton, { backgroundColor: theme.colors.neonCyan }]}
                        onPress={() => handleTryCommand(command)}
                      >
                        <Text style={styles.tryButtonText}>Try</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                ))}
              </View>
            </View>
          ))}

          {/* No Results */}
          {Object.keys(filteredCommands).length === 0 && (
            <View style={styles.noResults}>
              <Text style={[styles.noResultsText, { color: theme.colors.textSecondary }]}>
                No commands match "{searchQuery}"
              </Text>
            </View>
          )}

          {/* Tips Section */}
          <View style={[styles.tipsSection, { backgroundColor: theme.colors.card }]}>
            <Text style={[styles.tipsTitle, { color: theme.colors.textPrimary }]}> 
              💡 Tips
            </Text>
            <Text style={[styles.tipText, { color: theme.colors.textSecondary }]}>
              • Speak clearly and naturally
            </Text>
            <Text style={[styles.tipText, { color: theme.colors.textSecondary }]}>
              • Commands work in any order
            </Text>
            <Text style={[styles.tipText, { color: theme.colors.textSecondary }]}>
              • Tap the microphone button to start
            </Text>
            <Text style={[styles.tipText, { color: theme.colors.textSecondary }]}>
              • Tap outside the overlay to cancel
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

function getCategoryIcon(type: VoiceCommandType): string {
  switch (type) {
    case 'navigate':
      return '🧭';
    case 'search':
      return '🔍';
    case 'filter':
      return '⚙️';
    case 'action':
      return '⚡';
    case 'help':
      return '❓';
    default:
      return '💬';
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
  },
  subtitle: {
    fontSize: 14,
    marginTop: 4,
  },
  closeButton: {
    padding: 8,
  },
  closeButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 20,
    marginVertical: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
  },
  searchIcon: {
    fontSize: 18,
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
  },
  clearButton: {
    fontSize: 20,
    padding: 4,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 32,
  },
  categorySection: {
    marginBottom: 32,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  categoryIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  categoryTitleContainer: {
    flex: 1,
  },
  categoryTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 4,
  },
  categoryDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  commandList: {
    gap: 12,
  },
  commandCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
  },
  commandText: {
    flex: 1,
    fontSize: 16,
    fontStyle: 'italic',
  },
  tryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    marginLeft: 12,
  },
  tryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  noResults: {
    padding: 40,
    alignItems: 'center',
  },
  noResultsText: {
    fontSize: 16,
    textAlign: 'center',
  },
  tipsSection: {
    padding: 20,
    borderRadius: 16,
    marginTop: 16,
  },
  tipsTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  tipText: {
    fontSize: 14,
    lineHeight: 24,
  },
});
