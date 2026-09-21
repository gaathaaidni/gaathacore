module.exports = {
  testDir: '.',
  testMatch: /gaatha_e2e\.spec\.js$/,
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: 'http://localhost:5000',
    headless: true,
    viewport: { width: 1440, height: 1100 },
    ignoreHTTPSErrors: true,
  },
};
