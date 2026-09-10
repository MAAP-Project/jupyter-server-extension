// tsconfig.json only includes src/*, so give the editor the Jest globals here
/// <reference types="jest" />
import { JupyterFrontEnd } from '@jupyterlab/application';
import { ServerConnection } from '@jupyterlab/services';
import { ISettingRegistry } from '@jupyterlab/settingregistry';

import plugin from '../index';

const PLUGIN_ID = 'maap-jupyter-server-extension:plugin';

// Settings the user already has saved, which should survive whenever the
// environment doesn't supply a replacement
const SAVED_SETTINGS: Record<string, string> = {
  maapApiUrl: 'https://api.saved.maap-project.org/',
  maapToken: 'saved-token',
  defaultAppImage: 'saved/default:image',
  currentAppImage: 'saved/current:image',
  workspaceBucket: 'saved-bucket'
};

const ENV_PARAMS = {
  maapApiUrl: 'https://api.env.maap-project.org/',
  maapToken: 'env-token',
  defaultAppImage: 'env/default:image',
  currentAppImage: 'env/current:image',
  workspaceBucket: 'env-bucket'
};

function createSettingRegistry() {
  const values = { ...SAVED_SETTINGS };
  const set = jest.fn(async (key: string, value: string) => {
    values[key] = value;
  });
  const settings = { set } as unknown as ISettingRegistry.ISettings;
  const registry = {
    load: jest.fn(async () => settings)
  } as unknown as ISettingRegistry;
  return { registry, set, values };
}

function createResponse(
  body: unknown,
  { ok = true, status = 200, statusText = 'OK' } = {}
): Response {
  return { ok, status, statusText, json: async () => body } as Response;
}

async function activate(registry: ISettingRegistry, response: Response) {
  jest
    .spyOn(ServerConnection, 'makeSettings')
    .mockReturnValue({} as ServerConnection.ISettings);
  const makeRequest = jest
    .spyOn(ServerConnection, 'makeRequest')
    .mockResolvedValue(response);

  await plugin.activate({} as JupyterFrontEnd, registry);
  // activate() doesn't wait for the settings update, so let it finish
  await new Promise(resolve => setTimeout(resolve, 0));

  return makeRequest;
}

describe('maap-jupyter-server-extension:plugin', () => {
  beforeEach(() => {
    jest.spyOn(console, 'log').mockImplementation(() => undefined);
    jest.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('overrides every setting the environment supplies', async () => {
    const { registry, set, values } = createSettingRegistry();

    const makeRequest = await activate(registry, createResponse(ENV_PARAMS));

    expect(registry.load).toHaveBeenCalledWith(PLUGIN_ID);
    expect(makeRequest).toHaveBeenCalledWith(
      expect.stringMatching(/maap-jupyter-server-extension\/get-maap-params$/),
      { method: 'GET' },
      expect.anything()
    );
    expect(set).toHaveBeenCalledTimes(5);
    expect(values).toEqual(ENV_PARAMS);
  });

  it('keeps existing settings when the environment value is empty, blank or missing', async () => {
    const { registry, set, values } = createSettingRegistry();

    await activate(
      registry,
      createResponse({
        maapApiUrl: ENV_PARAMS.maapApiUrl,
        maapToken: '',
        defaultAppImage: '   ',
        // currentAppImage omitted entirely
        workspaceBucket: ENV_PARAMS.workspaceBucket
      })
    );

    expect(set).toHaveBeenCalledTimes(2);
    expect(values).toEqual({
      ...SAVED_SETTINGS,
      maapApiUrl: ENV_PARAMS.maapApiUrl,
      workspaceBucket: ENV_PARAMS.workspaceBucket
    });
  });

  it('trims whitespace from environment values before saving them', async () => {
    const { registry, values } = createSettingRegistry();

    await activate(
      registry,
      createResponse({ ...ENV_PARAMS, maapToken: '  env-token\n' })
    );

    expect(values.maapToken).toBe('env-token');
  });

  it('leaves all settings unchanged when the environment supplies nothing', async () => {
    const { registry, set, values } = createSettingRegistry();

    await activate(
      registry,
      createResponse({
        maapApiUrl: '',
        maapToken: '',
        defaultAppImage: '',
        currentAppImage: '',
        workspaceBucket: ''
      })
    );

    expect(set).not.toHaveBeenCalled();
    expect(values).toEqual(SAVED_SETTINGS);
  });

  it('leaves all settings unchanged when the server request fails', async () => {
    const { registry, set, values } = createSettingRegistry();

    await activate(
      registry,
      createResponse(
        { error: 'boom' },
        { ok: false, status: 500, statusText: 'Internal Server Error' }
      )
    );

    expect(set).not.toHaveBeenCalled();
    expect(values).toEqual(SAVED_SETTINGS);
    expect(console.error).toHaveBeenCalledWith(
      'Failed to fetch MAAP parameters from server: ',
      expect.objectContaining({ message: 'HTTP 500 Internal Server Error' })
    );
  });
});
