/**
 * Auth Navigator
 * 
 * Handles authentication flow screens (Sign In, Sign Up, OTP Verification)
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type { AuthStackParamList } from './types';
import { useTheme } from '../hooks/useTheme';

// Screens
import { SignInScreen } from '../screens/auth/SignInScreen';
import { SignUpScreen } from '../screens/auth/SignUpScreen';
import { OTPVerificationScreen } from '../screens/auth/OTPVerificationScreen';
import { useAuthStore } from '../store/authStore';

const Stack = createNativeStackNavigator<AuthStackParamList>();

export const AuthNavigator = () => {
  const { colors } = useTheme();
  const login = useAuthStore((state) => state.login);

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: {
          backgroundColor: colors.black,
        },
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen
        name="SignIn"
        component={SignInScreen}
        options={{
          title: 'Sign In',
        }}
      />
      <Stack.Screen
        name="SignUp"
        options={{
          title: 'Sign Up',
        }}
      >
        {(props) => (
          <SignUpScreen
            {...props}
            onSignInPress={() => props.navigation.navigate('SignIn')}
            onRegistrationSuccess={(registrationId, otpId) => {
              // Navigate to OTP verification
              // Note: We'll get channel and destinationMasked from the registration response
              props.navigation.navigate('OTPVerification', {
                registrationId,
                otpId,
                destinationMasked: 'your email', // TODO: Get from registration response
              });
            }}
          />
        )}
      </Stack.Screen>
      <Stack.Screen
        name="OTPVerification"
        options={{
          title: 'Verify OTP',
        }}
      >
        {(props) => (
          <OTPVerificationScreen
            {...props}
            registrationId={props.route.params.registrationId}
            otpId={props.route.params.otpId}
            channel={props.route.params.channel}
            destinationMasked={props.route.params.destinationMasked}
            onVerificationSuccess={() => {
              // Auth state will be handled by the service layer
              // Token is saved automatically by RegistrationService.verifyOTP
              // Just need to update auth store with user data
              // The RootNavigator will automatically switch to MainNavigator
              
              // For now, navigate will be handled by auth state change
              // The login action should be called from the OTPVerificationScreen
              // after successful verification
            }}
            onBack={() => props.navigation.goBack()}
          />
        )}
      </Stack.Screen>
    </Stack.Navigator>
  );
};
