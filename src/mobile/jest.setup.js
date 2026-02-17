// Add custom jest matchers from @testing-library/react-native
// require('@testing-library/react-native/extend-expect');

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

// Mock React Native
jest.mock('react-native', () => ({
  Platform: {
    OS: 'ios',
    select: jest.fn((obj) => obj.ios || obj.default),
  },
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
  TouchableOpacity: 'TouchableOpacity',
  View: 'View',
  ScrollView: 'ScrollView',
  SafeAreaView: 'SafeAreaView',
  KeyboardAvoidingView: 'KeyboardAvoidingView',
  RefreshControl: 'RefreshControl',
  FlatList: 'FlatList',
  Dimensions: {
    get: jest.fn(() => ({ width: 375, height: 812 })),
  },
}));

// Mock React Native Safe Area Context
jest.mock('react-native-safe-area-context', () => ({
  SafeAreaView: 'SafeAreaView',
}));

// Mock React Native modules
// jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');
