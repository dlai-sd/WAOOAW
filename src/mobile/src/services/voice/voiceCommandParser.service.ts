/**
 * Voice Command Parser Service
 * Parses natural language voice input into structured commands
 * 
 * Supported Commands:
 * - Navigation: "go to home", "open discover", "show my agents"
 * - Search: "search for marketing agents", "find education agents"
 * - Filter: "show available agents", "filter by rating"
 * - Actions: "hire agent", "refresh", "go back", "help"
 */

import {
  VoiceCommandType,
  ParsedVoiceCommand,
  NavigateCommand,
  SearchCommand,
  FilterCommand,
  ActionCommand,
  HelpCommand,
  UnknownCommand,
  VoiceCommandPattern,
  NavigationTarget,
  ActionType,
} from '../../types/voice.types';

class VoiceCommandParser {
  private patterns: VoiceCommandPattern[] = [];

  constructor() {
    this.initializePatterns();
  }

  /**
   * Parse voice transcript into structured command
   */
  parse(transcript: string, confidence: number = 1.0): ParsedVoiceCommand {
    const normalizedTranscript = transcript.toLowerCase().trim();

    for (const pattern of this.patterns) {
      const match = normalizedTranscript.match(pattern.pattern);
      if (match) {
        const command = pattern.parser(match, transcript);
        return { ...command, confidence };
      }
    }

    // Return unknown command if no pattern matches
    return {
      type: 'unknown',
      transcript,
      confidence,
    } as UnknownCommand;
  }

  /**
   * Initialize command patterns
   */
  private initializePatterns(): void {
    // Navigation patterns
    this.addPattern(
      /(?:go to|open|show|navigate to)\s+(home|discover|my agents|profile|trial)/i,
      'navigate',
      (match, transcript) => {
        const target = this.parseNavigationTarget(match[1]);
        return {
          type: 'navigate',
          screen: target,
          transcript,
        } as NavigateCommand;
      }
    );

    // Search patterns
    this.addPattern(
      /(?:search for|find|look for)\s+(.+?)(?:\s+agents?)?$/i,
      'search',
      (match, transcript) => {
        const query = match[1].trim();
        const industry = this.parseIndustry(query);
        
        return {
          type: 'search',
          query: industry ? query.replace(industry, '').trim() : query,
          industry,
          transcript,
        } as SearchCommand;
      }
    );

    // Filter patterns
    this.addPattern(
      /(?:show|filter|display)\s+(?:only\s+)?(.+?)\s+agents?/i,
      'filter',
      (match, transcript) => {
        const filterText = match[1].trim();
        const filters: FilterCommand['filters'] = {};

        // Parse status
        if (filterText.includes('available')) {
          filters.status = 'available';
        } else if (filterText.includes('working')) {
          filters.status = 'working';
        } else if (filterText.includes('offline')) {
          filters.status = 'offline';
        }

        // Parse industry
        const industry = this.parseIndustry(filterText);
        if (industry) {
          filters.industry = industry;
        }

        // Parse rating
        const ratingMatch = filterText.match(/(\d+)\s+stars?/i);
        if (ratingMatch) {
          filters.rating = parseInt(ratingMatch[1], 10);
        }

        return {
          type: 'filter',
          filters,
          transcript,
        } as FilterCommand;
      }
    );

    // Action patterns
    this.addPattern(
      /(?:hire|start trial|begin trial|try)\s+(?:this\s+)?agent/i,
      'action',
      (match, transcript) => ({
        type: 'action',
        action: 'hire' as ActionType,
        transcript,
      } as ActionCommand)
    );

    this.addPattern(
      /(?:cancel|stop|end)\s+(?:trial|subscription)/i,
      'action',
      (match, transcript) => ({
        type: 'action',
        action: 'cancel' as ActionType,
        transcript,
      } as ActionCommand)
    );

    this.addPattern(
      /(?:refresh|reload|update)/i,
      'action',
      (match, transcript) => ({
        type: 'action',
        action: 'refresh' as ActionType,
        transcript,
      } as ActionCommand)
    );

    this.addPattern(
      /(?:go back|back|return)/i,
      'action',
      (match, transcript) => ({
        type: 'action',
        action: 'back' as ActionType,
        transcript,
      } as ActionCommand)
    );

    // Help patterns
    this.addPattern(
      /(?:help|what can (?:i|you) (?:do|say)|commands?|how to use)/i,
      'help',
      (match, transcript) => ({
        type: 'help',
        transcript,
      } as HelpCommand)
    );
  }

  /**
   * Add a command pattern
   */
  private addPattern(
    pattern: RegExp,
    type: VoiceCommandType,
    parser: (match: RegExpMatchArray, transcript: string) => ParsedVoiceCommand
  ): void {
    this.patterns.push({ pattern, type, parser });
  }

  /**
   * Parse navigation target from text
   */
  private parseNavigationTarget(text: string): NavigationTarget {
    const normalized = text.toLowerCase().replace(/\s+/g, '');

    switch (normalized) {
      case 'home':
        return 'Home';
      case 'discover':
        return 'Discover';
      case 'myagents':
        return 'MyAgents';
      case 'profile':
        return 'Profile';
      case 'trial':
        return 'TrialDashboard';
      default:
        return 'Home';
    }
  }

  /**
   * Parse industry from text
   */
  private parseIndustry(text: string): 'marketing' | 'education' | 'sales' | undefined {
    const normalized = text.toLowerCase();

    if (normalized.includes('marketing')) {
      return 'marketing';
    } else if (normalized.includes('education') || normalized.includes('learning')) {
      return 'education';
    } else if (normalized.includes('sales')) {
      return 'sales';
    }

    return undefined;
  }

  /**
   * Get list of example commands for help
   */
  getExampleCommands(): Record<VoiceCommandType, string[]> {
    return {
      navigate: [
        'Go to home',
        'Open discover',
        'Show my agents',
        'Go to profile',
        'Show trial dashboard',
      ],
      search: [
        'Search for marketing agents',
        'Find education agents',
        'Look for sales agents',
      ],
      filter: [
        'Show available agents',
        'Filter marketing agents',
        'Show 5 star agents',
        'Display working agents',
      ],
      action: [
        'Hire this agent',
        'Refresh',
        'Go back',
        'Cancel trial',
      ],
      help: [
        'Help',
        'What can I say?',
        'Show commands',
      ],
      unknown: [],
    };
  }
}

// Export singleton instance
export const voiceCommandParser = new VoiceCommandParser();
export default voiceCommandParser;
