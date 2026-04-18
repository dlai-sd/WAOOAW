// Global test setup for jsdom environment
global.fetch = jest.fn();
global.alert = jest.fn();
global.confirm = jest.fn(() => true);

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch.mockReset();
});
