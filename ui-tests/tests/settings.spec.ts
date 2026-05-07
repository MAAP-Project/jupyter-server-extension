import { expect, test } from '@jupyterlab/galata';

const PLUGIN_ID = 'maap-jupyter-server-extension:plugin';
const MAAP_API_URL = 'https://api.dit.maap-project.org/api/';
const MAAP_PGT_TOKEN = 'PGT-my_test_token';
const MAAP_SETTINGS = 'MAAP Settings';

test.describe('MAAP Jupyter Server Extension Settings Test', () => {
  test.use({ ...test.use });

  test('Should retrieve MAAP params from environment then update JupyterLab settings', async ({
    page
  }) => {
    // Wait for JupyterLab to be fully loaded
    await page.waitForSelector('#jupyterlab-splash', { state: 'detached' });

    // Call the get-maap-params endpoint
    const response = await page.request.get(
      '/maap-jupyter-server-extension/get-maap-params'
    );
    expect(response.ok()).toBeTruthy();

    // Confirm expected environment variables were retrieved
    const body = await response.json();
    expect(body).toEqual({
      maapApiUrl: MAAP_API_URL,
      maapToken: MAAP_PGT_TOKEN,
      defaultAppImage: '',
      currentAppImage: '',
      workspaceBucket: ''
    });

    // Set retrieved environment variables to the extension settings
    const resp = await page.request.put(`/lab/api/settings/${PLUGIN_ID}`, {
      data: {
        raw: JSON.stringify({
          maapApiUrl: MAAP_API_URL,
          maapToken: MAAP_PGT_TOKEN
        })
      }
    });

    if (!resp.ok()) {
      const body = await resp.text();
      throw new Error(`Request failed ${resp.status()}: ${body}`);
    }

    // Retrieve the settings to verify variables were correctly set
    const getSettingsResp = await page.request.get(
      `/lab/api/settings/${PLUGIN_ID}`
    );
    expect(getSettingsResp.ok()).toBeTruthy();
    const settingsJson = await getSettingsResp.json();
    expect(settingsJson.settings).toEqual({
      maapApiUrl: MAAP_API_URL,
      maapToken: MAAP_PGT_TOKEN
    });
  });

  test('User manually updates MAAP settings via Settings Editor UI', async ({
    page
  }) => {
    await page.waitForSelector('#jupyterlab-splash', { state: 'detached' });

    const menuBar = page.locator('.lm-MenuBar');
    await expect(menuBar).toBeVisible({ timeout: 30_000 });

    // Click Settings ONCE to open dropdown
    await menuBar.getByText('Settings', { exact: true }).click();

    // JupyterLab/Lumino menus render in an overlay with class .lm-Menu
    const openMenu = page
      .locator('.lm-Menu')
      .filter({ has: page.getByText('Settings Editor') });
    await expect(openMenu).toBeVisible({ timeout: 10_000 });

    // Click the item inside the open menu (more reliable than page.getByRole(menuitem...))
    await openMenu.getByText(/Settings Editor/i).click();

    // Search for MAAP settings
    const searchBox = page.getByPlaceholder('Search settings…').nth(1);
    await expect(searchBox).toBeVisible({ timeout: 10_000 });
    await searchBox.fill(MAAP_SETTINGS);

    // Get handles on the input boxes
    const apiUrlInput = page.locator(
      '[id="jp-SettingsEditor-maap-jupyter-server-extension:plugin_maapApiUrl"]'
    );
    const tokenInput = page.locator(
      '[id="jp-SettingsEditor-maap-jupyter-server-extension:plugin_maapToken"]'
    );
    await expect(apiUrlInput).toBeVisible({ timeout: 10_000 });
    await expect(tokenInput).toBeVisible({ timeout: 10_000 });

    // Fill the setting inputs
    await apiUrlInput.fill(MAAP_API_URL);
    await tokenInput.fill(MAAP_PGT_TOKEN);

    // Retrieve settings to verify they were successfully set
    const getSettingsResp = await page.request.get(
      `/lab/api/settings/${PLUGIN_ID}`
    );
    expect(getSettingsResp.ok()).toBeTruthy();

    const settingsJson = await getSettingsResp.json();
    expect(settingsJson.settings).toEqual({
      maapApiUrl: MAAP_API_URL,
      maapToken: MAAP_PGT_TOKEN
    });
  });
});
