/**
 * Speech-to-Text Service
 * Wrapper around @react-native-voice/voice library
 * 
 * Features:
 * - Voice recognition with continuous listening support
 * - Multi-language support (default: en-US)
 * - Error handling and retry logic
 * - Permission management
 */

// STUB: Voice removed for demo build
const Voice = {
  onSpeechStart: () => {},
  onSpeechEnd: () => {},
  onSpeechResults: () => {},
  onSpeechError: () => {},
  start: async () => {},
  stop: async () => {},
  destroy: async () => {},
  removeAllListeners: () => {},
  isAvailable: async () => false,
};

export type SpeechStartEvent = any;
export type SpeechEndEvent = any;
export type SpeechResultsEvent = { value?: string[] };
export type SpeechErrorEvent = { error?: { message?: string } };

export interface SpeechToTextConfig {
  language?: string;
  continuous?: boolean;
  maxAlternatives?: number;
  partialResults?: boolean;
}

export interface SpeechResult {
  transcript: string;
  confidence?: number;
  isFinal: boolean;
}

export type SpeechEventType = 'start' | 'end' | 'results' | 'partialResults' | 'error';

export type SpeechEventCallback = {
  start?: () => void;
  end?: () => void;
  results?: (results: SpeechResult[]) => void;
  partialResults?: (results: SpeechResult[]) => void;
  error?: (error: string) => void;
};

class SpeechToTextService {
  private isListening = false;
  private callbacks: SpeechEventCallback = {};

  constructor() {
    Voice.onSpeechStart = this.handleSpeechStart;
    Voice.onSpeechEnd = this.handleSpeechEnd;
    Voice.onSpeechResults = this.handleSpeechResults;
    Voice.onSpeechPartialResults = this.handleSpeechPartialResults;
    Voice.onSpeechError = this.handleSpeechError;
  }

  /**
   * Check if speech recognition is available on device
   */
  async isAvailable(): Promise<boolean> {
    try {
      return await Voice.isAvailable();
    } catch (error) {
      console.error('Speech recognition check failed:', error);
      return false;
    }
  }

  /**
   * Start speech recognition
   */
  async start(config: SpeechToTextConfig = {}): Promise<void> {
    try {
      if (this.isListening) {
        await this.stop();
      }

      const language = config.language || 'en-US';
      
      await Voice.start(language);
      this.isListening = true;
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      throw new Error('Failed to start speech recognition');
    }
  }

  /**
   * Stop speech recognition
   */
  async stop(): Promise<void> {
    try {
      await Voice.stop();
      this.isListening = false;
    } catch (error) {
      console.error('Failed to stop speech recognition:', error);
      throw new Error('Failed to stop speech recognition');
    }
  }

  /**
   * Cancel speech recognition
   */
  async cancel(): Promise<void> {
    try {
      await Voice.cancel();
      this.isListening = false;
    } catch (error) {
      console.error('Failed to cancel speech recognition:', error);
      throw new Error('Failed to cancel speech recognition');
    }
  }

  /**
   * Destroy speech recognition instance
   */
  async destroy(): Promise<void> {
    try {
      await Voice.destroy();
      this.isListening = false;
      Voice.removeAllListeners();
    } catch (error) {
      console.error('Failed to destroy speech recognition:', error);
    }
  }

  /**
   * Get current listening state
   */
  getIsListening(): boolean {
    return this.isListening;
  }

  /**
   * Register event callbacks
   */
  on(callbacks: SpeechEventCallback): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  /**
   * Unregister event callbacks
   */
  off(type?: SpeechEventType): void {
    if (type) {
      delete this.callbacks[type];
    } else {
      this.callbacks = {};
    }
  }

  // Private event handlers
  private handleSpeechStart = (e: SpeechStartEvent) => {
    this.callbacks.start?.();
  };

  private handleSpeechEnd = (e: SpeechEndEvent) => {
    this.isListening = false;
    this.callbacks.end?.();
  };

  private handleSpeechResults = (e: SpeechResultsEvent) => {
    if (e.value && e.value.length > 0) {
      const results: SpeechResult[] = e.value.map((transcript, index) => ({
        transcript,
        confidence: e.confidence?.[index],
        isFinal: true,
      }));
      this.callbacks.results?.(results);
    }
  };

  private handleSpeechPartialResults = (e: SpeechResultsEvent) => {
    if (e.value && e.value.length > 0) {
      const results: SpeechResult[] = e.value.map((transcript, index) => ({
        transcript,
        confidence: e.confidence?.[index],
        isFinal: false,
      }));
      this.callbacks.partialResults?.(results);
    }
  };

  private handleSpeechError = (e: SpeechErrorEvent) => {
    this.isListening = false;
    const errorMessage = e.error?.message || 'Speech recognition error';
    this.callbacks.error?.(errorMessage);
  };
}

// Export singleton instance
export const speechToTextService = new SpeechToTextService();
export default speechToTextService;
