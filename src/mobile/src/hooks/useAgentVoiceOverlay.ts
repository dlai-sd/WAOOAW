/**
 * useAgentVoiceOverlay Hook (MOB-PARITY-1 E5-S1)
 *
 * Reusable voice command layer for agent screens. Accepts a command map and
 * processes speech transcripts against it. Provides TTS feedback on execution.
 */

import { useState, useEffect, useCallback } from 'react';
import { useSpeechToText } from './useSpeechToText';
import { useTextToSpeech } from './useTextToSpeech';

export type CommandMap = Record<string, (args: string) => void | Promise<void>>;

export interface UseAgentVoiceOverlayResult {
  isListening: boolean;
  toggle: () => void;
  lastCommand: string | null;
  isAvailable: boolean;
}

export function useAgentVoiceOverlay(commands: CommandMap): UseAgentVoiceOverlayResult {
  const { isListening, transcript, start, stop, isAvailable } = useSpeechToText();
  const { speak } = useTextToSpeech();
  const [lastCommand, setLastCommand] = useState<string | null>(null);

  const toggle = useCallback(() => {
    if (isListening) {
      stop();
    } else {
      start({ language: 'en-US' });
    }
  }, [isListening, start, stop]);

  useEffect(() => {
    if (!isListening && transcript) {
      const lower = transcript.toLowerCase().trim();
      const match = Object.entries(commands).find(([key]) =>
        lower.startsWith(key.toLowerCase())
      );
      if (match) {
        const [key, handler] = match;
        const args = lower.slice(key.length).trim();
        setLastCommand(key);
        Promise.resolve(handler(args)).catch(() => {});
        speak(`Done: ${key}`).catch(() => {});
      } else {
        const available = Object.keys(commands).join(', ');
        speak(`Command not recognized. Try: ${available}`).catch(() => {});
      }
    }
  }, [isListening, transcript, commands, speak]);

  return { isListening, toggle, lastCommand, isAvailable };
}
