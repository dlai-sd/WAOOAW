/**
 * Voice Command Types
 * Type definitions for voice control system
 */

export type VoiceCommandType = 
  | 'navigate'
  | 'search'
  | 'filter'
  | 'action'
  | 'help'
  | 'unknown';

export type NavigationTarget =
  | 'Home'
  | 'Discover'
  | 'MyAgents'
  | 'Profile'
  | 'TrialDashboard';

export type ActionType =
  | 'hire'
  | 'cancel'
  | 'refresh'
  | 'back'
  | 'showHelp';

export interface VoiceCommand {
  type: VoiceCommandType;
  confidence?: number;
  transcript: string;
}

export interface NavigateCommand extends VoiceCommand {
  type: 'navigate';
  screen: NavigationTarget;
}

export interface SearchCommand extends VoiceCommand {
  type: 'search';
  query: string;
  industry?: 'marketing' | 'education' | 'sales';
}

export interface FilterCommand extends VoiceCommand {
  type: 'filter';
  filters: {
    status?: 'available' | 'working' | 'offline';
    rating?: number;
    industry?: 'marketing' | 'education' | 'sales';
  };
}

export interface ActionCommand extends VoiceCommand {
  type: 'action';
  action: ActionType;
  params?: Record<string, unknown>;
}

export interface HelpCommand extends VoiceCommand {
  type: 'help';
}

export interface UnknownCommand extends VoiceCommand {
  type: 'unknown';
}

export type ParsedVoiceCommand =
  | NavigateCommand
  | SearchCommand
  | FilterCommand
  | ActionCommand
  | HelpCommand
  | UnknownCommand;

export interface VoiceCommandPattern {
  pattern: RegExp;
  type: VoiceCommandType;
  parser: (match: RegExpMatchArray, transcript: string) => ParsedVoiceCommand;
}

export interface VoiceRecognitionResult {
  value: string[];
  error?: string;
}

export interface VoiceState {
  isListening: boolean;
  isProcessing: boolean;
  transcript: string | null;
  lastCommand: ParsedVoiceCommand | null;
  error: string | null;
}
