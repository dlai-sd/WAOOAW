/**
 * useTextToSpeech Hook
 * React hook for text-to-speech functionality
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  textToSpeechService,
  TextToSpeechConfig,
  Voice,
} from '../services/voice/textToSpeech.service';

export interface UseTextToSpeechResult {
  isSpeaking: boolean;
  queueLength: number;
  error: string | null;
  isAvailable: boolean;
  availableVoices: Voice[];
  speak: (text: string, config?: TextToSpeechConfig) => Promise<void>;
  queue: (text: string, config?: TextToSpeechConfig) => void;
  stop: () => Promise<void>;
  pause: () => Promise<void>;
  resume: () => Promise<void>;
  clearQueue: () => void;
}

export function useTextToSpeech(): UseTextToSpeechResult {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [queueLength, setQueueLength] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isAvailable, setIsAvailable] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<Voice[]>([]);
  const isMounted = useRef(true);
  const updateInterval = useRef<NodeJS.Timeout | null>(null);

  // Check availability and get voices on mount
  useEffect(() => {
    const initialize = async () => {
      const available = await textToSpeechService.isAvailable();
      if (isMounted.current) {
        setIsAvailable(available);
      }

      if (available) {
        const voices = await textToSpeechService.getAvailableVoices();
        if (isMounted.current) {
          setAvailableVoices(voices);
        }
      }
    };

    initialize();

    // Poll for status updates
    updateInterval.current = setInterval(() => {
      if (isMounted.current) {
        setIsSpeaking(textToSpeechService.getIsSpeaking());
        setQueueLength(textToSpeechService.getQueueLength());
      }
    }, 100);

    return () => {
      isMounted.current = false;
      if (updateInterval.current) {
        clearInterval(updateInterval.current);
      }
    };
  }, []);

  const speak = useCallback(async (text: string, config?: TextToSpeechConfig) => {
    try {
      setError(null);
      
      const wrappedConfig: TextToSpeechConfig = {
        ...config,
        onStart: () => {
          if (isMounted.current) {
            setIsSpeaking(true);
          }
          config?.onStart?.();
        },
        onDone: () => {
          if (isMounted.current) {
            setIsSpeaking(false);
          }
          config?.onDone?.();
        },
        onStopped: () => {
          if (isMounted.current) {
            setIsSpeaking(false);
          }
          config?.onStopped?.();
        },
        onError: (err) => {
          if (isMounted.current) {
            setError(err.message);
            setIsSpeaking(false);
          }
          config?.onError?.(err);
        },
      };

      await textToSpeechService.speak(text, wrappedConfig);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to speak text');
    }
  }, []);

  const queue = useCallback((text: string, config?: TextToSpeechConfig) => {
    textToSpeechService.queue(text, config);
    setQueueLength(textToSpeechService.getQueueLength());
  }, []);

  const stop = useCallback(async () => {
    try {
      await textToSpeechService.stop();
      if (isMounted.current) {
        setIsSpeaking(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop speech');
    }
  }, []);

  const pause = useCallback(async () => {
    try {
      await textToSpeechService.pause();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to pause speech');
    }
  }, []);

  const resume = useCallback(async () => {
    try {
      await textToSpeechService.resume();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resume speech');
    }
  }, []);

  const clearQueue = useCallback(() => {
    textToSpeechService.clearQueue();
    setQueueLength(0);
  }, []);

  return {
    isSpeaking,
    queueLength,
    error,
    isAvailable,
    availableVoices,
    speak,
    queue,
    stop,
    pause,
    resume,
    clearQueue,
  };
}
