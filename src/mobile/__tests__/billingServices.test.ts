/**
 * Billing Services Tests (MOB-PARITY-1 E2-S1)
 * Covers invoices.service.ts and receipts.service.ts
 */

const mockCpGet = jest.fn();

jest.mock('../src/lib/apiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockCpGet(...args),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

import { listInvoices, getInvoiceHtml } from '../src/services/invoices.service';
import { listReceipts, getReceiptHtml } from '../src/services/receipts.service';

describe('invoices.service', () => {
  beforeEach(() => jest.clearAllMocks());

  it('listInvoices returns array from response', async () => {
    const mockData = [
      { id: 'inv1', amount: 1000, currency: 'INR', status: 'paid', created_at: '2026-01-01' },
    ];
    mockCpGet.mockResolvedValue({ data: mockData });
    const result = await listInvoices();
    expect(result).toEqual(mockData);
    expect(mockCpGet).toHaveBeenCalledWith('/api/v1/invoices');
  });

  it('listInvoices handles wrapped response', async () => {
    const mockData = [{ id: 'inv2', amount: 500, currency: 'INR', status: 'pending', created_at: '2026-01-02' }];
    mockCpGet.mockResolvedValue({ data: { invoices: mockData } });
    const result = await listInvoices();
    expect(result).toEqual(mockData);
  });

  it('getInvoiceHtml returns HTML string', async () => {
    mockCpGet.mockResolvedValue({ data: '<html>Invoice</html>' });
    const result = await getInvoiceHtml('inv1');
    expect(result).toBe('<html>Invoice</html>');
    expect(mockCpGet).toHaveBeenCalledWith('/api/v1/invoices/inv1/html');
  });
});

describe('receipts.service', () => {
  beforeEach(() => jest.clearAllMocks());

  it('listReceipts returns array from response', async () => {
    const mockData = [
      { id: 'rec1', amount: 1000, currency: 'INR', created_at: '2026-01-01', order_id: 'ord1' },
    ];
    mockCpGet.mockResolvedValue({ data: mockData });
    const result = await listReceipts();
    expect(result).toEqual(mockData);
    expect(mockCpGet).toHaveBeenCalledWith('/api/v1/receipts');
  });

  it('listReceipts handles wrapped response', async () => {
    const mockData = [{ id: 'rec2', amount: 200, currency: 'INR', created_at: '2026-01-02', order_id: 'ord2' }];
    mockCpGet.mockResolvedValue({ data: { receipts: mockData } });
    const result = await listReceipts();
    expect(result).toEqual(mockData);
  });

  it('getReceiptHtml returns HTML string', async () => {
    mockCpGet.mockResolvedValue({ data: '<html>Receipt</html>' });
    const result = await getReceiptHtml('rec1');
    expect(result).toBe('<html>Receipt</html>');
    expect(mockCpGet).toHaveBeenCalledWith('/api/v1/receipts/rec1/html');
  });
});
