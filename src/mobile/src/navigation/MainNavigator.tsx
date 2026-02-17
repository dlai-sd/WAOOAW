/**
 * Main Navigator
 * 
 * Bottom tab navigation for authenticated users
 * Includes Home, Discover, My Agents, and Profile tabs
 */

import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type {
  MainTabParamList,
  HomeStackParamList,
  DiscoverStackParamList,
  MyAgentsStackParamList,
  ProfileStackParamList,
} from './types';
import { useTheme } from '../hooks/useTheme';
import { View, Text, StyleSheet } from 'react-native';

// Placeholder screens (will be implemented in Story 1.12)
const PlaceholderScreen = ({ title }: { title: string }) => {
  const { colors, spacing, typography } = useTheme();
  
  return (
    <View style={[styles.container, { backgroundColor: colors.black }]}>
      <Text
        style={[
          styles.title,
          {
            color: colors.neonCyan,
            fontSize: 32,
            fontFamily: typography.fontFamily.display,
            marginBottom: spacing.lg,
          },
        ]}
      >
        WAOOAW
      </Text>
      <Text
        style={[
          styles.subtitle,
          {
            color: colors.textPrimary,
            fontSize: 20,
            fontFamily: typography.fontFamily.bodyBold,
          },
        ]}
      >
        {title}
      </Text>
      <Text
        style={[
          styles.description,
          {
            color: colors.textSecondary,
            fontSize: 14,
            fontFamily: typography.fontFamily.body,
            marginTop: spacing.md,
          },
        ]}
      >
        Coming in Story 1.12
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    textAlign: 'center',
  },
  subtitle: {
    textAlign: 'center',
  },
  description: {
    textAlign: 'center',
  },
});

// Temporary placeholder components
const HomeScreen = () => <PlaceholderScreen title="Home Screen" />;
const DiscoverScreen = () => <PlaceholderScreen title="Discover Agents" />;
const MyAgentsScreen = () => <PlaceholderScreen title="My Agents" />;
const ProfileScreen = () => <PlaceholderScreen title="Profile" />;

// Stack navigators for each tab
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const DiscoverStack = createNativeStackNavigator<DiscoverStackParamList>();
const MyAgentsStack = createNativeStackNavigator<MyAgentsStackParamList>();
const ProfileStack = createNativeStackNavigator<ProfileStackParamList>();

const Tab = createBottomTabNavigator<MainTabParamList>();

// Home Tab Navigator
const HomeNavigator = () => {
  const { colors } = useTheme();
  
  return (
    <HomeStack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.black },
      }}
    >
      <HomeStack.Screen name="Home" component={HomeScreen} />
    </HomeStack.Navigator>
  );
};

// Discover Tab Navigator
const DiscoverNavigator = () => {
  const { colors } = useTheme();
  
  return (
    <DiscoverStack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.black },
      }}
    >
      <DiscoverStack.Screen name="Discover" component={DiscoverScreen} />
    </DiscoverStack.Navigator>
  );
};

// My Agents Tab Navigator
const MyAgentsNavigator = () => {
  const { colors } = useTheme();
  
  return (
    <MyAgentsStack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.black },
      }}
    >
      <MyAgentsStack.Screen name="MyAgents" component={MyAgentsScreen} />
    </MyAgentsStack.Navigator>
  );
};

// Profile Tab Navigator
const ProfileNavigator = () => {
  const { colors } = useTheme();
  
  return (
    <ProfileStack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.black },
      }}
    >
      <ProfileStack.Screen name="Profile" component={ProfileScreen} />
    </ProfileStack.Navigator>
  );
};

/**
 * Main Navigator
 * Bottom tabs with stack navigators for each tab
 */
export const MainNavigator = () => {
  const { colors, spacing } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.black,
          borderTopColor: colors.textSecondary + '20', // 20% opacity
          borderTopWidth: 1,
          height: 60,
          paddingBottom: spacing.sm,
          paddingTop: spacing.xs,
        },
        tabBarActiveTintColor: colors.neonCyan,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeNavigator}
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => (
            <View
              style={{
                width: size,
                height: size,
                borderRadius: size / 2,
                backgroundColor: color + '20', // 20% opacity background
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <Text style={{ color, fontSize: size * 0.6, fontWeight: 'bold' }}>
                🏠
              </Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="DiscoverTab"
        component={DiscoverNavigator}
        options={{
          title: 'Discover',
          tabBarIcon: ({ color, size }) => (
            <View
              style={{
                width: size,
                height: size,
                borderRadius: size / 2,
                backgroundColor: color + '20',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <Text style={{ color, fontSize: size * 0.6, fontWeight: 'bold' }}>
                🔍
              </Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="MyAgentsTab"
        component={MyAgentsNavigator}
        options={{
          title: 'My Agents',
          tabBarIcon: ({ color, size }) => (
            <View
              style={{
                width: size,
                height: size,
                borderRadius: size / 2,
                backgroundColor: color + '20',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <Text style={{ color, fontSize: size * 0.6, fontWeight: 'bold' }}>
                🤖
              </Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileNavigator}
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <View
              style={{
                width: size,
                height: size,
                borderRadius: size / 2,
                backgroundColor: color + '20',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <Text style={{ color, fontSize: size * 0.6, fontWeight: 'bold' }}>
                👤
              </Text>
            </View>
          ),
        }}
      />
    </Tab.Navigator>
  );
};
