import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ISettingRegistry } from '@jupyterlab/settingregistry';

/**
 * Initialization data for the maap-jupyter-server-extension extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'maap-jupyter-server-extension:plugin',
  description: 'A JupyterLab extension.',
  autoStart: true,
  requires: [ISettingRegistry],
  activate: async (app: JupyterFrontEnd, settings: ISettingRegistry) => {
    const setting = await settings.load('maap-jupyter-server-extension:plugin');

    try {
      const res = await fetch('http://localhost:8888/maap-jupyter-server-extension/get-api-url');
      console.log('Made call to backend');
      const value = await res.json();
      console.log('value:', value.apiUrl);
      if (value) {
        await setting.set('maapApiUrl', value.apiUrl);
        console.log('maapApiUrl set to:', value.apiUrl);
      } else {
        console.warn('No MAAP_API_URL returned from server');
      }
    } catch (error) {
      console.error('Failed to fetch env variable from server:', error);
    }
  }
};

export default plugin;
