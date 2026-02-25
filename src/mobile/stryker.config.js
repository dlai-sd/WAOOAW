/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
module.exports = {
  testRunner: 'jest',
  mutate: [
    'src/services/auth.service.ts',
    'src/services/tokenManager.service.ts',
  ],
  reporters: ['html', 'clear-text', 'progress'],
  htmlReporter: {
    fileName: '../../tests/mutation/reports/mobile-stryker/index.html',
  },
  coverageAnalysis: 'perTest',
  jest: {
    configFile: 'jest.config.js',
  },
};
