/**
 * Platform Connections Service Tests (MOB-PARITY-1 E4-S1)
 */

const mockCpGet = jest.fn();
const mockCpPost = jest.fn();
const mockCpDelete = jest.fn(() => Promise.resolve({ data: null }));

jest.mock('../src/lib/apiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockCpGet(...args),
    post: (...args: unknown[]) => mockCpPost(...args),
    delete: (...args: unknown[]) => mockCpDelete(...args),
  },
}));

import {
  listPlatformConnections,
  createPlatformConnection,
  deletePlatformConnection,
  startYouTubeOAuth,
  PlatformConnection,
} from '../src/services/platformConnections.service';

describe('platformConnections.service', () => {
  beforeEach(() => jest.clearAllMocks());

  it('listPlatformConnections returns typed array', async () => {
    const mockData: PlatformConnection[] = [
      {
        id: 'conn1',
        hired_instance_id: 'ha1',
        skill_id: 'digital_marketing',
        platform_key: 'youtube',
        status: 'connected',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ];
    mockCpGet.mockResolvedValue({ data: mockData });

    const result = await listPlatformConnections('ha1');

    expect(result).toEqual(mockData);
    expect(mockCpGet).toHaveBeenCalledWith('/api/v1/hired-agents/ha1/platform-connections');
  });

  it('listPlatformConnections handles wrapped connections response', async () => {
    const mockData: PlatformConnection[] = [
      {
        id: 'conn2',
        hired_instance_id: 'ha1',
        skill_id: 'digital_marketing',
        platform_key: 'instagram',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ];
    mockCpGet.mockResolvedValue({ data: { connections: mockData } });

    const result = await listPlatformConnections('ha1');

    expect(result).toEqual(mockData);
  });

  it('createPlatformConnection returns typed PlatformConnection', async () => {
    const mockCreated: PlatformConnection = {
      id: 'conn-new',
      hired_instance_id: 'ha1',
      skill_id: 'digital_marketing',
      platform_key: 'facebook',
      status: 'pending',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    };
    mockCpPost.mockResolvedValue({ data: mockCreated });

    const result = await createPlatformConnection('ha1', {
      skill_id: 'digital_marketing',
      platform_key: 'facebook',
      credentials: { token: 'abc' },
    });

    expect(result).toEqual(mockCreated);
    expect(mockCpPost).toHaveBeenCalledWith(
      '/api/v1/hired-agents/ha1/platform-connections',
      expect.objectContaining({ platform_key: 'facebook' })
    );
  });

  it('startYouTubeOAuth returns authorization_url', async () => {
    const mockResponse = { authorization_url: 'https://accounts.google.com/auth' };
    mockCpPost.mockResolvedValue({ data: mockResponse });

    const result = await startYouTubeOAuth('waooaw://youtube-callback');

    expect(result).toEqual(mockResponse);
    expect(mockCpPost).toHaveBeenCalledWith(
      '/api/v1/customer-platform-connections/youtube/connect/start',
      { redirect_uri: 'waooaw://youtube-callback' }
    );
  });

  it('deletePlatformConnection calls delete endpoint', async () => {
    mockCpDelete.mockResolvedValue({ data: null });

    await deletePlatformConnection('ha1', 'conn1');

    expect(mockCpDelete).toHaveBeenCalledWith(
      '/api/v1/hired-agents/ha1/platform-connections/conn1'
    );
  });
});
