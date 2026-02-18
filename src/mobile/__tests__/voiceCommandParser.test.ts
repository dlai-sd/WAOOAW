/**
 * Voice Services Tests
 * Tests for speech-to-text, text-to-speech, and voice command parser
 */

import { voiceCommandParser } from '../src/services/voice/voiceCommandParser.service';

describe('Voice Command Parser', () => {
  describe('Navigation Commands', () => {
    it('should parse "go to home" as navigate command', () => {
      const result = voiceCommandParser.parse('go to home');
      
      expect(result.type).toBe('navigate');
      expect(result.transcript).toBe('go to home');
      if (result.type === 'navigate') {
        expect(result.screen).toBe('Home');
      }
    });

    it('should parse "open discover" as navigate command', () => {
      const result = voiceCommandParser.parse('open discover');
      
      expect(result.type).toBe('navigate');
      if (result.type === 'navigate') {
        expect(result.screen).toBe('Discover');
      }
    });

    it('should parse "show my agents" as navigate command', () => {
      const result = voiceCommandParser.parse('show my agents');
      
      expect(result.type).toBe('navigate');
      if (result.type === 'navigate') {
        expect(result.screen).toBe('MyAgents');
      }
    });
  });

  describe('Search Commands', () => {
    it('should parse "search for marketing agents" as search command', () => {
      const result = voiceCommandParser.parse('search for marketing agents');
      
      expect(result.type).toBe('search');
      if (result.type === 'search') {
        expect(result.industry).toBe('marketing');
      }
    });

    it('should parse "find education agents" as search command', () => {
      const result = voiceCommandParser.parse('find education agents');
      
      expect(result.type).toBe('search');
      if (result.type === 'search') {
        expect(result.industry).toBe('education');
      }
    });

    it('should parse "look for sales agents" as search command', () => {
      const result = voiceCommandParser.parse('look for sales agents');
      
      expect(result.type).toBe('search');
      if (result.type === 'search') {
        expect(result.industry).toBe('sales');
      }
    });
  });

  describe('Filter Commands', () => {
    it('should parse "show available agents" as filter command', () => {
      const result = voiceCommandParser.parse('show available agents');
      
      expect(result.type).toBe('filter');
      if (result.type === 'filter') {
        expect(result.filters.status).toBe('available');
      }
    });

    it('should parse "filter marketing agents" as filter command', () => {
      const result = voiceCommandParser.parse('filter marketing agents');
      
      expect(result.type).toBe('filter');
      if (result.type === 'filter') {
        expect(result.filters.industry).toBe('marketing');
      }
    });

    it('should parse "show 5 star agents" as filter command with rating', () => {
      const result = voiceCommandParser.parse('show 5 star agents');
      
      expect(result.type).toBe('filter');
      if (result.type === 'filter') {
        expect(result.filters.rating).toBe(5);
      }
    });
  });

  describe('Action Commands', () => {
    it('should parse "hire agent" as action command', () => {
      const result = voiceCommandParser.parse('hire agent');
      
      expect(result.type).toBe('action');
      if (result.type === 'action') {
        expect(result.action).toBe('hire');
      }
    });

    it('should parse "refresh" as action command', () => {
      const result = voiceCommandParser.parse('refresh');
      
      expect(result.type).toBe('action');
      if (result.type === 'action') {
        expect(result.action).toBe('refresh');
      }
    });

    it('should parse "go back" as action command', () => {
      const result = voiceCommandParser.parse('go back');
      
      expect(result.type).toBe('action');
      if (result.type === 'action') {
        expect(result.action).toBe('back');
      }
    });

    it('should parse "cancel trial" as action command', () => {
      const result = voiceCommandParser.parse('cancel trial');
      
      expect(result.type).toBe('action');
      if (result.type === 'action') {
        expect(result.action).toBe('cancel');
      }
    });
  });

  describe('Help Commands', () => {
    it('should parse "help" as help command', () => {
      const result = voiceCommandParser.parse('help');
      
      expect(result.type).toBe('help');
    });

    it('should parse "what can I say" as help command', () => {
      const result = voiceCommandParser.parse('what can I say');
      
      expect(result.type).toBe('help');
    });

    it('should parse "show commands" as help command', () => {
      const result = voiceCommandParser.parse('show commands');
      
      expect(result.type).toBe('help');
    });
  });

  describe('Unknown Commands', () => {
    it('should parse unrecognized text as unknown command', () => {
      const result = voiceCommandParser.parse('xyz random text 123');
      
      expect(result.type).toBe('unknown');
    });

    it('should preserve original transcript for unknown commands', () => {
      const text = 'completely unrecognized xyz 98765';
      const result = voiceCommandParser.parse(text);
      
      expect(result.type).toBe('unknown');
      expect(result.transcript).toBe(text);
    });
  });

  describe('Example Commands', () => {
    it('should return example commands for all categories', () => {
      const examples = voiceCommandParser.getExampleCommands();
      
      expect(examples.navigate).toBeDefined();
      expect(examples.search).toBeDefined();
      expect(examples.filter).toBeDefined();
      expect(examples.action).toBeDefined();
      expect(examples.help).toBeDefined();
      
      expect(examples.navigate.length).toBeGreaterThan(0);
      expect(examples.search.length).toBeGreaterThan(0);
      expect(examples.filter.length).toBeGreaterThan(0);
      expect(examples.action.length).toBeGreaterThan(0);
      expect(examples.help.length).toBeGreaterThan(0);
    });
  });

  describe('Case Insensitivity', () => {
    it('should parse commands regardless of case', () => {
      const lowercase = voiceCommandParser.parse('go to home');
      const uppercase = voiceCommandParser.parse('GO TO HOME');
      const mixedcase = voiceCommandParser.parse('Go To Home');
      
      expect(lowercase.type).toBe('navigate');
      expect(uppercase.type).toBe('navigate');
      expect(mixedcase.type).toBe('navigate');
    });
  });

  describe('Confidence Scores', () => {
    it('should preserve confidence score from input', () => {
      const result = voiceCommandParser.parse('go to home', 0.95);
      
      expect(result.confidence).toBe(0.95);
    });

    it('should default confidence to 1.0 if not provided', () => {
      const result = voiceCommandParser.parse('go to home');
      
      expect(result.confidence).toBe(1.0);
    });
  });
});
