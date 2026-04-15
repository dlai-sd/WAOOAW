import cpApiClient from '@/lib/cpApiClient'
import {
  listCustomerDraftBatches,
  createDraftBatch,
  approveDraftPost,
  rejectDraftPost,
  createContentBatchFromTheme,
} from '@/services/marketingReview.service'

jest.mock('@/lib/cpApiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}))

const mockGet = (cpApiClient.get as jest.Mock)
const mockPost = (cpApiClient.post as jest.Mock)

const mockBatch = {
  batch_id: 'b1',
  agent_id: 'agt1',
  theme: 'test theme',
  brand_name: 'Test Brand',
  created_at: '2026-01-01T00:00:00Z',
  status: 'draft',
  posts: [],
}

describe('marketingReview.service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('E1-S2-T1: listCustomerDraftBatches resolves with empty array', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    const result = await listCustomerDraftBatches()
    expect(result).toEqual([])
  })

  it('E1-S2-T2: approveDraftPost resolves with review_status approved', async () => {
    mockPost.mockResolvedValueOnce({
      data: { post_id: 'p1', review_status: 'approved', approval_id: 'a1' },
    })
    const result = await approveDraftPost('p1')
    expect(result.review_status).toBe('approved')
  })

  it('E1-S2-T3: createContentBatchFromTheme calls URL containing b1/create-content-batch', async () => {
    mockPost.mockResolvedValueOnce({ data: mockBatch })
    await createContentBatchFromTheme('b1', {})
    const callArgs = mockPost.mock.calls[0]
    expect(callArgs[0]).toContain('b1/create-content-batch')
  })

  it('E1-S2-T4: rejectDraftPost calls correct path with post_id and reason', async () => {
    mockPost.mockResolvedValueOnce({ data: { post_id: 'p1', decision: 'rejected' } })
    await rejectDraftPost('p1', 'off-brand')
    const callArgs = mockPost.mock.calls[0]
    expect(callArgs[0]).toBe('/cp/marketing/draft-posts/reject')
    expect(callArgs[1]).toEqual({ post_id: 'p1', reason: 'off-brand' })
  })
})
