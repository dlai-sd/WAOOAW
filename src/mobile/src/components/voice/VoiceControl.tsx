/**
 * VoiceControl Component
 * Full voice interaction UI with FAB, transcript display, and feedback
 * 
 * Features:
 * - Voice FAB with listening state
 * - Transcript overlay showing recognized text
 * - Command feedback and suggestions
 * - Error handling
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableWithoutFeedback,
  Animated,
  Dimensions,
} from 'react-native';
import { VoiceFAB } from './VoiceFAB';
import { useVoiceCommands, VoiceCommandCallbacks } from '../../hooks/useVoiceCommands';
import { useTheme } from '../../hooks/useTheme';

export interface VoiceControlProps {
  callbacks: VoiceCommandCallbacks;
  enabled?: boolean;
  fabPosition?: 'bottom-right' | 'bottom-center' | 'bottom-left';
  showTranscript?: boolean;
}

const { height } = Dimensions.get('window');

export function VoiceControl({
  callbacks,
  enabled = true,
  fabPosition = 'bottom-right',
  showTranscript = true,
}: VoiceControlProps): JSX.Element {
  const theme = useTheme();
  const voiceCommands = useVoiceCommands(callbacks, {
    enableFeedback: true,
    autoExecute: true,
  });

  const [showTranscriptModal, setShowTranscriptModal] = useState(false);
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  const handlePress = async () => {
    if (voiceCommands.state.isListening) {
      await voiceCommands.stopListening();
      hideTranscript();
    } else {
      await voiceCommands.startListening();
      if (showTranscript) {
        showTranscriptOverlay();
      }
    }
  };

  const showTranscriptOverlay = () => {
    setShowTranscriptModal(true);
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 200,
      useNativeDriver: true,
    }).start();
  };

  const hideTranscript = () => {
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: true,
    }).start(() => {
      setShowTranscriptModal(false);
    });
  };

  const handleBackdropPress = async () => {
    if (voiceCommands.state.isListening) {
      await voiceCommands.cancelListening();
    }
    hideTranscript();
  };

  if (!enabled || !voiceCommands.isAvailable) {
    return <View />;
  }

  return (
    <>
      <VoiceFAB
        isListening={voiceCommands.state.isListening}
        isProcessing={voiceCommands.state.isProcessing}
        hasError={!!voiceCommands.state.error}
        disabled={!enabled}
        onPress={handlePress}
        position={fabPosition}
      />

      {/* Transcript Overlay Modal */}
      <Modal
        visible={showTranscriptModal}
        transparent
        animationType="none"
        onRequestClose={handleBackdropPress}
      >
        <TouchableWithoutFeedback onPress={handleBackdropPress}>
          <Animated.View
            style={[
              styles.modalOverlay,
              {
                opacity: fadeAnim,
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
              },
            ]}
          >
            <TouchableWithoutFeedback>
              <View style={[styles.transcriptContainer, { backgroundColor: theme.colors.card }]}>
                {/* Listening Indicator */}
                <View style={styles.header}>
                  <View style={[styles.listeningDot, { backgroundColor: theme.colors.neonCyan }]} />
                  <Text style={[styles.headerText, { color: theme.colors.text }]}>
                    Listening...
                  </Text>
                </View>

                {/* Transcript Text */}
                <View style={styles.transcriptContent}>
                  {voiceCommands.state.transcript ? (
                    <Text style={[styles.transcriptText, { color: theme.colors.text }]}>
                      {voiceCommands.state.transcript}
                    </Text>
                  ) : (
                    <Text style={[styles.placeholderText, { color: theme.colors.textSecondary }]}>
                      Try: "Go to home" or "Search for marketing agents"
                    </Text>
                  )}
                </View>

                {/* Last Command Feedback */}
                {voiceCommands.state.lastCommand && (
                  <View style={[styles.commandFeedback, { backgroundColor: theme.colors.background }]}>
                    <Text style={[styles.commandType, { color: theme.colors.primary }]}>
                      {voiceCommands.state.lastCommand.type.toUpperCase()}
                    </Text>
                    <Text style={[styles.commandText, { color: theme.colors.textSecondary }]}>
                      {voiceCommands.state.lastCommand.transcript}
                    </Text>
                  </View>
                )}

                {/* Error Display */}
                {voiceCommands.state.error && (
                  <View style={[styles.errorContainer, { backgroundColor: theme.colors.error }]}>
                    <Text style={styles.errorText}>
                      {voiceCommands.state.error}
                    </Text>
                  </View>
                )}

                {/* Help Text */}
                <Text style={[styles.helpText, { color: theme.colors.textSecondary }]}>
                  Tap outside to cancel
                </Text>
              </View>
            </TouchableWithoutFeedback>
          </Animated.View>
        </TouchableWithoutFeedback>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  transcriptContainer: {
    width: '100%',
    maxWidth: 400,
    borderRadius: 24,
    padding: 24,
    minHeight: 200,
    shadowColor: '#00f2fe',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  listeningDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  headerText: {
    fontSize: 18,
    fontWeight: '600',
  },
  transcriptContent: {
    minHeight: 80,
    justifyContent: 'center',
    marginBottom: 16,
  },
  transcriptText: {
    fontSize: 24,
    fontWeight: '500',
    lineHeight: 32,
  },
  placeholderText: {
    fontSize: 16,
    lineHeight: 24,
    fontStyle: 'italic',
  },
  commandFeedback: {
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
  },
  commandType: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 4,
  },
  commandText: {
    fontSize: 14,
  },
  errorContainer: {
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
  },
  errorText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  helpText: {
    fontSize: 14,
    textAlign: 'center',
    marginTop: 8,
  },
});
