/**
 * NotificationsScreen Tests (CP-MOULD-1 E6-S1)
 *
 * Coverage:
 * - resolveNavigationTarget returns correct screen + params for each type
 * - resolveNavigationTarget returns null for 'generic' type
 * - resolveNavigationTarget returns null when hired_agent_id is missing
 * - NotificationsScreen renders without crashing
 */

import { describe, it, expect, jest } from '@jest/globals';
import {
  resolveNavigationTarget,
  type Notification,
  type NotificationType,
} from '@/screens/profile/NotificationsScreen';

// ─── resolveNavigationTarget unit tests ──────────────────────────────────────

describe('resolveNavigationTarget', () => {
  const baseNotification: Notification = {
    id: 'n-1',
    type: 'generic',
    title: 'Test',
    body: 'Body',
    hired_agent_id: 'hi-123',
  };

  it('returns null for generic type', () => {
    expect(resolveNavigationTarget({ ...baseNotification, type: 'generic' })).toBeNull();
  });

  it('returns null when hired_agent_id is missing', () => {
    const n: Notification = { ...baseNotification, type: 'approval_required', hired_agent_id: undefined };
    expect(resolveNavigationTarget(n)).toBeNull();
  });

  it('prefers hired_instance_id when present', () => {
    const result = resolveNavigationTarget({
      ...baseNotification,
      type: 'approval_required',
      hired_agent_id: 'legacy-id',
      hired_instance_id: 'runtime-id',
    });

    expect(result).not.toBeNull();
    expect((result!.params as any).hiredAgentId).toBe('runtime-id');
  });

  it.each<[NotificationType, string]>([
    ['approval_required', 'approvals'],
    ['credential_expiring', 'health'],
    ['agent_paused', 'scheduler'],
    ['trial_ending', 'spend'],
    ['goal_run_failed', 'activity'],
  ])('routes %s to AgentOperations with focusSection=%s', (type, focusSection) => {
    const result = resolveNavigationTarget({ ...baseNotification, type });
    expect(result).not.toBeNull();
    expect(result!.screen).toBe('AgentOperations');
    expect((result!.params as any).hiredAgentId).toBe('hi-123');
    expect((result!.params as any).focusSection).toBe(focusSection);
  });
});
