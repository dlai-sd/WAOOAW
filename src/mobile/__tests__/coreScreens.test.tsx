/**
 * Core Screens Tests
 * 
 * Tests for HomeScreen, DiscoverScreen, MyAgentsScreen, ProfileScreen
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { HomeScreen } from '../src/screens/home/HomeScreen';
import { DiscoverScreen } from '../src/screens/discover/DiscoverScreen';
import { MyAgentsScreen } from '../src/screens/agents/MyAgentsScreen';
import { ProfileScreen } from '../src/screens/profile/ProfileScreen';
import { useAuthStore } from '../src/store/authStore';

// Mock hooks
jest.mock('../src/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      neonCyan: '#00f2fe',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      card: '#18181b',
      error: '#ef4444',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      xxl: 48,
      screenPadding: 20,
    },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk_700Bold',
        body: 'Inter_400Regular',
        bodyBold: 'Inter_600SemiBold',
      },
    },
  }),
}));

jest.mock('../src/store/authStore');

// Mock Alert
jest.spyOn(Alert, 'alert').mockImplementation(() => {});

describe('Core Screens', () => {
  const mockUser = {
    customer_id: 'CUST-123',
    email: 'test@example.com',
    full_name: 'Test User',
    phone: '+919876543210',
    business_name: 'ACME Inc',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuthStore as unknown as jest.Mock).mockImplementation((selector) => {
      const state = {
        user: mockUser,
        logout: jest.fn(),
      };
      return selector ? selector(state) : state;
    });
  });

  describe('HomeScreen', () => {
    it('should render correctly', () => {
      const { getByText } = render(<HomeScreen />);

      expect(getByText('Good Morning')).toBeTruthy(); // Or Good Afternoon/Evening
      expect(getByText('Test User')).toBeTruthy();
      expect(getByText('WAOOAW')).toBeTruthy();
      expect(getByText('Agents Earn Your Business')).toBeTruthy();
    });

    it('should display user full name', () => {
      const { getByText } = render(<HomeScreen />);

      expect(getByText('Test User')).toBeTruthy();
    });

    it('should show correct greeting based on time', () => {
      const { getByText } = render(<HomeScreen />);

      // Should show one of the greetings
      const hasGreeting =
        getByText(/Good Morning/i) ||
        getByText(/Good Afternoon/i) ||
        getByText(/Good Evening/i);

      expect(hasGreeting).toBeTruthy();
    });

    it('should display quick action cards', () => {
      const { getByText } = render(<HomeScreen />);

      expect(getByText('Quick Actions')).toBeTruthy();
      expect(getByText('Discover Agents')).toBeTruthy();
      expect(getByText('Start Trial')).toBeTruthy();
    });

    it('should display activity stats', () => {
      const { getByText, getAllByText } = render(<HomeScreen />);

      expect(getByText('Your Activity')).toBeTruthy();
      expect(getByText('Active Trials')).toBeTruthy();
      expect(getByText('Hired Agents')).toBeTruthy();
      expect(getAllByText('0').length).toBeGreaterThanOrEqual(2);
    });

    it('should display featured agents placeholder', () => {
      const { getByText } = render(<HomeScreen />);

      expect(getByText('Featured Agents')).toBeTruthy();
      expect(getByText('Featured agents will appear here')).toBeTruthy();
      expect(getByText('Coming in Story 2.2')).toBeTruthy();
    });
  });

  describe('DiscoverScreen', () => {
    it('should render correctly', () => {
      const { getByText, getByPlaceholderText } = render(<DiscoverScreen />);

      expect(getByText('Discover Agents')).toBeTruthy();
      expect(getByPlaceholderText('Search agents by skill, industry...')).toBeTruthy();
    });

    it('should handle search input', () => {
      const { getByPlaceholderText, getByText } = render(<DiscoverScreen />);

      const searchInput = getByPlaceholderText('Search agents by skill, industry...');
      fireEvent.changeText(searchInput, 'marketing');

      expect(searchInput.props.value).toBe('marketing');
    });

    it('should clear search query', () => {
      const { getByPlaceholderText, getByText } = render(<DiscoverScreen />);

      const searchInput = getByPlaceholderText('Search agents by skill, industry...');
      fireEvent.changeText(searchInput, 'test');

      const clearButton = getByText('✕');
      fireEvent.press(clearButton);

      expect(searchInput.props.value).toBe('');
    });

    it('should display industry filters', () => {
      const { getByText } = render(<DiscoverScreen />);

      expect(getByText('Marketing')).toBeTruthy();
      expect(getByText('Education')).toBeTruthy();
      expect(getByText('Sales')).toBeTruthy();
      expect(getByText('+ More Filters')).toBeTruthy();
    });

    it('should toggle industry filter', () => {
      const { getByText } = render(<DiscoverScreen />);

      const marketingFilter = getByText('Marketing');
      fireEvent.press(marketingFilter);

      expect(getByText('Showing Marketing agents')).toBeTruthy();

      // Toggle off
      fireEvent.press(marketingFilter);
      expect(getByText('Showing all agents')).toBeTruthy();
    });

    it('should display industry breakdown', () => {
      const { getByText } = render(<DiscoverScreen />);

      expect(getByText('Browse by Industry')).toBeTruthy();
      expect(getByText('7 agents available')).toBeTruthy(); // Marketing
      expect(getByText('5 agents available')).toBeTruthy(); // Sales
    });

    it('should display placeholder for agent list', () => {
      const { getByText } = render(<DiscoverScreen />);

      expect(getByText('19+ AI Agents Ready to Work')).toBeTruthy();
      expect(getByText('Agent cards and details will appear here')).toBeTruthy();
      expect(getByText('Coming in Story 2.2-2.3')).toBeTruthy();
    });
  });

  describe('MyAgentsScreen', () => {
    it('should render correctly', () => {
      const { getByText } = render(<MyAgentsScreen />);

      expect(getByText('My Agents')).toBeTruthy();
      expect(getByText('Active Trials (0)')).toBeTruthy();
      expect(getByText('Hired (0)')).toBeTruthy();
    });

    it('should switch between trials and hired tabs', () => {
      const { getByText } = render(<MyAgentsScreen />);

      const trialsTab = getByText('Active Trials (0)');
      const hiredTab = getByText('Hired (0)');

      // Start with trials tab
      expect(getByText('No Active Trials')).toBeTruthy();

      // Switch to hired tab
      fireEvent.press(hiredTab);
      expect(getByText('No Hired Agents Yet')).toBeTruthy();

      // Switch back to trials
      fireEvent.press(trialsTab);
      expect(getByText('No Active Trials')).toBeTruthy();
    });

    it('should display empty state for trials', () => {
      const { getByText } = render(<MyAgentsScreen />);

      expect(getByText('No Active Trials')).toBeTruthy();
      expect(getByText('Start a 7-day trial to see results before hiring')).toBeTruthy();
      expect(getByText('Discover Agents')).toBeTruthy();
    });

    it('should display empty state for hired agents', () => {
      const { getByText } = render(<MyAgentsScreen />);

      const hiredTab = getByText('Hired (0)');
      fireEvent.press(hiredTab);

      expect(getByText('No Hired Agents Yet')).toBeTruthy();
      expect(getByText('Hire agents after successful trials or direct from discovery')).toBeTruthy();
    });

    it('should display how it works section', () => {
      const { getByText } = render(<MyAgentsScreen />);

      expect(getByText('How It Works')).toBeTruthy();
      expect(getByText('Start a 7-Day Trial')).toBeTruthy();
      expect(getByText('Keep All Deliverables')).toBeTruthy();
      expect(getByText('Hire What Works')).toBeTruthy();
    });
  });

  describe('ProfileScreen', () => {
    const mockLogout = jest.fn();

    beforeEach(() => {
      (useAuthStore as unknown as jest.Mock).mockImplementation((selector) => {
        const state = {
          user: mockUser,
          logout: mockLogout,
        };
        return selector ? selector(state) : state;
      });
    });

    it('should render correctly', () => {
      const { getByText } = render(<ProfileScreen />);

      expect(getByText('Profile')).toBeTruthy();
      expect(getByText('Test User')).toBeTruthy();
      expect(getByText('test@example.com')).toBeTruthy();
      expect(getByText('+919876543210')).toBeTruthy();
    });

    it('should display user business name badge', () => {
      const { getByText } = render(<ProfileScreen />);

      expect(getByText(/ACME Inc/)).toBeTruthy();
    });

    it('should display menu sections', () => {
      const { getByText } = render(<ProfileScreen />);

      // Account section
      expect(getByText('Edit Profile')).toBeTruthy();
      expect(getByText('Payment Methods')).toBeTruthy();
      expect(getByText('Subscription Management')).toBeTruthy();

      // Preferences section
      expect(getByText('Notifications')).toBeTruthy();
      expect(getByText('Settings')).toBeTruthy();

      // Support section
      expect(getByText('Help Center')).toBeTruthy();
      expect(getByText('Privacy Policy')).toBeTruthy();
      expect(getByText('Terms of Service')).toBeTruthy();
    });

    it('should display app info', () => {
      const { getByText } = render(<ProfileScreen />);

      expect(getByText('WAOOAW')).toBeTruthy();
      expect(getByText('Version 1.0.0')).toBeTruthy();
      expect(getByText('Agents Earn Your Business')).toBeTruthy();
    });

    it('should show logout confirmation dialog', () => {
      const { getByText } = render(<ProfileScreen />);

      const logoutButton = getByText('Sign Out');
      fireEvent.press(logoutButton);

      expect(Alert.alert).toHaveBeenCalledWith(
        'Sign Out',
        'Are you sure you want to sign out?',
        expect.any(Array),
        expect.any(Object)
      );
    });

    it('should call logout function when confirmed', () => {
      (Alert.alert as jest.Mock).mockImplementation((title, message, buttons) => {
        // Simulate pressing "Sign Out" button
        buttons[1].onPress();
      });

      const { getByText } = render(<ProfileScreen />);

      const logoutButton = getByText('Sign Out');
      fireEvent.press(logoutButton);

      expect(mockLogout).toHaveBeenCalled();
    });

    it('should not call logout when cancelled', () => {
      mockLogout.mockClear();

      (Alert.alert as jest.Mock).mockImplementation((title, message, buttons) => {
        // Simulate pressing "Cancel" button
        if (buttons[0].onPress) buttons[0].onPress();
      });

      const { getByText } = render(<ProfileScreen />);

      const logoutButton = getByText('Sign Out');
      fireEvent.press(logoutButton);

      expect(mockLogout).not.toHaveBeenCalled();
    });
  });
});
