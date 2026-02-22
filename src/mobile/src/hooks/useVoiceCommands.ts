/**
 * useVoiceCommands Hook
 * Combined hook for full voice command interaction flow
 * Features: Speech recognition + command parsing + TTS feedback
 */

import { useState, useCallback, useEffect } from 'react';
import { useSpeechToText } from './useSpeechToText';
import { useTextToSpeech } from './useTextToSpeech';
import { voiceCommandParser } from '../services/voice/voiceCommandParser.service';
import { ParsedVoiceCommand, VoiceState } from '../types/voice.types';

export interface VoiceCommandCallbacks {
  onCommand?: (command: ParsedVoiceCommand) => void;
  onNavigate?: (screen: string) => void;
  onSearch?: (query: string, industry?: string) => void;
  onFilter?: (filters: Record<string, unknown>) => void;
  onAction?: (action: string, params?: Record<string, unknown>) => void;
  onHelp?: () => void;
  onUnknown?: (transcript: string) => void;
}

export interface UseVoiceCommandsOptions {
  enableFeedback?: boolean; // Enable TTS feedback
  language?: string; // Speech recognition language
  autoExecute?: boolean; // Auto-execute commands
}

export interface UseVoiceCommandsResult {
  state: VoiceState;
  isAvailable: boolean;
  startListening: () => Promise<void>;
  stopListening: () => Promise<void>;
  cancelListening: () => Promise<void>;
  speakFeedback: (text: string) => Promise<void>;
  getExampleCommands: () => Record<string, string[]>;
}

export function useVoiceCommands(
  callbacks: VoiceCommandCallbacks = {},
  options: UseVoiceCommandsOptions = {}
): UseVoiceCommandsResult {
  const {
    enableFeedback = true,
    language = 'en-US',
    autoExecute = true,
  } = options;

  const speechToText = useSpeechToText();
  const textToSpeech = useTextToSpeech();

  const [state, setState] = useState<VoiceState>({
    isListening: false,
    isProcessing: false,
    transcript: null,
    lastCommand: null,
    error: null,
  });

  // Update state when speech recognition changes
  useEffect(() => {
    setState((prev) => ({
      ...prev,
      isListening: speechToText.isListening,
      transcript: speechToText.transcript,
      error: speechToText.error,
    }));
  }, [speechToText.isListening, speechToText.transcript, speechToText.error]);

  // Process command when results are received
  useEffect(() => {
    if (speechToText.results.length > 0) {
      const result = speechToText.results[0];
      if (result.isFinal && result.transcript) {
        processCommand(result.transcript, result.confidence);
      }
    }
  }, [speechToText.results]);

  const processCommand = useCallback(
    async (transcript: string, confidence?: number) => {
      setState((prev) => ({ ...prev, isProcessing: true }));

      try {
        const command = voiceCommandParser.parse(transcript, confidence);
        
        setState((prev) => ({
          ...prev,
          lastCommand: command,
          isProcessing: false,
        }));

        // Provide feedback
        if (enableFeedback) {
          await provideFeedback(command);
        }

        // Execute command if auto-execute is enabled
        if (autoExecute) {
          await executeCommand(command);
        }

        // Call generic callback
        callbacks.onCommand?.(command);
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Failed to process command',
          isProcessing: false,
        }));
      }
    },
    [callbacks, enableFeedback, autoExecute]
  );

  const provideFeedback = async (command: ParsedVoiceCommand): Promise<void> => {
    let feedbackText = '';

    switch (command.type) {
      case 'navigate':
        feedbackText = `Navigating to ${command.screen}`;
        break;
      case 'search':
        feedbackText = `Searching for ${command.query}`;
        break;
      case 'filter':
        feedbackText = 'Applying filters';
        break;
      case 'action':
        feedbackText = `Executing ${command.action}`;
        break;
      case 'help':
        feedbackText = 'Opening help';
        break;
      case 'unknown':
        feedbackText = "I didn't understand that command";
        break;
    }

    if (feedbackText) {
      await textToSpeech.speak(feedbackText, { rate: 1.2 });
    }
  };

  const executeCommand = async (command: ParsedVoiceCommand): Promise<void> => {
    try {
      switch (command.type) {
        case 'navigate':
          callbacks.onNavigate?.(command.screen);
          break;
        case 'search':
          callbacks.onSearch?.(command.query, command.industry);
          break;
        case 'filter':
          callbacks.onFilter?.(command.filters);
          break;
        case 'action':
          callbacks.onAction?.(command.action, command.params);
          break;
        case 'help':
          callbacks.onHelp?.();
          break;
        case 'unknown':
          callbacks.onUnknown?.(command.transcript);
          break;
      }
    } catch (error) {
      console.error('Command execution error:', error);
    }
  };

  const startListening = useCallback(async () => {
    setState((prev) => ({ ...prev, error: null }));
    await speechToText.start({ language, partialResults: true });
  }, [language, speechToText]);

  const stopListening = useCallback(async () => {
    await speechToText.stop();
  }, [speechToText]);

  const cancelListening = useCallback(async () => {
    await speechToText.cancel();
    setState((prev) => ({
      ...prev,
      transcript: null,
      lastCommand: null,
    }));
  }, [speechToText]);

  const speakFeedback = useCallback(
    async (text: string) => {
      await textToSpeech.speak(text, { rate: 1.2 });
    },
    [textToSpeech]
  );

  const getExampleCommands = useCallback(() => {
    return voiceCommandParser.getExampleCommands();
  }, []);

  return {
    state,
    isAvailable: speechToText.isAvailable && textToSpeech.isAvailable,
    startListening,
    stopListening,
    cancelListening,
    speakFeedback,
    getExampleCommands,
  };
}
