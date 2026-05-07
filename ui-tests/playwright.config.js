/**
 * Configuration for Playwright using default from @jupyterlab/galata
 */
const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  ...baseConfig,
  webServer: {
    command: 'jlpm start',
    url: 'http://localhost:8888/lab',
    env: {
      MAAP_API_HOST: 'https://api.dit.maap-project.org/api/',
      MAAP_PGT: 'PGT-my_test_token'
    },
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI
  }
};
