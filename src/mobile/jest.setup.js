// Add custom jest matchers from @testing-library/react-native
// require('@testing-library/react-native/extend-expect');

global.__DEV__ = true;

// Mock expo modules
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

jest.mock('expo-auth-session', () => ({
  useAuthRequest: jest.fn(),
  makeRedirectUri: jest.fn(),
}));

jest.mock('expo-crypto', () => ({
  randomUUID: jest.fn(() => 'test-uuid'),
}));

jest.mock('expo-font', () => ({
  loadAsync: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('expo-status-bar', () => ({
  StatusBar: 'StatusBar',
}));

jest.mock('expo-speech', () => ({
  speak: jest.fn(),
  stop: jest.fn().mockResolvedValue(undefined),
  pause: jest.fn().mockResolvedValue(undefined),
  resume: jest.fn().mockResolvedValue(undefined),
  getAvailableVoicesAsync: jest.fn().mockResolvedValue([]),
}));

jest.mock('@react-navigation/native', () => ({
  NavigationContainer: ({ children }) => children,
  useNavigation: () => ({
    navigate: jest.fn(),
    goBack: jest.fn(),
    dispatch: jest.fn(),
    setOptions: jest.fn(),
  }),
  useRoute: () => ({ params: {} }),
}));

jest.mock('@react-navigation/native-stack', () => ({
  createNativeStackNavigator: () => ({
    Navigator: ({ children }) => {
      const ReactLib = require('react');
      const screens = ReactLib.Children.toArray(children);
      return screens[0] || null;
    },
    Screen: ({ children, component: Component }) => {
      if (typeof children === 'function') {
        return children({
          navigation: {
            navigate: jest.fn(),
            goBack: jest.fn(),
            dispatch: jest.fn(),
          },
          route: { params: {} },
        });
      }

      if (Component) {
        const ReactLib = require('react');
        return ReactLib.createElement(Component, {
          navigation: {
            navigate: jest.fn(),
            goBack: jest.fn(),
            dispatch: jest.fn(),
          },
          route: { params: {} },
        });
      }

      return children || null;
    },
  }),
}));

jest.mock('@react-navigation/bottom-tabs', () => ({
  createBottomTabNavigator: () => ({
    Navigator: ({ children }) => {
      const ReactLib = require('react');
      const screens = ReactLib.Children.toArray(children);
      return screens[0] || null;
    },
    Screen: ({ children, component: Component }) => {
      if (typeof children === 'function') {
        return children({
          navigation: {
            navigate: jest.fn(),
            goBack: jest.fn(),
            dispatch: jest.fn(),
          },
          route: { params: {} },
        });
      }

      if (Component) {
        const ReactLib = require('react');
        return ReactLib.createElement(Component, {
          navigation: {
            navigate: jest.fn(),
            goBack: jest.fn(),
            dispatch: jest.fn(),
          },
          route: { params: {} },
        });
      }

      return children || null;
    },
  }),
}));

jest.mock('@shopify/flash-list', () => {
  const React = require('react');

  return {
    FlashList: ({ data = [], renderItem, ListEmptyComponent }) => {
      if (Array.isArray(data) && data.length > 0 && typeof renderItem === 'function') {
        return React.createElement(
          React.Fragment,
          null,
          ...data.map((item, index) => renderItem({ item, index }))
        );
      }

      if (ListEmptyComponent) {
        if (typeof ListEmptyComponent === 'function') {
          return React.createElement(ListEmptyComponent);
        }
        return ListEmptyComponent;
      }

      return null;
    },
  };
});

// Mock React Native
jest.mock('react-native', () => {
  const React = require('react');

  const FlatList = ({ data = [], renderItem, ListEmptyComponent, ...props }) => {
    if (Array.isArray(data) && data.length > 0 && typeof renderItem === 'function') {
      return React.createElement(
        React.Fragment,
        null,
        ...data.map((item, index) => renderItem({ item, index }))
      );
    }

    if (ListEmptyComponent) {
      if (typeof ListEmptyComponent === 'function') {
        return React.createElement(ListEmptyComponent);
      }
      return ListEmptyComponent;
    }

    return React.createElement('FlatList', props);
  };

  return ({
  Platform: {
    OS: 'ios',
    select: jest.fn((obj) => obj.ios || obj.default),
  },
  useColorScheme: jest.fn(() => 'dark'),
  StyleSheet: {
    create: jest.fn((styles) => styles),
    flatten: jest.fn((styles) => styles),
  },
  Alert: {
    alert: jest.fn(),
  },
  ActivityIndicator: 'ActivityIndicator',
  Image: 'Image',
  Text: 'Text',
  TextInput: 'TextInput',
  TouchableOpacity: 'TouchableOpacity',
  TouchableWithoutFeedback: 'TouchableWithoutFeedback',
  View: 'View',
  ScrollView: 'ScrollView',
  SafeAreaView: 'SafeAreaView',
  Modal: 'Modal',
  KeyboardAvoidingView: 'KeyboardAvoidingView',
  RefreshControl: 'RefreshControl',
  FlatList,
  Animated: {
    Value: jest.fn().mockImplementation((value) => ({
      _value: value,
      setValue: jest.fn(),
      interpolate: jest.fn(() => '0deg'),
    })),
    timing: jest.fn(() => ({ start: jest.fn((callback) => callback?.()) })),
    sequence: jest.fn(() => ({ start: jest.fn() })),
    loop: jest.fn(() => ({ start: jest.fn() })),
  },
  Dimensions: {
    get: jest.fn(() => ({ width: 375, height: 812 })),
  },
  });
});

jest.mock('@react-native-community/netinfo', () => ({
  addEventListener: jest.fn(() => jest.fn()),
  fetch: jest.fn().mockResolvedValue({
    isConnected: true,
    isInternetReachable: true,
    type: 'wifi',
  }),
  useNetInfo: jest.fn(() => ({
    isConnected: true,
    isInternetReachable: true,
    type: 'wifi',
  })),
}));

// Mock React Native Safe Area Context
jest.mock('react-native-safe-area-context', () => ({
  SafeAreaView: 'SafeAreaView',
}));

// Mock React Native modules
// jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');
