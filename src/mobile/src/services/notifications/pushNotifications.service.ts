/**
 * Push Notification Service (MOBILE-FUNC-1 S8b)
 *
 * Registers the device's Expo push token with the Plant Backend so the
 * server can send targeted push notifications.
 *
 * Design decisions:
 * - fire-and-forget safe: this function never throws — errors are swallowed
 *   so callers can safely do `registerPushToken().catch(() => {})` without
 *   risk of crashing the login flow.
 * - web guard: expo-notifications is not supported on web; early-return prevents
 *   a runtime crash on web/browser targets.
 * - permission request: requests permissions automatically on first call.
 *   If the user denies, the function returns silently.
 */

import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import apiClient from '../../lib/apiClient';

/**
 * Request push notification permissions and register the Expo push token
 * with the backend endpoint POST /api/v1/customers/fcm-token.
 *
 * Safe to call from sign-in flows — never throws.
 */
export const registerPushToken = async (): Promise<void> => {
  if (process.env.NODE_ENV === 'test') return;

  // expo-notifications is unsupported on web
  if (Platform.OS === 'web') return;

  try {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    // User denied push permissions — do not proceed
    if (finalStatus !== 'granted') return;

    const tokenData = await Notifications.getExpoPushTokenAsync();
    const token = tokenData.data;

    if (!token) return;

    await apiClient.post('/api/v1/customers/fcm-token', { token });
  } catch {
    // Intentionally swallowed — push token failure must never block login
  }
};
