import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { PageConfig } from '@jupyterlab/coreutils';
import { ISettingRegistry } from '@jupyterlab/settingregistry';

const MAAP_JUPYTER_SERVER_EXTENSION_ID = 'maap-jupyter-server-extension:plugin';

const plugin: JupyterFrontEndPlugin<void> = {
  id: MAAP_JUPYTER_SERVER_EXTENSION_ID,
  description: 'MAAP Jupyter Server Extension',
  autoStart: true,
  requires: [ISettingRegistry],
  activate: async (app: JupyterFrontEnd, settings: ISettingRegistry) => {
    const setting = await settings.load(MAAP_JUPYTER_SERVER_EXTENSION_ID);
    const baseUrl = PageConfig.getBaseUrl();

    setting.changed.connect(() => {
      const newUrl = setting.get('maapApiUrl').composite as string;
      // const newToken = setting.get('maapToken').composite as string;
      // console.log('MAAP API URL updated by user:', newUrl);
    });

    // Get MAAP API URL and MAAP PGT Token and set them in the MAAP Extension settings
    try {
      const res = await fetch(
        `${baseUrl}maap-jupyter-server-extension/get-maap-params`
      );
      const { token, apiUrl } = await res.json();
      await setting.set('maapApiUrl', apiUrl);
      await setting.set('maapToken', token);
    } catch (error) {
      console.error('Failed to fetch MAAP parameters from server:', error);
    }
  }
};

export default plugin;
