module.exports = {
  signInAsync: jest.fn(() => Promise.resolve({
    user: 'mock-apple-user',
    email: 'test@apple.com',
    fullName: { givenName: 'Test', familyName: 'User' },
    identityToken: 'mock-identity-token',
    authorizationCode: 'mock-auth-code',
    realUserStatus: 1,
  })),
  isAvailableAsync: jest.fn(() => Promise.resolve(false)),
  AppleAuthenticationButton: 'AppleAuthenticationButton',
  AppleAuthenticationButtonType: { SIGN_IN: 0, CONTINUE: 1, SIGN_UP: 2 },
  AppleAuthenticationButtonStyle: { WHITE: 0, WHITE_OUTLINE: 1, BLACK: 2 },
  AppleAuthenticationScope: { FULL_NAME: 0, EMAIL: 1 },
};
