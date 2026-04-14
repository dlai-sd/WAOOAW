/**
 * useAgentVoiceOverlay Hook Tests (MOB-PARITY-1 E5-S1)
 */

import { renderHook, act } from '@testing-library/react-native';

// ─── Mocks ────────────────────────────────────────────────────────────────────

const mockStart = jest.fn(() => Promise.resolve());
const mockStop = jest.fn(() => Promise.resolve());
let mockIsListening = false;
let mockTranscript: string | null = null;
let mockIsAvailable = true;

jest.mock('../src/hooks/useSpeechToText', () => ({
  useSpeechToText: () => ({
    isListening: mockIsListening,
    transcript: mockTranscript,
    results: [],
    error: null,
    isAvailable: mockIsAvailable,
    start: mockStart,
    stop: mockStop,
    cancel: jest.fn(),
  }),
}));

const mockSpeak = jest.fn(() => Promise.resolve());
jest.mock('../src/hooks/useTextToSpeech', () => ({
  useTextToSpeech: () => ({
    speak: mockSpeak,
    isSpeaking: false,
    stop: jest.fn(),
    isAvailable: true,
    availableVoices: [],
    queue: jest.fn(),
    pause: jest.fn(),
    resume: jest.fn(),
    clearQueue: jest.fn(),
    queueLength: 0,
    error: null,
  }),
}));

import { useAgentVoiceOverlay } from '../src/hooks/useAgentVoiceOverlay';

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('useAgentVoiceOverlay', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsListening = false;
    mockTranscript = null;
    mockIsAvailable = true;
  });

  it('calls start when toggle is called and not listening', async () => {
    mockIsListening = false;
    const { result } = renderHook(() =>
      useAgentVoiceOverlay({ approve: jest.fn(), reject: jest.fn() })
    );

    await act(async () => {
      result.current.toggle();
    });

    expect(mockStart).toHaveBeenCalledWith({ language: 'en-US' });
  });

  it('calls stop when toggle is called and is listening', async () => {
    mockIsListening = true;
    const { result } = renderHook(() =>
      useAgentVoiceOverlay({ approve: jest.fn(), reject: jest.fn() })
    );

    await act(async () => {
      result.current.toggle();
    });

    expect(mockStop).toHaveBeenCalled();
  });

  it('dispatches matching command handler when transcript matches', async () => {
    const mockApprove = jest.fn();
    const { rerender } = renderHook(
      ({ transcript, isListening }: { transcript: string | null; isListening: boolean }) => {
        mockIsListening = isListening;
        mockTranscript = transcript;
        return useAgentVoiceOverlay({ approve: mockApprove, reject: jest.fn() });
      },
      { initialProps: { transcript: null, isListening: true } }
    );

    // Simulate speech ending with transcript
    await act(async () => {
      rerender({ transcript: 'approve monthly report', isListening: false });
    });

    expect(mockApprove).toHaveBeenCalledWith('monthly report');
  });

  it('speaks error message when command not recognized', async () => {
    const { rerender } = renderHook(
      ({ transcript, isListening }: { transcript: string | null; isListening: boolean }) => {
        mockIsListening = isListening;
        mockTranscript = transcript;
        return useAgentVoiceOverlay({ approve: jest.fn() });
      },
      { initialProps: { transcript: null, isListening: true } }
    );

    await act(async () => {
      rerender({ transcript: 'unknown command xyz', isListening: false });
    });

    expect(mockSpeak).toHaveBeenCalledWith(expect.stringContaining('Command not recognized'));
  });

  it('returns isAvailable from useSpeechToText', () => {
    mockIsAvailable = false;
    const { result } = renderHook(() =>
      useAgentVoiceOverlay({ approve: jest.fn() })
    );
    expect(result.current.isAvailable).toBe(false);
  });
});
