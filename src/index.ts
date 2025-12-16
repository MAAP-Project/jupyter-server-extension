import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { PageConfig } from '@jupyterlab/coreutils';
import { ISettingRegistry } from '@jupyterlab/settingregistry';

const MAAP_JUPYTER_SERVER_EXTENSION_ID = 'maap-jupyter-server-extension:plugin';

interface IMaapParams {
  maapApiUrl: string;
  maapToken: string;
}

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
    fetch(`${baseUrl}maap-jupyter-server-extension/get-maap-params`)
      .then(response => {
        if (!response.ok) {
          return response.text().then(data => {
            return Promise.reject(
              new Error(`${response.status} ${response.statusText}: ${data}`)
            );
          });
        }
        return response.json();
      })
      .then(async (maapParams: IMaapParams) => {
        // Update extension settings with the fetched MAAP environment variables
        try {
          await Promise.all([
            serverExtSettings.set('maapApiUrl', maapParams.maapApiUrl),
            serverExtSettings.set('maapToken', maapParams.maapToken)
          ]);
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
