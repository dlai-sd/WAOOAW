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
import { View, Text } from 'react-native';

// Import real screens
import { HomeScreen } from '../screens/home/HomeScreen';
import { DiscoverScreen } from '../screens/discover/DiscoverScreen';
import { AgentDetailScreen } from '../screens/discover/AgentDetailScreen';
import { MyAgentsScreen, TrialDashboardScreen } from '../screens/agents';
import { ProfileScreen } from '../screens/profile/ProfileScreen';

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
      <HomeStack.Screen name="AgentDetail" component={AgentDetailScreen} />
      <HomeStack.Screen name="TrialDashboard" component={TrialDashboardScreen} />
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
      <DiscoverStack.Screen name="AgentDetail" component={AgentDetailScreen} />
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
      <MyAgentsStack.Screen name="AgentDetail" component={AgentDetailScreen} />
      <MyAgentsStack.Screen name="TrialDashboard" component={TrialDashboardScreen} />
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
