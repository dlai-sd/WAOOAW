/**
 * useSpeechToText Hook
 * React hook for speech recognition functionality
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  speechToTextService,
  SpeechResult,
  SpeechToTextConfig,
} from '../services/voice/speechToText.service';

export interface UseSpeechToTextResult {
  isListening: boolean;
  transcript: string | null;
  results: SpeechResult[];
  error: string | null;
  isAvailable: boolean;
  start: (config?: SpeechToTextConfig) => Promise<void>;
  stop: () => Promise<void>;
  cancel: () => Promise<void>;
}

export function useSpeechToText(): UseSpeechToTextResult {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [results, setResults] = useState<SpeechResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isAvailable, setIsAvailable] = useState(false);
  const isMounted = useRef(true);

  // Check availability on mount
  useEffect(() => {
    const checkAvailability = async () => {
      const available = await speechToTextService.isAvailable();
      if (isMounted.current) {
        setIsAvailable(available);
      }
    };

    checkAvailability();

    return () => {
      isMounted.current = false;
    };
  }, []);

  // Setup event callbacks
  useEffect(() => {
    speechToTextService.on({
      start: () => {
        if (isMounted.current) {
          setIsListening(true);
          setError(null);
        }
      },
      end: () => {
        if (isMounted.current) {
          setIsListening(false);
        }
      },
      results: (speechResults) => {
        if (isMounted.current) {
          setResults(speechResults);
          if (speechResults.length > 0) {
            setTranscript(speechResults[0].transcript);
          }
        }
      },
      partialResults: (speechResults) => {
        if (isMounted.current && speechResults.length > 0) {
          setTranscript(speechResults[0].transcript);
        }
      },
      error: (errorMessage) => {
        if (isMounted.current) {
          setError(errorMessage);
          setIsListening(false);
        }
      },
    });

    return () => {
      speechToTextService.off();
      speechToTextService.destroy();
    };
  }, []);

  const start = useCallback(async (config?: SpeechToTextConfig) => {
    try {
      setError(null);
      setTranscript(null);
      setResults([]);
      await speechToTextService.start(config);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start speech recognition');
    }
  }, []);

  const stop = useCallback(async () => {
    try {
      await speechToTextService.stop();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop speech recognition');
    }
  }, []);

  const cancel = useCallback(async () => {
    try {
      await speechToTextService.cancel();
      setTranscript(null);
      setResults([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel speech recognition');
    }
  }, []);

  return {
    isListening,
    transcript,
    results,
    error,
    isAvailable,
    start,
    stop,
    cancel,
  };
}
