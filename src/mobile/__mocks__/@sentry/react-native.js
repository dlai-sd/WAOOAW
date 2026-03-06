module.exports = {
  init: jest.fn(),
  captureException: jest.fn(),
  captureMessage: jest.fn(),
  setUser: jest.fn(),
  setTag: jest.fn(),
  setContext: jest.fn(),
  addBreadcrumb: jest.fn(),
  reactNativeTracingIntegration: jest.fn(() => ({})),
  wrap: jest.fn((component) => component),
  withScope: jest.fn(),
  configureScope: jest.fn(),
};
