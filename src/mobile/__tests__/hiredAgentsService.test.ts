/**
 * Hired Agents Service Tests
 * Tests for hired agents service API calls
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { hiredAgentsService } from '../src/services/hiredAgents/hiredAgents.service';
import apiClient from '../src/lib/apiClient';

// @ts-ignore
apiClient.get = jest.fn();
import type {
  MyAgentInstanceSummary,
  HiredAgentInstance,
  TrialStatusRecord,
  MyAgentsSummaryResponse,
  TrialStatusListResponse,
} from '../src/types/hiredAgents.types';

// Mock apiClient
jest.mock('../src/lib/apiClient');

describe('HiredAgentsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('listMyAgents', () => {
    it('should fetch hired agents summary from API', async () => {
      const mockSummary: MyAgentInstanceSummary[] = [
        {
          subscription_id: 'SUB-123',
          agent_id: 'AGT-MKT-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRE-123',
          agent_type_id: 'marketing.content.v1',
          nickname: 'Content Bot',
          configured: true,
          goals_completed: true,
          trial_status: 'active',
          trial_start_at: '2024-01-01T00:00:00Z',
          trial_end_at: '2024-01-08T00:00:00Z',
        },
      ];

      const mockResponse: MyAgentsSummaryResponse = {
        instances: mockSummary,
      };

      (apiClient.get as any).mockResolvedValue({ data: mockResponse });

      const result = await hiredAgentsService.listMyAgents();

      expect(apiClient.get).toHaveBeenCalledWith('/cp/my-agents/summary');
      expect(result).toEqual(mockSummary);
    });

    it('should return empty array when instances is missing', async () => {
      const mockResponse: MyAgentsSummaryResponse = {
        instances: undefined as any,
      };

      (apiClient.get as any).mockResolvedValue({ data: mockResponse });

      const result = await hiredAgentsService.listMyAgents();

      expect(result).toEqual([]);
    });
  });

  describe('getHiredAgentBySubscription', () => {
    it('should fetch hired agent by subscription ID', async () => {
      const mockHiredAgent: HiredAgentInstance = {
        hired_instance_id: 'HIRE-123',
        subscription_id: 'SUB-123',
        agent_id: 'AGT-MKT-001',
        agent_type_id: 'marketing.content.v1',
        customer_id: 'CUST-456',
        nickname: 'Content Bot',
        theme: 'dark',
        config: { timezone: 'Asia/Kolkata' },
        configured: true,
        goals_completed: true,
        trial_status: 'active',
        trial_start_at: '2024-01-01T00:00:00Z',
        trial_end_at: '2024-01-08T00:00:00Z',
        subscription_status: 'active',
        active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      (apiClient.get as any).mockResolvedValue({ data: mockHiredAgent });

      const result = await hiredAgentsService.getHiredAgentBySubscription('SUB-123');

      expect(apiClient.get).toHaveBeenCalledWith('/cp/hired-agents/by-subscription/SUB-123');
      expect(result).toEqual(mockHiredAgent);
    });

    it('should encode subscription ID with special characters', async () => {
      const mockHiredAgent: HiredAgentInstance = {
        hired_instance_id: 'HIRE-123',
        subscription_id: 'SUB/123',
        agent_id: 'AGT-MKT-001',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      (apiClient.get as any).mockResolvedValue({ data: mockHiredAgent });

      await hiredAgentsService.getHiredAgentBySubscription('SUB/123');

      // Should encode the slash
      expect(apiClient.get).toHaveBeenCalledWith('/cp/hired-agents/by-subscription/SUB%2F123');
    });
  });

  describe('listTrialStatus', () => {
    it('should fetch trial status list from API', async () => {
      const mockTrials: TrialStatusRecord[] = [
        {
          subscription_id: 'SUB-123',
          hired_instance_id: 'HIRE-123',
          trial_status: 'active',
          trial_start_at: '2024-01-01T00:00:00Z',
          trial_end_at: '2024-01-08T00:00:00Z',
          configured: true,
          goals_completed: true,
        },
        {
          subscription_id: 'SUB-456',
          hired_instance_id: 'HIRE-456',
          trial_status: 'expired',
          trial_start_at: '2023-12-01T00:00:00Z',
          trial_end_at: '2023-12-08T00:00:00Z',
          configured: true,
          goals_completed: true,
        },
      ];

      const mockResponse: TrialStatusListResponse = {
        trials: mockTrials,
      };

      (apiClient.get as any).mockResolvedValue({ data: mockResponse });

      const result = await hiredAgentsService.listTrialStatus();

      expect(apiClient.get).toHaveBeenCalledWith('/v1/trial-status');
      expect(result).toEqual(mockTrials);
    });

    it('should return empty array when trials is missing', async () => {
      const mockResponse: TrialStatusListResponse = {
        trials: undefined,
      };

      (apiClient.get as any).mockResolvedValue({ data: mockResponse });

      const result = await hiredAgentsService.listTrialStatus();

      expect(result).toEqual([]);
    });
  });

  describe('getTrialStatusBySubscription', () => {
    it('should fetch trial status by subscription ID', async () => {
      const mockTrialStatus: TrialStatusRecord = {
        subscription_id: 'SUB-123',
        hired_instance_id: 'HIRE-123',
        trial_status: 'active',
        trial_start_at: '2024-01-01T00:00:00Z',
        trial_end_at: '2024-01-08T00:00:00Z',
        configured: true,
        goals_completed: true,
      };

      (apiClient.get as any).mockResolvedValue({ data: mockTrialStatus });

      const result = await hiredAgentsService.getTrialStatusBySubscription('SUB-123');

      expect(apiClient.get).toHaveBeenCalledWith('/v1/trial-status/by-subscription/SUB-123');
      expect(result).toEqual(mockTrialStatus);
    });
  });

  describe('listActiveHiredAgents', () => {
    it('should filter and return only active agents', async () => {
      const mockSummary: MyAgentInstanceSummary[] = [
        {
          subscription_id: 'SUB-123',
          agent_id: 'AGT-MKT-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: false,
        },
        {
          subscription_id: 'SUB-456',
          agent_id: 'AGT-EDU-001',
          duration: 'monthly',
          status: 'canceled',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: true,
        },
        {
          subscription_id: 'SUB-789',
          agent_id: 'AGT-SALES-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: false,
        },
      ];

      const mockResponse: MyAgentsSummaryResponse = {
        instances: mockSummary,
      };

      (apiClient.get as any).mockResolvedValue({ data: mockResponse });

      const result = await hiredAgentsService.listActiveHiredAgents();

      expect(result).toHaveLength(2);
      expect(result[0].status).toBe('active');
      expect(result[1].status).toBe('active');
    });
  });

  describe('listAgentsInTrial', () => {
    it('should filter and return only agents in active trial', async () => {
      const mockSummary: MyAgentInstanceSummary[] = [
        {
          subscription_id: 'SUB-123',
          agent_id: 'AGT-MKT-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: false,
          trial_status: 'active',
        },
        {
          subscription_id: 'SUB-456',
          agent_id: 'AGT-EDU-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: false,
          trial_status: 'expired',
        },
        {
          subscription_id: 'SUB-789',
          agent_id: 'AGT-SALES-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: false,
          trial_status: 'active',
        },
      ];

      const mockResponse: MyAgentsSummaryResponse = {
        instances: mockSummary,
      };

      (apiClient.get as any).mockResolvedValue({ data: mockResponse });

      const result = await hiredAgentsService.listAgentsInTrial();

      expect(result).toHaveLength(2);
      expect(result[0].trial_status).toBe('active');
      expect(result[1].trial_status).toBe('active');
    });
  });

  describe('listAgentsNeedingSetup', () => {
    it('should filter and return agents not configured', async () => {
      const mockSummary: MyAgentInstanceSummary[] = [
        {
          subscription_id: 'SUB-123',
          agent_id: 'AGT-MKT-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: false,
          configured: false,
          goals_completed: false,
        },
        {
          subscription_id: 'SUB-456',
          agent_id: 'AGT-EDU-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: false,
          configured: true,
          goals_completed: true,
        },
      ];

      const mockResponse: MyAgentsSummaryResponse = {
        instances: mockSummary,
      };

      (apiClient.get as any).mockResolvedValue({ data: mockResponse });

      const result = await hiredAgentsService.listAgentsNeedingSetup();

      expect(result).toHaveLength(1);
      expect(result[0].configured).toBe(false);
    });

    it('should filter and return agents with goals not completed', async () => {
      const mockSummary: MyAgentInstanceSummary[] = [
        {
          subscription_id: 'SUB-123',
          agent_id: 'AGT-MKT-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2024-01-01T00:00:00Z',
          current_period_end: '2024-02-01T00:00:00Z',
          cancel_at_period_end: false,
          configured: true,
          goals_completed: false,
        },
      ];

      const mockResponse: MyAgentsSummaryResponse = {
        instances: mockSummary,
      };

      (apiClient.get as any).mockResolvedValue({ data: mockResponse });

      const result = await hiredAgentsService.listAgentsNeedingSetup();

      expect(result).toHaveLength(1);
      expect(result[0].goals_completed).toBe(false);
    });
  });
});
