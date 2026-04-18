module.exports = {
  useAuthRequest: jest.fn(() => [null, null, jest.fn()]),
  makeRedirectUri: jest.fn(() => 'https://mock-redirect-uri'),
  AuthSession: {
    ResponseType: {
      IdToken: 'id_token',
      Token: 'token',
      Code: 'code',
    },
  },
  ResponseType: {
    IdToken: 'id_token',
    Token: 'token',
    Code: 'code',
  },
};
