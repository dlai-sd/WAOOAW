/**
 * Text-to-Speech Service
 * Wrapper around expo-speech library
 * 
 * Features:
 * - Text-to-speech with customizable voice parameters
 * - Multi-language support
 * - Queue management for multiple messages
 * - Playback control (pause, resume, stop)
 */

import * as Speech from 'expo-speech';

export interface TextToSpeechConfig {
  language?: string;
  pitch?: number; // 0.5 to 2.0
  rate?: number; // 0.5 to 2.0 (speed)
  voice?: string;
  volume?: number; // 0.0 to 1.0
  onStart?: () => void;
  onDone?: () => void;
  onStopped?: () => void;
  onError?: (error: Error) => void;
}

export interface Voice {
  identifier: string;
  name: string;
  quality: string;
  language: string;
}

class TextToSpeechService {
  private isSpeaking = false;
  private speechQueue: Array<{ text: string; config: TextToSpeechConfig }> = [];
  private isProcessingQueue = false;

  /**
   * Speak text with optional configuration
   */
  async speak(text: string, config: TextToSpeechConfig = {}): Promise<void> {
    try {
      const options: Speech.SpeechOptions = {
        language: config.language || 'en-US',
        pitch: config.pitch ?? 1.0,
        rate: config.rate ?? 1.0,
        voice: config.voice,
        volume: config.volume ?? 1.0,
        onStart: () => {
          this.isSpeaking = true;
          config.onStart?.();
        },
        onDone: () => {
          this.isSpeaking = false;
          config.onDone?.();
          this.processQueue(); // Process next item in queue
        },
        onStopped: () => {
          this.isSpeaking = false;
          config.onStopped?.();
        },
        onError: (error) => {
          this.isSpeaking = false;
          config.onError?.(new Error(String(error)));
        },
      };

      Speech.speak(text, options);
    } catch (error) {
      console.error('Text-to-speech error:', error);
      throw new Error('Failed to speak text');
    }
  }

  /**
   * Add text to speech queue
   */
  queue(text: string, config: TextToSpeechConfig = {}): void {
    this.speechQueue.push({ text, config });
    
    if (!this.isProcessingQueue) {
      this.processQueue();
    }
  }

  /**
   * Process speech queue
   */
  private async processQueue(): Promise<void> {
    if (this.speechQueue.length === 0) {
      this.isProcessingQueue = false;
      return;
    }

    this.isProcessingQueue = true;
    const item = this.speechQueue.shift();

    if (item) {
      await this.speak(item.text, item.config);
    }
  }

  /**
   * Stop current speech
   */
  async stop(): Promise<void> {
    try {
      await Speech.stop();
      this.isSpeaking = false;
    } catch (error) {
      console.error('Failed to stop speech:', error);
      throw new Error('Failed to stop speech');
    }
  }

  /**
   * Pause current speech (iOS only)
   */
  async pause(): Promise<void> {
    try {
      await Speech.pause();
    } catch (error) {
      console.error('Failed to pause speech:', error);
      throw new Error('Failed to pause speech');
    }
  }

  /**
   * Resume paused speech (iOS only)
   */
  async resume(): Promise<void> {
    try {
      await Speech.resume();
    } catch (error) {
      console.error('Failed to resume speech:', error);
      throw new Error('Failed to resume speech');
    }
  }

  /**
   * Get available voices
   */
  async getAvailableVoices(): Promise<Voice[]> {
    try {
      const voices = await Speech.getAvailableVoicesAsync();
      return voices.map((voice) => ({
        identifier: voice.identifier,
        name: voice.name,
        quality: voice.quality,
        language: voice.language,
      }));
    } catch (error) {
      console.error('Failed to get available voices:', error);
      return [];
    }
  }

  /**
   * Check if currently speaking
   */
  getIsSpeaking(): boolean {
    return this.isSpeaking;
  }

  /**
   * Clear speech queue
   */
  clearQueue(): void {
    this.speechQueue = [];
    this.isProcessingQueue = false;
  }

  /**
   * Get queue length
   */
  getQueueLength(): number {
    return this.speechQueue.length;
  }

  /**
   * Check if speech is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const voices = await this.getAvailableVoices();
      return voices.length > 0;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const textToSpeechService = new TextToSpeechService();
export default textToSpeechService;
