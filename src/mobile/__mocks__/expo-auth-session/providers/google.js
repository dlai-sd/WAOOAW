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
  useAutoDiscovery: jest.fn(),
  discovery: {},
};
