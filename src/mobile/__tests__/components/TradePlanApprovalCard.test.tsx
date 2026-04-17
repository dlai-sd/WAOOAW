/**
 * TradePlanApprovalCard tests
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { TradePlanApprovalCard } from '@/components/TradePlanApprovalCard';

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: { textPrimary: '#fff', textSecondary: '#a1a1aa', background: '#0a0a0a', surface: '#18181b', border: '#27272a' },
    typography: {
      fontFamily: { body: 'Inter', bodyBold: 'Inter-Bold', heading: 'Outfit' },
      fontSize: { sm: 12, md: 14, lg: 16 },
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24 },
  }),
}));

const MOCK_DELIVERABLE = {
  id: 'DEL-001',
  type: 'trade_plan',
  status: 'pending_approval',
  symbol: 'RELIANCE',
  action: 'BUY' as const,
  price: 2500,
  quantity: 10,
  risk_rating: 'medium' as const,
  hired_agent_id: 'ha-1',
  created_at: '2026-01-01T00:00:00Z',
};

describe('TradePlanApprovalCard', () => {
  const mockApprove = jest.fn();
  const mockReject = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it('renders symbol', () => {
    render(<TradePlanApprovalCard deliverable={MOCK_DELIVERABLE} onApprove={mockApprove} onReject={mockReject} />);
    expect(screen.getByText('RELIANCE')).toBeTruthy();
  });

  it('renders action chip BUY', () => {
    render(<TradePlanApprovalCard deliverable={MOCK_DELIVERABLE} onApprove={mockApprove} onReject={mockReject} />);
    expect(screen.getByText('BUY')).toBeTruthy();
  });

  it('renders SELL action', () => {
    render(<TradePlanApprovalCard deliverable={{ ...MOCK_DELIVERABLE, action: 'SELL' }} onApprove={mockApprove} onReject={mockReject} />);
    expect(screen.getByText('SELL')).toBeTruthy();
  });

  it('renders risk rating chip', () => {
    render(<TradePlanApprovalCard deliverable={MOCK_DELIVERABLE} onApprove={mockApprove} onReject={mockReject} />);
    expect(screen.getByText('MEDIUM RISK')).toBeTruthy();
  });

  it('renders low risk', () => {
    render(<TradePlanApprovalCard deliverable={{ ...MOCK_DELIVERABLE, risk_rating: 'low' }} onApprove={mockApprove} onReject={mockReject} />);
    expect(screen.getByText('LOW RISK')).toBeTruthy();
  });

  it('renders high risk', () => {
    render(<TradePlanApprovalCard deliverable={{ ...MOCK_DELIVERABLE, risk_rating: 'high' }} onApprove={mockApprove} onReject={mockReject} />);
    expect(screen.getByText('HIGH RISK')).toBeTruthy();
  });

  it('renders no risk chip when risk_rating undefined', () => {
    const { risk_rating: _, ...noRisk } = MOCK_DELIVERABLE as any;
    render(<TradePlanApprovalCard deliverable={noRisk} onApprove={mockApprove} onReject={mockReject} />);
    expect(screen.queryByText(/RISK/)).toBeNull();
  });

  it('renders price and quantity', () => {
    render(<TradePlanApprovalCard deliverable={MOCK_DELIVERABLE} onApprove={mockApprove} onReject={mockReject} />);
    expect(screen.getByText(/2500|2,500/)).toBeTruthy();
    expect(screen.getByText(/10/)).toBeTruthy();
  });

  it('calls onApprove with id when Approve pressed', () => {
    render(<TradePlanApprovalCard deliverable={MOCK_DELIVERABLE} onApprove={mockApprove} onReject={mockReject} />);
    fireEvent.press(screen.getByText(/approve/i));
    expect(mockApprove).toHaveBeenCalledWith('DEL-001');
  });

  it('calls onReject with id when Reject pressed', () => {
    render(<TradePlanApprovalCard deliverable={MOCK_DELIVERABLE} onApprove={mockApprove} onReject={mockReject} />);
    fireEvent.press(screen.getByText(/reject/i));
    expect(mockReject).toHaveBeenCalledWith('DEL-001');
  });

  it('renders dash when symbol is undefined', () => {
    const { symbol: _, ...noSymbol } = MOCK_DELIVERABLE as any;
    render(<TradePlanApprovalCard deliverable={noSymbol} onApprove={mockApprove} onReject={mockReject} />);
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });
});
