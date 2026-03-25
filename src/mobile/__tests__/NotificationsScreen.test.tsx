/**
 * NotificationsScreen Tests (MOBILE-COMP-1 E2-S1)
 *
 * Coverage:
 * - resolveNavigationTarget returns correct screen + params for approval and deliverable events
 * - resolveNavigationTarget returns null for 'generic' type
 * - resolveNavigationTarget returns null when hired_agent_id is missing
 * - deriveActionableNotifications produces correct live notifications from hired-agent data
 * - No hard-coded demo notification IDs remain in the rendered path
 */

import { describe, it, expect, jest } from '@jest/globals';
import {
  resolveNavigationTarget,
  deriveActionableNotifications,
  type Notification,
  type NotificationType,
} from '@/screens/profile/NotificationsScreen';
import type { MyAgentInstanceSummary } from '@/types/hiredAgents.types';

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
    ['deliverable_approved', 'recent'],
    ['deliverable_rejected', 'activity'],
    ['publish_ready', 'recent'],
    ['publish_blocked', 'health'],
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

  it('keeps approval and deliverable outcome routes aligned to different runtime surfaces', () => {
    const approvalResult = resolveNavigationTarget({
      ...baseNotification,
      type: 'approval_required',
    });
    const approvedDeliverableResult = resolveNavigationTarget({
      ...baseNotification,
      type: 'deliverable_approved',
    });

    expect((approvalResult!.params as any).focusSection).toBe('approvals');
    expect((approvedDeliverableResult!.params as any).focusSection).toBe('recent');
  });

  it('keeps publish-ready and publish-blocked routes on different runtime surfaces', () => {
    const readyResult = resolveNavigationTarget({
      ...baseNotification,
      type: 'publish_ready',
    });
    const blockedResult = resolveNavigationTarget({
      ...baseNotification,
      type: 'publish_blocked',
    });

    expect((readyResult!.params as any).focusSection).toBe('recent');
    expect((blockedResult!.params as any).focusSection).toBe('health');
  });
});

// ─── deriveActionableNotifications unit tests ─────────────────────────────────

describe('deriveActionableNotifications (MOBILE-COMP-1 E2-S1)', () => {
  const baseAgent: MyAgentInstanceSummary = {
    subscription_id: 'sub-1',
    agent_id: 'agent-1',
    duration: 'monthly',
    status: 'active',
    current_period_start: '2026-03-01T00:00:00Z',
    current_period_end: '2026-04-01T00:00:00Z',
    cancel_at_period_end: false,
    hired_instance_id: 'hi-1',
    configured: true,
    goals_completed: true,
    trial_status: null,
  };

  it('returns empty array when no agents', () => {
    expect(deriveActionableNotifications([])).toEqual([]);
  });

  it('produces a setup-incomplete notification when configured is false', () => {
    const notifications = deriveActionableNotifications([
      { ...baseAgent, configured: false },
    ]);
    expect(notifications).toHaveLength(1);
    expect(notifications[0].type).toBe('approval_required');
    expect(notifications[0].title).toMatch(/setup incomplete/i);
    expect(notifications[0].hired_instance_id).toBe('hi-1');
  });

  it('produces a setup-incomplete notification when goals_completed is false', () => {
    const notifications = deriveActionableNotifications([
      { ...baseAgent, goals_completed: false },
    ]);
    expect(notifications).toHaveLength(1);
    expect(notifications[0].type).toBe('approval_required');
  });

  it('produces a trial-ending notification when trial ends within 3 days', () => {
    const soonDate = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString();
    const notifications = deriveActionableNotifications([
      { ...baseAgent, trial_status: 'active', trial_end_at: soonDate },
    ]);
    const trialNotif = notifications.find((n) => n.type === 'trial_ending');
    expect(trialNotif).toBeTruthy();
    expect(trialNotif!.title).toMatch(/trial ending soon/i);
  });

  it('does NOT produce a trial-ending notification when trial ends in more than 3 days', () => {
    const farDate = new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString();
    const notifications = deriveActionableNotifications([
      { ...baseAgent, trial_status: 'active', trial_end_at: farDate },
    ]);
    const trialNotif = notifications.find((n) => n.type === 'trial_ending');
    expect(trialNotif).toBeUndefined();
  });

  it('produces a billing notification when subscription is past_due', () => {
    const notifications = deriveActionableNotifications([
      { ...baseAgent, subscription_status: 'past_due' },
    ]);
    const billingNotif = notifications.find((n) => n.type === 'credential_expiring');
    expect(billingNotif).toBeTruthy();
    expect(billingNotif!.title).toMatch(/billing/i);
  });

  it('does not produce demo-id notifications (no hardcoded demo-* IDs)', () => {
    const notifications = deriveActionableNotifications([
      { ...baseAgent, configured: false, subscription_status: 'past_due' },
    ]);
    const demoIds = notifications.filter((n) => n.id.startsWith('demo-'));
    expect(demoIds).toHaveLength(0);
  });
});


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
    ['deliverable_approved', 'recent'],
    ['deliverable_rejected', 'activity'],
    ['publish_ready', 'recent'],
    ['publish_blocked', 'health'],
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

  it('keeps approval and deliverable outcome routes aligned to different runtime surfaces', () => {
    const approvalResult = resolveNavigationTarget({
      ...baseNotification,
      type: 'approval_required',
    });
    const approvedDeliverableResult = resolveNavigationTarget({
      ...baseNotification,
      type: 'deliverable_approved',
    });

    expect((approvalResult!.params as any).focusSection).toBe('approvals');
    expect((approvedDeliverableResult!.params as any).focusSection).toBe('recent');
  });

  it('keeps publish-ready and publish-blocked routes on different runtime surfaces', () => {
    const readyResult = resolveNavigationTarget({
      ...baseNotification,
      type: 'publish_ready',
    });
    const blockedResult = resolveNavigationTarget({
      ...baseNotification,
      type: 'publish_blocked',
    });

    expect((readyResult!.params as any).focusSection).toBe('recent');
    expect((blockedResult!.params as any).focusSection).toBe('health');
  });
});
