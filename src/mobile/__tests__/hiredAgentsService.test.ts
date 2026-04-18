/**
 * Hired Agents Service Tests — updated to match refactored API paths
 * All calls now go through apiClient (Plant Backend) not cpApiClient
 * listMyAgents requires customerId
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { hiredAgentsService } from '../src/services/hiredAgents/hiredAgents.service';
import apiClient from '../src/lib/apiClient';

import type {
  Deliverable,
  MyAgentInstanceSummary,
  HiredAgentInstance,
  TrialStatusRecord,
  MyAgentsSummaryResponse,
  TrialStatusListResponse,
} from '../src/types/hiredAgents.types';

jest.mock('../src/lib/apiClient');
jest.mock('../src/lib/cpApiClient');

const MOCK_CUSTOMER_ID = 'CUST-001';

describe('HiredAgentsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (apiClient.get as jest.Mock).mockReset();
  });

  describe('listMyAgents', () => {
    it('should return empty array when no customerId is provided', async () => {
      const result = await hiredAgentsService.listMyAgents();
      expect(apiClient.get).not.toHaveBeenCalled();
      expect(result).toEqual([]);
    });

    it('should fetch hired agents from Plant Backend by customerId', async () => {
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
        },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ data: { instances: mockSummary } });

      const result = await hiredAgentsService.listMyAgents(MOCK_CUSTOMER_ID);

      expect(apiClient.get).toHaveBeenCalledWith(
        `/api/v1/hired-agents/by-customer/${MOCK_CUSTOMER_ID}`
      );
      expect(result).toEqual(mockSummary);
    });

    it('should return empty array when instances is missing', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: {} });
      const result = await hiredAgentsService.listMyAgents(MOCK_CUSTOMER_ID);
      expect(result).toEqual([]);
    });
  });

  describe('getHiredAgentBySubscription', () => {
    const mockHiredAgent: HiredAgentInstance = {
      hired_instance_id: 'HIRE-123',
      subscription_id: 'SUB-123',
      agent_id: 'AGT-MKT-001',
      agent_type_id: 'marketing.content.v1',
      customer_id: 'CUST-001',
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      subscription_status: 'active',
      active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should fetch hired agent by subscription ID', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockHiredAgent });

      const result = await hiredAgentsService.getHiredAgentBySubscription('SUB-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/hired-agents/by-subscription/SUB-123'
      );
      expect(result).toEqual(mockHiredAgent);
    });

    it('should URL-encode subscription IDs with special chars', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockHiredAgent });
      await hiredAgentsService.getHiredAgentBySubscription('SUB/123');
      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/hired-agents/by-subscription/SUB%2F123'
      );
    });
  });

  describe('getHiredAgentById', () => {
    it('should fetch hired agent by hired instance ID', async () => {
      const mockHiredAgent: HiredAgentInstance = {
        hired_instance_id: 'HIRE-123',
        subscription_id: 'SUB-123',
        agent_id: 'AGT-MKT-001',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockHiredAgent });

      const result = await hiredAgentsService.getHiredAgentById('HIRE-123');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/hired-agents/by-id/HIRE-123');
      expect(result).toEqual(mockHiredAgent);
    });
  });

  describe('getDeliverablesByHiredAgent', () => {
    it('should fetch deliverables from Plant Backend', async () => {
      const mockDeliverables: Deliverable[] = [
        {
          deliverable_id: 'del-1',
          hired_instance_id: 'HIRE-123',
          agent_id: 'AGT-MKT-001',
          title: 'Draft 1',
          type: 'document',
          review_status: 'pending_review',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ data: { deliverables: mockDeliverables } });

      const result = await hiredAgentsService.getDeliverablesByHiredAgent('HIRE-123');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/hired-agents/HIRE-123/deliverables');
      expect(result).toEqual(mockDeliverables);
    });

    it('should return empty array when deliverables is missing', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: {} });
      const result = await hiredAgentsService.getDeliverablesByHiredAgent('HIRE-123');
      expect(result).toEqual([]);
    });
  });

  describe('listTrialStatus', () => {
    it('should fetch trial status list from Plant Backend', async () => {
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
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ data: { trials: mockTrials } });

      const result = await hiredAgentsService.listTrialStatus();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/trial-status');
      expect(result).toEqual(mockTrials);
    });

    it('should return empty array when trials is missing', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: {} });
      const result = await hiredAgentsService.listTrialStatus();
      expect(result).toEqual([]);
    });
  });

  describe('listActiveHiredAgents', () => {
    it('should return only active agents', async () => {
      const instances: MyAgentInstanceSummary[] = [
        { subscription_id: 'S1', agent_id: 'A1', status: 'active', duration: 'monthly', current_period_start: '', current_period_end: '', cancel_at_period_end: false },
        { subscription_id: 'S2', agent_id: 'A2', status: 'canceled', duration: 'monthly', current_period_start: '', current_period_end: '', cancel_at_period_end: true },
        { subscription_id: 'S3', agent_id: 'A3', status: 'active', duration: 'monthly', current_period_start: '', current_period_end: '', cancel_at_period_end: false },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ data: { instances } });

      const result = await hiredAgentsService.listActiveHiredAgents(MOCK_CUSTOMER_ID);

      expect(result).toHaveLength(2);
      expect(result.every(a => a.status === 'active')).toBe(true);
    });
  });

  describe('listAgentsInTrial', () => {
    it('should return only agents in active trial', async () => {
      const instances: MyAgentInstanceSummary[] = [
        { subscription_id: 'S1', agent_id: 'A1', status: 'active', duration: 'monthly', current_period_start: '', current_period_end: '', cancel_at_period_end: false, trial_status: 'active' },
        { subscription_id: 'S2', agent_id: 'A2', status: 'active', duration: 'monthly', current_period_start: '', current_period_end: '', cancel_at_period_end: false, trial_status: 'expired' },
        { subscription_id: 'S3', agent_id: 'A3', status: 'active', duration: 'monthly', current_period_start: '', current_period_end: '', cancel_at_period_end: false, trial_status: 'active' },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ data: { instances } });

      const result = await hiredAgentsService.listAgentsInTrial(MOCK_CUSTOMER_ID);

      expect(result).toHaveLength(2);
      expect(result.every(a => a.trial_status === 'active')).toBe(true);
    });
  });

  describe('listAgentsNeedingSetup', () => {
    it('should return agents that are not configured', async () => {
      const instances: MyAgentInstanceSummary[] = [
        { subscription_id: 'S1', agent_id: 'A1', status: 'active', duration: 'monthly', current_period_start: '', current_period_end: '', cancel_at_period_end: false, configured: false, goals_completed: false },
        { subscription_id: 'S2', agent_id: 'A2', status: 'active', duration: 'monthly', current_period_start: '', current_period_end: '', cancel_at_period_end: false, configured: true, goals_completed: true },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ data: { instances } });

      const result = await hiredAgentsService.listAgentsNeedingSetup(MOCK_CUSTOMER_ID);

      expect(result).toHaveLength(1);
      expect(result[0].configured).toBe(false);
    });

    it('should return agents with goals not completed', async () => {
      const instances: MyAgentInstanceSummary[] = [
        { subscription_id: 'S1', agent_id: 'A1', status: 'active', duration: 'monthly', current_period_start: '', current_period_end: '', cancel_at_period_end: false, configured: true, goals_completed: false },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ data: { instances } });

      const result = await hiredAgentsService.listAgentsNeedingSetup(MOCK_CUSTOMER_ID);

      expect(result).toHaveLength(1);
      expect(result[0].goals_completed).toBe(false);
    });
  });
});
