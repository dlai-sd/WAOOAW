// CP-SKILLS-2 regression: unit tests for agentSkills.service
// Verifies that listHiredAgentSkills and saveGoalConfig call the correct
// CP backend routes via gatewayRequestJson with the right payloads.

import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('agentSkills.service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  // ──────────────────────────────────────────────────────────────────────────
  // listHiredAgentSkills
  // ──────────────────────────────────────────────────────────────────────────

  it('calls the hired-agent skills endpoint and returns an array', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue([
      { skill_id: 'skill-1', name: 'content_posting', display_name: 'Content Posting' },
    ])

    const svc = await import('../services/agentSkills.service')
    const result = await svc.listHiredAgentSkills('hire-instance-abc')

    expect(spy).toHaveBeenCalledWith('/cp/hired-agents/hire-instance-abc/skills')
    expect(result).toHaveLength(1)
    expect(result[0].skill_id).toBe('skill-1')
  })

  it('handles wrapped { skills: [...] } response from listHiredAgentSkills', async () => {
    const gateway = await import('../services/gatewayApiClient')
    vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      skills: [
        { skill_id: 'skill-2', name: 'seo_audit', display_name: 'SEO Audit' },
      ],
    })

    const svc = await import('../services/agentSkills.service')
    const result = await svc.listHiredAgentSkills('hire-instance-def')

    expect(result).toHaveLength(1)
    expect(result[0].skill_id).toBe('skill-2')
  })

  it('returns empty array when listHiredAgentSkills response is not array-like', async () => {
    const gateway = await import('../services/gatewayApiClient')
    vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      unexpected_shape: true,
    })

    const svc = await import('../services/agentSkills.service')
    const result = await svc.listHiredAgentSkills('hire-instance-xyz')

    expect(result).toEqual([])
  })

  // ──────────────────────────────────────────────────────────────────────────
  // saveGoalConfig
  // ──────────────────────────────────────────────────────────────────────────

  it('calls PATCH goal-config route with correct path and body', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      skill_id: 'skill-1',
      name: 'content_posting',
      display_name: 'Content Posting',
      goal_config: { frequency: 'daily', tone: 'professional' },
    })

    const svc = await import('../services/agentSkills.service')
    const result = await svc.saveGoalConfig('hire-abc', 'skill-1', {
      frequency: 'daily',
      tone: 'professional',
    })

    expect(spy).toHaveBeenCalledWith(
      '/cp/hired-agents/hire-abc/skills/skill-1/goal-config',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ goal_config: { frequency: 'daily', tone: 'professional' } }),
      })
    )
    expect(result.goal_config).toEqual({ frequency: 'daily', tone: 'professional' })
  })

  it('propagates rejection when saveGoalConfig backend returns error', async () => {
    const gateway = await import('../services/gatewayApiClient')
    vi.spyOn(gateway, 'gatewayRequestJson' as any).mockRejectedValue(
      Object.assign(new Error('Skill not attached to hired agent'), { status: 404 })
    )

    const svc = await import('../services/agentSkills.service')
    await expect(
      svc.saveGoalConfig('hire-abc', 'skill-not-attached', { frequency: 'daily' })
    ).rejects.toThrow('Skill not attached to hired agent')
  })

  it('URL-encodes hired_instance_id and skill_id with special characters', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      skill_id: 'skill/1',
      name: 'test',
      display_name: 'Test',
    })

    const svc = await import('../services/agentSkills.service')
    await svc.saveGoalConfig('hire/abc', 'skill/1', {})

    expect(spy).toHaveBeenCalledWith(
      '/cp/hired-agents/hire%2Fabc/skills/skill%2F1/goal-config',
      expect.anything()
    )
  })

  it('identifies the Digital Marketing Agent by agent_id or type', async () => {
    const svc = await import('../services/agentSkills.service')

    expect(svc.isDigitalMarketingAgent('AGT-MKT-DMA-001', null)).toBe(true)
    expect(svc.isDigitalMarketingAgent(null, 'marketing.digital_marketing.v1')).toBe(true)
    expect(svc.isDigitalMarketingAgent('AGT-TRD-001', 'trading.share_trader.v1')).toBe(false)
  })

  it('finds the Theme Discovery skill from a hired-agent skill list', async () => {
    const svc = await import('../services/agentSkills.service')

    const result = svc.getThemeDiscoverySkill([
      { skill_id: 'skill-1', name: 'content_creation', display_name: 'Content Creation' },
      { skill_id: 'skill-2', name: 'theme_discovery', display_name: 'Theme Discovery' },
    ])

    expect(result?.skill_id).toBe('skill-2')
  })
})
