/**
 * Profile Screens Tests
 * Covers: ProfileScreen, SettingsScreen, EditProfileScreen,
 *         HelpCenterScreen, PaymentMethodsScreen, SubscriptionManagementScreen
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert, Linking } from 'react-native';

// ─── Shared mocks ──────────────────────────────────────────────────────────

const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
const mockNavigation: any = {
  navigate: mockNavigate,
  goBack: mockGoBack,
};

const mockColors = {
  primary: '#667eea',
  textPrimary: '#ffffff',
  textSecondary: '#a1a1aa',
  background: '#0a0a0a',
  surface: '#18181b',
  border: '#27272a',
  error: '#ef4444',
  success: '#10b981',
};
const mockSpacing = {
  xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48,
  screenPadding: { horizontal: 20, vertical: 16 },
};
const mockTypography = {
  fontSize: { xs: 10, sm: 12, md: 14, lg: 16, xl: 20, xxl: 24, xxxl: 32 },
  fontFamily: { body: 'Inter', bodyBold: 'Inter-Bold', heading: 'Outfit' },
};

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({ colors: mockColors, spacing: mockSpacing, typography: mockTypography }),
}));

const mockLogout = jest.fn().mockResolvedValue(undefined);
const mockUpdateUser = jest.fn();

jest.mock('@/store/authStore', () => ({
  useAuthStore: (selector: any) => selector({ logout: mockLogout, updateUser: mockUpdateUser }),
  useCurrentUser: () => ({
    full_name: 'Test User',
    email: 'test@example.com',
    phone: '9999999999',
    business_name: 'Test Biz',
    industry: 'marketing',
  }),
}));

jest.mock('@react-navigation/native', () => ({
  useNavigation: () => mockNavigation,
}));

jest.mock('@/lib/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

// ─── ProfileScreen ─────────────────────────────────────────────────────────

import { ProfileScreen } from '@/screens/profile/ProfileScreen';

describe('ProfileScreen', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it('renders user name and email', () => {
    render(<ProfileScreen />);
    expect(screen.getByText('Test User')).toBeTruthy();
  });

  it('renders profile menu items', () => {
    render(<ProfileScreen />);
    expect(screen.getByText(/edit profile/i)).toBeTruthy();
    expect(screen.getByText(/subscription/i)).toBeTruthy();
    expect(screen.getByText(/sign out/i)).toBeTruthy();
  });

  it('shows sign out confirmation alert', () => {
    const alertSpy = jest.spyOn(Alert, 'alert');
    render(<ProfileScreen />);
    const signOuts = screen.getAllByText(/sign out/i);
    fireEvent.press(signOuts[signOuts.length - 1]);
    expect(alertSpy).toHaveBeenCalled();
  });

  it('calls logout when confirmed', async () => {
    jest.spyOn(Alert, 'alert').mockImplementationOnce((_title, _msg, buttons: any) => {
      const confirmBtn = buttons?.find((b: any) => b.style === 'destructive');
      confirmBtn?.onPress?.();
    });
    render(<ProfileScreen />);
    const signOuts = screen.getAllByText(/sign out/i);
    fireEvent.press(signOuts[signOuts.length - 1]);
    await waitFor(() => expect(mockLogout).toHaveBeenCalled());
  });

  it('navigates to profile screens when menu items are pressed', () => {
    render(<ProfileScreen />);
    const menus = [
      { text: /edit profile/i, screen: 'EditProfile' },
      { text: /payment methods/i, screen: 'PaymentMethods' },
      { text: /subscription management/i, screen: 'SubscriptionManagement' },
      { text: /usage.*billing|billing/i, screen: 'UsageBilling' },
      { text: /notifications/i, screen: 'Notifications' },
      { text: /settings/i, screen: 'Settings' },
      { text: /help center/i, screen: 'HelpCenter' },
    ];
    for (const { text } of menus) {
      const btn = screen.queryAllByText(text)?.[0];
      if (btn) fireEvent.press(btn);
    }
    expect(mockNavigate).toHaveBeenCalled();
  });

  it('handles logout error gracefully', async () => {
    mockLogout.mockRejectedValueOnce(new Error('Network error'));
    jest.spyOn(Alert, 'alert').mockImplementationOnce((_title, _msg, buttons: any) => {
      const confirmBtn = buttons?.find((b: any) => b.style === 'destructive');
      confirmBtn?.onPress?.();
    });
    render(<ProfileScreen />);
    const signOuts = screen.getAllByText(/sign out/i);
    fireEvent.press(signOuts[signOuts.length - 1]);
    await waitFor(() => expect(mockLogout).toHaveBeenCalled());
    // No crash expected
  });
});

// ─── SettingsScreen ────────────────────────────────────────────────────────

import { SettingsScreen } from '@/screens/profile/SettingsScreen';

describe('SettingsScreen', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it('renders heading', () => {
    render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText(/settings/i)).toBeTruthy();
  });

  it('renders sign out option', () => {
    render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText(/sign out/i)).toBeTruthy();
  });

  it('shows alert on sign out press', () => {
    const alertSpy = jest.spyOn(Alert, 'alert');
    render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(screen.getByText(/sign out/i));
    expect(alertSpy).toHaveBeenCalled();
  });

  it('calls logout when confirmed', async () => {
    jest.spyOn(Alert, 'alert').mockImplementationOnce((_title, _msg, buttons) => {
      const confirmBtn = buttons?.find((b: any) => b.style === 'destructive');
      confirmBtn?.onPress?.();
    });
    render(<SettingsScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(screen.getByText(/sign out/i));
    await waitFor(() => expect(mockLogout).toHaveBeenCalled());
  });
});

// ─── EditProfileScreen ─────────────────────────────────────────────────────

import { EditProfileScreen } from '@/screens/profile/EditProfileScreen';
import apiClient from '@/lib/apiClient';

describe('EditProfileScreen', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it('renders form with user data pre-filled', async () => {
    render(<EditProfileScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByDisplayValue('Test User')).toBeTruthy();
    });
  });

  it('renders save button', () => {
    render(<EditProfileScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText(/save/i)).toBeTruthy();
  });

  it('calls patch API on save', async () => {
    (apiClient.patch as jest.Mock).mockResolvedValue({ data: {} });
    render(<EditProfileScreen navigation={mockNavigation} route={{} as any} />);
    await act(async () => {
      fireEvent.press(screen.getByText(/save/i));
    });
    await waitFor(() => expect(apiClient.patch).toHaveBeenCalled());
  });

  it('renders back navigation', () => {
    render(<EditProfileScreen navigation={mockNavigation} route={{} as any} />);
    // back button or navigates back on cancel
    const backBtn = screen.queryByText(/cancel/i) ?? screen.queryByText(/←/);
    expect(backBtn).toBeTruthy();
  });
});

// ─── HelpCenterScreen ──────────────────────────────────────────────────────

import { HelpCenterScreen } from '@/screens/profile/HelpCenterScreen';

describe('HelpCenterScreen', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it('renders FAQ headings', () => {
    render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText(/7-day trial/i)).toBeTruthy();
  });

  it('renders contact support button', () => {
    render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText(/contact support/i)).toBeTruthy();
  });

  it('renders FAQ contact section', () => {
    render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText(/contact support/i)).toBeTruthy();
  });

  it('renders back button', () => {
    render(<HelpCenterScreen navigation={mockNavigation} route={{} as any} />);
    const back = screen.queryByText(/←/) ?? screen.queryByText(/back/i);
    expect(back).toBeTruthy();
  });
});

// ─── PaymentMethodsScreen ──────────────────────────────────────────────────

import { PaymentMethodsScreen } from '@/screens/profile/PaymentMethodsScreen';

const mockProcessPayment = jest.fn().mockResolvedValue(undefined);
jest.mock('@/hooks/useRazorpay', () => ({
  useRazorpay: () => ({ processPayment: mockProcessPayment, isProcessing: false }),
}));

describe('PaymentMethodsScreen', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it('renders screen title', () => {
    render(<PaymentMethodsScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText(/payment methods/i)).toBeTruthy();
  });

  it('renders placeholder payment methods', () => {
    render(<PaymentMethodsScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText('user@upi')).toBeTruthy();
  });

  it('renders Add Payment Method button', () => {
    render(<PaymentMethodsScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText(/add payment method/i)).toBeTruthy();
  });

  it('calls processPayment on add button press', async () => {
    render(<PaymentMethodsScreen navigation={mockNavigation} route={{} as any} />);
    await act(async () => {
      fireEvent.press(screen.getByText(/add payment method/i));
    });
    await waitFor(() => expect(mockProcessPayment).toHaveBeenCalled());
  });
});

// ─── SubscriptionManagementScreen ─────────────────────────────────────────

import { SubscriptionManagementScreen } from '@/screens/profile/SubscriptionManagementScreen';

const mockHiredAgents = jest.fn();
jest.mock('@/hooks/useHiredAgents', () => ({
  useHiredAgents: () => mockHiredAgents(),
}));

describe('SubscriptionManagementScreen', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it('shows loading state', () => {
    mockHiredAgents.mockReturnValue({ isLoading: true, data: null, error: null, refetch: jest.fn() });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText(/loading/i)).toBeTruthy();
  });

  it('shows no active subscription when list is empty', async () => {
    mockHiredAgents.mockReturnValue({ isLoading: false, data: [], error: null, refetch: jest.fn() });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText(/no active subscription/i)).toBeTruthy();
    });
  });

  it('shows subscription details when active agent exists', async () => {
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: 'ha-1',
        status: 'active',
        duration: 'monthly',
        agent: { name: 'DMA Agent' },
        current_period_end: '2026-04-01T00:00:00Z',
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText(/DMA Agent|subscription/i)).toBeTruthy();
    });
  });

  it('renders back button', () => {
    mockHiredAgents.mockReturnValue({ isLoading: false, data: [], error: null, refetch: jest.fn() });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    const back = screen.queryByText(/←/) ?? screen.queryByText(/back/i);
    expect(back).toBeTruthy();
  });

  it('shows error state and calls refetch on Try Again', async () => {
    const mockRefetch = jest.fn();
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: null,
      error: { message: 'Load failed' },
      refetch: mockRefetch,
    });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText(/could not load subscription data/i)).toBeTruthy();
    });
    fireEvent.press(screen.getByText('Try Again'));
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('shows annual plan label for yearly duration', async () => {
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: 'ha-2',
        status: 'active',
        duration: 'yearly',
        agent: { name: 'Agent' },
        current_period_end: null,
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText(/Annual Plan/i)).toBeTruthy();
    });
  });

  it('shows quarterly plan label for quarterly duration', async () => {
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: 'ha-3',
        status: 'active',
        duration: 'quarterly',
        agent: { name: 'Agent' },
        current_period_end: null,
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText(/Quarterly Plan/i)).toBeTruthy();
    });
  });

  it('shows past_due warning in status text', async () => {
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: 'ha-4',
        status: 'past_due',
        duration: 'monthly',
        agent: { name: 'Agent' },
        current_period_end: null,
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText(/Past due/i)).toBeTruthy();
    });
  });

  it('shows trial end date when trial is active', async () => {
    const trialEnd = new Date(Date.now() + 5 * 24 * 3600 * 1000).toISOString();
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: 'ha-5',
        status: 'active',
        duration: 'monthly',
        agent: { name: 'Agent' },
        trial_status: 'active',
        trial_end_at: trialEnd,
        current_period_end: null,
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText(/Trial active/i)).toBeTruthy();
    });
  });

  it('shows renewal date when current_period_end is set', async () => {
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: 'ha-6',
        status: 'active',
        duration: 'monthly',
        agent: { name: 'Agent' },
        current_period_end: '2026-05-01T00:00:00Z',
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText(/Renews/i)).toBeTruthy();
    });
  });

  it('calls goBack when Back is pressed', () => {
    mockHiredAgents.mockReturnValue({ isLoading: false, data: [], error: null, refetch: jest.fn() });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(screen.getByText('← Back'));
    expect(mockGoBack).toHaveBeenCalled();
  });

  it('pressing Renew/Upgrade calls processPayment when canRenew is true', async () => {
    mockProcessPayment.mockResolvedValue(undefined);
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: 'ha-renew',
        status: 'active',
        duration: 'monthly',
        agent: { name: 'Agent' },
        current_period_end: null,
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByTestId('subscription-renew-cta')).toBeTruthy();
    });
    fireEvent.press(screen.getByTestId('subscription-renew-cta'));
    await waitFor(() => {
      expect(mockProcessPayment).toHaveBeenCalledWith(expect.objectContaining({
        agentId: 'ha-renew',
      }));
    });
  });

  it('does not call processPayment when hired_instance_id is missing', async () => {
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: undefined,
        status: 'active',
        duration: 'monthly',
        agent: { name: 'Agent' },
        current_period_end: null,
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<SubscriptionManagementScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByTestId('subscription-renew-cta')).toBeTruthy();
    });
    fireEvent.press(screen.getByTestId('subscription-renew-cta'));
    // canRenew is false when hired_instance_id is missing, so button is disabled
    expect(mockProcessPayment).not.toHaveBeenCalled();
  });
});
