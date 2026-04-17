/**
 * Agent Service Tests — updated to match refactored API paths
 * listAgents → /api/v1/catalog/agents (with catalogToAgent mapper)
 * searchAgents → client-side filter on catalog results
 * All other endpoints → /api/v1/...
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { agentService } from '../../src/services/agents/agent.service';
import apiClient from '../../src/lib/apiClient';
import type { Agent, AgentTypeDefinition, Skill, JobRole } from '../../src/types/agent.types';

// Mock apiClient
jest.mock('../../src/lib/apiClient');

describe('AgentService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('listAgentTypes', () => {
    it('should fetch agent types from API', async () => {
      const mockAgentTypes: AgentTypeDefinition[] = [
        {
          agent_type_id: 'type-1',
          display_name: 'Marketing Agent',
          version: '1.0.0',
        },
        {
          agent_type_id: 'type-2',
          display_name: 'Sales Agent',
          version: '1.0.0',
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAgentTypes });

      const result = await agentService.listAgentTypes();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/agent-types');
      expect(result).toEqual(mockAgentTypes);
    });
  });

  describe('listAgents', () => {
    // listAgents now calls /api/v1/catalog/agents and maps via catalogToAgent
    const mockCatalog = [
      {
        release_id: 'rel-1',
        id: 'agent-1',
        public_name: 'Content Marketing Agent',
        short_description: 'Creates content',
        industry_name: 'marketing',
        job_role_label: 'Content Marketer',
        monthly_price_inr: 12000,
        trial_days: 7,
        allowed_durations: ['monthly'],
        supported_channels: ['youtube'],
        agent_type_id: 'type-1',
        lifecycle_state: 'live',
        approved_for_new_hire: true,
        retired_from_catalog_at: null,
      },
    ];

    it('should fetch agents from catalog endpoint', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockCatalog });

      const result = await agentService.listAgents();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/catalog/agents');
      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('Content Marketing Agent');
      expect(result[0].price).toBe(12000);
    });

    it('should filter agents by industry client-side', async () => {
      const multiCatalog = [
        { ...mockCatalog[0], id: 'a1', industry_name: 'marketing', lifecycle_state: 'live' },
        { ...mockCatalog[0], id: 'a2', public_name: 'Edu Agent', industry_name: 'education', lifecycle_state: 'live' },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ data: multiCatalog });

      const result = await agentService.listAgents({ industry: 'marketing' });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/catalog/agents');
      expect(result).toHaveLength(1);
      expect(result[0].industry).toBe('marketing');
    });

    it('should map lifecycle_state=live to status=active', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockCatalog });

      const result = await agentService.listAgents();

      expect(result[0].status).toBe('active');
    });

    it('should map non-live lifecycle_state to status=inactive', async () => {
      const retired = [{ ...mockCatalog[0], lifecycle_state: 'retired' }];
      (apiClient.get as jest.Mock).mockResolvedValue({ data: retired });

      const result = await agentService.listAgents();

      expect(result[0].status).toBe('inactive');
    });
  });

  describe('getAgent', () => {
    it('should fetch single agent by ID', async () => {
      const mockAgent: Agent = {
        id: 'agent-123',
        name: 'Test Agent',
        description: 'Test description',
        job_role_id: 'role-1',
        industry: 'marketing',
        entity_type: 'agent',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
        rating: 4.5,
        price: 12000,
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAgent });

      const result = await agentService.getAgent('agent-123');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/agents/agent-123');
      expect(result).toEqual(mockAgent);
    });
  });

  describe('searchAgents', () => {
    // searchAgents does client-side filtering on top of catalog
    const mockCatalog = [
      {
        release_id: 'rel-1', id: 'a1', public_name: 'Marketing Agent', short_description: 'Marketing',
        industry_name: 'marketing', job_role_label: 'Marketer', monthly_price_inr: 12000, trial_days: 7,
        allowed_durations: ['monthly'], supported_channels: ['youtube'], agent_type_id: 'type-1',
        lifecycle_state: 'live', approved_for_new_hire: true, retired_from_catalog_at: null,
      },
      {
        release_id: 'rel-2', id: 'a2', public_name: 'Sales Agent', short_description: 'Sales',
        industry_name: 'sales', job_role_label: 'SDR', monthly_price_inr: 10000, trial_days: 7,
        allowed_durations: ['monthly'], supported_channels: [], agent_type_id: 'type-2',
        lifecycle_state: 'live', approved_for_new_hire: true, retired_from_catalog_at: null,
      },
    ];

    it('should filter agents by query string (name match)', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockCatalog });

      const result = await agentService.searchAgents('marketing');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/catalog/agents');
      expect(result.length).toBeGreaterThanOrEqual(1);
    });

    it('should return all agents when query is empty/whitespace', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockCatalog });

      const result = await agentService.searchAgents('   ');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/catalog/agents');
      expect(result).toHaveLength(2);
    });

    it('should combine query and industry filter', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockCatalog });

      const result = await agentService.searchAgents('agent', { industry: 'sales' });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/catalog/agents');
      // Only the sales agent should remain after industry filter
      expect(result.every((a) => a.industry === 'sales')).toBe(true);
    });
  });

  describe('listSkills', () => {
    it('should fetch skills without filters', async () => {
      const mockSkills: Skill[] = [
        {
          id: 'skill-1',
          name: 'SEO',
          description: 'Search Engine Optimization',
          category: 'technical',
          entity_type: 'skill',
          status: 'certified',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockSkills });

      const result = await agentService.listSkills();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/skills');
      expect(result).toEqual(mockSkills);
    });

    it('should fetch skills with category filter', async () => {
      const mockSkills: Skill[] = [];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockSkills });

      await agentService.listSkills({ category: 'domain_expertise', limit: 20 });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/skills?category=domain_expertise&limit=20');
    });
  });

  describe('getSkill', () => {
    it('should fetch single skill by ID', async () => {
      const mockSkill: Skill = {
        id: 'skill-123',
        name: 'Content Writing',
        description: 'Create engaging content',
        category: 'soft_skill',
        entity_type: 'skill',
        status: 'certified',
        created_at: '2024-01-01T00:00:00Z',
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockSkill });

      const result = await agentService.getSkill('skill-123');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/skills/skill-123');
      expect(result).toEqual(mockSkill);
    });
  });

  describe('listJobRoles', () => {
    it('should fetch job roles', async () => {
      const mockJobRoles: JobRole[] = [
        {
          id: 'role-1',
          name: 'Content Marketer',
          description: 'Creates marketing content',
          required_skills: ['skill-1', 'skill-2'],
          seniority_level: 'mid',
          entity_type: 'job_role',
          status: 'certified',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockJobRoles });

      const result = await agentService.listJobRoles({ limit: 10 });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/job-roles?limit=10');
      expect(result).toEqual(mockJobRoles);
    });
  });

  describe('getJobRole', () => {
    it('should fetch single job role by ID', async () => {
      const mockJobRole: JobRole = {
        id: 'role-123',
        name: 'Senior Marketer',
        description: 'Lead marketing initiatives',
        required_skills: ['skill-1', 'skill-2', 'skill-3'],
        seniority_level: 'senior',
        entity_type: 'job_role',
        status: 'certified',
        created_at: '2024-01-01T00:00:00Z',
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockJobRole });

      const result = await agentService.getJobRole('role-123');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/job-roles/role-123');
      expect(result).toEqual(mockJobRole);
    });
  });

  describe('buildQueryString', () => {
    it('should always call catalog endpoint for listAgents', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: [] });

      await agentService.listAgents({ industry: 'marketing' });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/catalog/agents');
    });

    it('should always call catalog endpoint for searchAgents', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: [] });

      await agentService.searchAgents('test');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/catalog/agents');
    });

    it('should build query string for skills endpoint', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: [] });

      await agentService.listSkills({ category: 'technical', limit: 5 });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/skills?category=technical&limit=5');
    });
  });
});
