import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './handler';

/**
 * Initialization data for the jupyter-server-extension extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyter-server-extension:plugin',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab MAAP DPS Server extension is activated!');

    requestAPI<any>('get_example')
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The maap_jupyter_server_extension server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default plugin;
