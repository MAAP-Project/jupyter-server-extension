import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { PageConfig } from '@jupyterlab/coreutils';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ServerConnection } from '@jupyterlab/services';

const MAAP_JUPYTER_SERVER_EXTENSION_ID = 'maap-jupyter-server-extension:plugin';

interface IMaapParams {
  maapApiUrl: string;
  maapToken: string;
  defaultAppImage: string;
  currentAppImage: string;
  workspaceBucket: string;
}

const MAAP_PARAM_KEYS: (keyof IMaapParams)[] = [
  'maapApiUrl',
  'maapToken',
  'defaultAppImage',
  'currentAppImage',
  'workspaceBucket'
];

const plugin: JupyterFrontEndPlugin<void> = {
  id: MAAP_JUPYTER_SERVER_EXTENSION_ID,
  autoStart: true,
  requires: [ISettingRegistry],
  activate: async (app: JupyterFrontEnd, settings: ISettingRegistry) => {
    // Load settings for this extension
    const serverExtSettings = await settings.load(
      MAAP_JUPYTER_SERVER_EXTENSION_ID
    );
    const baseUrl = PageConfig.getBaseUrl();

    // Add listener to detect changes in extension settings
    // serverExtSettings.changed.connect(() => {
    //   const newUrl = serverExtSettings.get('maapApiUrl').composite as string;
    //   const newToken = serverExtSettings.get('maapToken').composite as string;
    //   console.log('MAAP API URL updated by user: ', newUrl, newToken);
    // });

    // Retrieve MAAP variables from environment and add them to the jupyter MAAP settings
    const serverSettings = ServerConnection.makeSettings();
    ServerConnection.makeRequest(
      `${baseUrl}maap-jupyter-server-extension/get-maap-params`,
      { method: 'GET' },
      serverSettings
    )
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} ${response.statusText}`);
        }
        return response.json();
      })
      .then(async (maapParams: Partial<IMaapParams>) => {
        // Only override settings the environment supplied a non-empty value for;
        // everything else keeps its existing (saved or default) setting
        const envKeys: (keyof IMaapParams)[] = [];
        const keptKeys: (keyof IMaapParams)[] = [];
        const updates: Promise<void>[] = [];
        for (const key of MAAP_PARAM_KEYS) {
          const value = maapParams[key];
          if (typeof value === 'string' && value.trim() !== '') {
            envKeys.push(key);
            updates.push(serverExtSettings.set(key, value.trim()));
          } else {
            keptKeys.push(key);
          }
        }

        try {
          await Promise.all(updates);
          console.log('Successfully updated MAAP extension settings.');
        } catch (error) {
          console.error('Failed to update MAAP extension settings: ', error);
        }
      })
      .catch(error => {
        console.error('Failed to fetch MAAP parameters from server: ', error);
      });
  }
};

export default plugin;
