/**
 * Manual mock for @react-native-google-signin/google-signin
 * Used by Jest because the package ships only ESM (lib/module/) which
 * Jest's Node runtime cannot parse without Babel. This mock provides the
 * same API surface so any test that indirectly imports useGoogleAuth.ts
 * (e.g. App.test.tsx, SignInScreen.test.tsx) doesn't blow up.
 *
 * Tests that need to assert behaviour (useGoogleAuth.test.ts) override
 * this with their own jest.mock() call.
 */

const GoogleSignin = {
  configure: jest.fn(),
  hasPlayServices: jest.fn(() => Promise.resolve(true)),
  signIn: jest.fn(() => Promise.resolve({ type: 'cancelled' })),
  signOut: jest.fn(() => Promise.resolve(null)),
  revokeAccess: jest.fn(() => Promise.resolve(null)),
  hasPreviousSignIn: jest.fn(() => false),
  getCurrentUser: jest.fn(() => null),
  getTokens: jest.fn(() => Promise.resolve({ idToken: '', accessToken: '' })),
};

const statusCodes = {
  SIGN_IN_CANCELLED: 'SIGN_IN_CANCELLED',
  IN_PROGRESS: 'IN_PROGRESS',
  PLAY_SERVICES_NOT_AVAILABLE: 'PLAY_SERVICES_NOT_AVAILABLE',
  SIGN_IN_REQUIRED: 'SIGN_IN_REQUIRED',
};

const isSuccessResponse = (r) => r && r.type === 'success';
const isCancelledResponse = (r) => r && r.type === 'cancelled';
const isNoSavedCredentialFoundResponse = (r) => r && r.type === 'noSavedCredentialFound';
const isErrorWithCode = (e) => e != null && typeof e.code === 'string';

module.exports = {
  GoogleSignin,
  statusCodes,
  isSuccessResponse,
  isCancelledResponse,
  isNoSavedCredentialFoundResponse,
  isErrorWithCode,
  GoogleSigninButton: 'GoogleSigninButton',
};
