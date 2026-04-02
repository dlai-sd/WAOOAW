/**
 * Main Navigator
 *
 * Bottom tab navigation for authenticated users
 * Includes Home, Discover, My Agents, and Profile tabs
 */

import React from "react";
import { Ionicons } from "@expo/vector-icons";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import type {
  MainTabParamList,
  HomeStackParamList,
  DiscoverStackParamList,
  MyAgentsStackParamList,
  ProfileStackParamList,
} from "./types";
import { useTheme } from "../hooks/useTheme";
import { useAgentsNeedingSetup } from "../hooks/useHiredAgents";
import { useSafeAreaInsets } from "react-native-safe-area-context";

// Import real screens
import { HomeScreen } from "../screens/home/HomeScreen";
import { DiscoverScreen } from "../screens/discover/DiscoverScreen";
import { AgentDetailScreen } from "../screens/discover/AgentDetailScreen";
import { HireWizardScreen } from "../screens/hire/HireWizardScreen";
import { MyAgentsScreen, TrialDashboardScreen, ActiveTrialsListScreen, HiredAgentsListScreen, AgentOperationsScreen } from "../screens/agents";
import { ProfileScreen } from "../screens/profile/ProfileScreen";
import { EditProfileScreen } from "../screens/profile/EditProfileScreen";
import { SettingsScreen, NotificationsScreen, HelpCenterScreen, PrivacyPolicyScreen, TermsOfServiceScreen, PaymentMethodsScreen, SubscriptionManagementScreen } from "../screens/profile";

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
      <HomeStack.Screen
        name="TrialDashboard"
        component={TrialDashboardScreen}
      />
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
      <DiscoverStack.Screen name="HireWizard" component={HireWizardScreen} />
      <DiscoverStack.Screen name="SearchResults" component={require('../screens/discover/SearchResultsScreen').default} />
      <DiscoverStack.Screen name="FilterAgents" component={require('../screens/discover/FilterAgentsScreen').default} />
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
      <MyAgentsStack.Screen
        name="TrialDashboard"
        component={TrialDashboardScreen}
      />
      <MyAgentsStack.Screen name="ActiveTrialsList" component={ActiveTrialsListScreen} />
      <MyAgentsStack.Screen name="HiredAgentsList" component={HiredAgentsListScreen} />
      <MyAgentsStack.Screen name="AgentOperations" component={AgentOperationsScreen} />
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
      <ProfileStack.Screen name="EditProfile" component={EditProfileScreen} />
      <ProfileStack.Screen name="Settings" component={SettingsScreen} />
      <ProfileStack.Screen name="Notifications" component={NotificationsScreen} />
      <ProfileStack.Screen name="HelpCenter" component={HelpCenterScreen} />
      <ProfileStack.Screen name="PrivacyPolicy" component={PrivacyPolicyScreen} />
      <ProfileStack.Screen name="TermsOfService" component={TermsOfServiceScreen} />
      <ProfileStack.Screen name="PaymentMethods" component={PaymentMethodsScreen} />
      <ProfileStack.Screen name="SubscriptionManagement" component={SubscriptionManagementScreen} />
    </ProfileStack.Navigator>
  );
};

/**
 * Main Navigator
 * Bottom tabs with stack navigators for each tab
 */
export const MainNavigator = () => {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const { data: agentsNeedingSetup } = useAgentsNeedingSetup();
  const needsSetupCount = agentsNeedingSetup?.length ?? 0;

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.black,
          borderTopColor: colors.textSecondary + "20",
          borderTopWidth: 1,
          height: 60 + insets.bottom,
          paddingBottom: Math.max(12, insets.bottom),
          paddingTop: 8,
        },
        tabBarActiveTintColor: colors.neonCyan,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "600",
        },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeNavigator}
        options={{
          title: "Today",
          tabBarButtonTestID: 'mobile-home-tab',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="DiscoverTab"
        component={DiscoverNavigator}
        options={{
          title: "Discover",
          tabBarButtonTestID: 'mobile-discover-tab',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="search" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="MyAgentsTab"
        component={MyAgentsNavigator}
        options={{
          title: "Ops",
          tabBarButtonTestID: 'mobile-my-agents-tab',
          tabBarBadge: needsSetupCount > 0 ? needsSetupCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: "#ef4444",
            fontSize: 10,
            fontWeight: "700",
          },
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="grid" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileNavigator}
        options={{
          title: "Profile",
          tabBarButtonTestID: 'mobile-profile-tab',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};
