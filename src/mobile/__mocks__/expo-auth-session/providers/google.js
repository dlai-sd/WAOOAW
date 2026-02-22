/**
 * Mock for expo-auth-session/providers/google
 */

module.exports = {
  useAuthRequest: jest.fn(() => [
    // request object
    {
      url: 'https://accounts.google.com/o/oauth2/v2/auth',
      codeVerifier: 'mock-code-verifier',
      codeChallenge: 'mock-code-challenge',
      state: 'mock-state',
    },
    // response object
    null,
    // promptAsync function
    jest.fn().mockResolvedValue(undefined),
  ]),
  // The app uses useIdTokenAuthRequest to get an id_token on web.
  // For tests, returning the same tuple shape is sufficient.
  useIdTokenAuthRequest: jest.fn(() => [
    {
      url: 'https://accounts.google.com/o/oauth2/v2/auth',
      codeVerifier: 'mock-code-verifier',
      codeChallenge: 'mock-code-challenge',
      state: 'mock-state',
    },
    null,
    jest.fn().mockResolvedValue(undefined),
  ]),
  useAutoDiscovery: jest.fn(),
  discovery: {},
};
