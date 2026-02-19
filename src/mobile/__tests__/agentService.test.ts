/**
 * Agent Service Tests
 * Tests for agent service API calls
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

      expect(apiClient.get).toHaveBeenCalledWith('/v1/agent-types');
      expect(result).toEqual(mockAgentTypes);
    });
  });

  describe('listAgents', () => {
    it('should fetch agents without filters', async () => {
      const mockAgents: Agent[] = [
        {
          id: 'agent-1',
          name: 'Content Marketing Agent',
          description: 'Creates content',
          job_role_id: 'role-1',
          industry: 'marketing',
          entity_type: 'agent',
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAgents });

      const result = await agentService.listAgents();

      expect(apiClient.get).toHaveBeenCalledWith('/v1/agents');
      expect(result).toEqual(mockAgents);
    });

    it('should fetch agents with industry filter', async () => {
      const mockAgents: Agent[] = [
        {
          id: 'agent-1',
          name: 'Content Marketing Agent',
          description: 'Creates content',
          job_role_id: 'role-1',
          industry: 'marketing',
          entity_type: 'agent',
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAgents });

      const result = await agentService.listAgents({ industry: 'marketing' });

      expect(apiClient.get).toHaveBeenCalledWith('/v1/agents?industry=marketing');
      expect(result).toEqual(mockAgents);
    });

    it('should fetch agents with multiple filters', async () => {
      const mockAgents: Agent[] = [];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAgents });

      await agentService.listAgents({
        industry: 'education',
        status: 'active',
        limit: 10,
        offset: 0,
      });

      expect(apiClient.get).toHaveBeenCalledWith(
        '/v1/agents?industry=education&status=active&limit=10&offset=0'
      );
    });

    it('should handle empty filter values', async () => {
      const mockAgents: Agent[] = [];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAgents });

      await agentService.listAgents({
        industry: undefined,
        status: 'active',
        limit: null as any,
      });

      // Should only include status (not undefined/null values)
      expect(apiClient.get).toHaveBeenCalledWith('/v1/agents?status=active');
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

      expect(apiClient.get).toHaveBeenCalledWith('/v1/agents/agent-123');
      expect(result).toEqual(mockAgent);
    });
  });

  describe('searchAgents', () => {
    it('should search agents with query', async () => {
      const mockAgents: Agent[] = [
        {
          id: 'agent-1',
          name: 'Marketing Agent',
          description: 'Marketing specialist',
          job_role_id: 'role-1',
          industry: 'marketing',
          entity_type: 'agent',
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAgents });

      const result = await agentService.searchAgents('marketing');

      expect(apiClient.get).toHaveBeenCalledWith('/v1/agents?q=marketing');
      expect(result).toEqual(mockAgents);
    });

    it('should search with query and filters', async () => {
      const mockAgents: Agent[] = [];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAgents });

      await agentService.searchAgents('content', { industry: 'marketing', limit: 5 });

      expect(apiClient.get).toHaveBeenCalledWith('/v1/agents?industry=marketing&limit=5&q=content');
    });

    it('should fallback to listAgents when query is empty', async () => {
      const mockAgents: Agent[] = [];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAgents });

      await agentService.searchAgents('   '); // Empty/whitespace query

      expect(apiClient.get).toHaveBeenCalledWith('/v1/agents');
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

      expect(apiClient.get).toHaveBeenCalledWith('/v1/skills');
      expect(result).toEqual(mockSkills);
    });

    it('should fetch skills with category filter', async () => {
      const mockSkills: Skill[] = [];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockSkills });

      await agentService.listSkills({ category: 'domain_expertise', limit: 20 });

      expect(apiClient.get).toHaveBeenCalledWith('/v1/skills?category=domain_expertise&limit=20');
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

      expect(apiClient.get).toHaveBeenCalledWith('/v1/skills/skill-123');
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

      expect(apiClient.get).toHaveBeenCalledWith('/v1/job-roles?limit=10');
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

      expect(apiClient.get).toHaveBeenCalledWith('/v1/job-roles/role-123');
      expect(result).toEqual(mockJobRole);
    });
  });

  describe('buildQueryString', () => {
    it('should build query string with single param', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: [] });
      
      await agentService.listAgents({ industry: 'marketing' });
      
      expect(apiClient.get).toHaveBeenCalledWith('/v1/agents?industry=marketing');
    });

    it('should build query string with multiple params', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: [] });
      
      await agentService.listAgents({ 
        industry: 'education',
        status: 'active',
        limit: 20,
        offset: 10,
      });
      
      expect(apiClient.get).toHaveBeenCalledWith(
        '/v1/agents?industry=education&status=active&limit=20&offset=10'
      );
    });

    it('should handle special characters in query params', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: [] });
      
      await agentService.searchAgents('marketing & sales');
      
      expect(apiClient.get).toHaveBeenCalledWith(
        '/v1/agents?q=marketing%20%26%20sales'
      );
    });
  });
});
