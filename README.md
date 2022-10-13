# Jupyter Server Extension

This is the JupyterLab server-side extension for the custom MAAP JupyterLab frontend extensions. It provides RESTful endpoints to the MAAP API and other services.

This extension is composed of a Python package named `jupyter_server_extension`
for the server extension and a NPM package named `jupyter-server-extension`
for the frontend extension.  
&nbsp;
## Requirements

- JupyterLab >= 3.4  
&nbsp;
## Install

To install the extension, execute:

```bash
pip install -i https://test.pypi.org/simple/ jupyter-server-extension

jupyter server extension enable jupyter_server_extension
```


&nbsp;
## Uninstall

To remove the extension, execute:

```bash
pip uninstall -i https://test.pypi.org/simple/ jupyter-server-extension
```  
&nbsp;
## Usage
RESTful endpoints are made available to the JupyterLab frontend. In the frontend extension code, users may build the request URL like so:
```bash
var requestUrl = new URL(HOST_NAME + 'jupyter-server-extension/listAlgorithms');
```

i.e. using localhost as an example: 
```bash
http://localhost:8888/jupyter-server-extension/listAlgorithms
```
  
&nbsp;
## Troubleshoot

If you are seeing the frontend extension, but it is not working, check
that the server extension is enabled:

```bash
jupyter server extension list
```

If the server extension is installed and enabled, but you are not seeing
the frontend extension, check the frontend extension is installed:

```bash
jupyter labextension list
```  
&nbsp;
## Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the jupyter_server_extension directory
# Install package in development mode
pip install -e .
# Link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite
# Server extension must be manually installed in develop mode
jupyter server extension enable jupyter_server_extension
# Rebuild extension Typescript source after making changes
jlpm build
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).

By default, the `jlpm build` command generates the source maps for this extension to make it easier to debug using the browser dev tools. To also generate source maps for the JupyterLab core extensions, you can run the following command:

```bash
jupyter lab build --minimize=False
```  
&nbsp;
## Development uninstall

```bash
# Server extension must be manually disabled in develop mode
jupyter server extension disable jupyter_server_extension
pip uninstall jupyter_server_extension
```

In development mode, you will also need to remove the symlink created by `jupyter labextension develop`
command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
folder is located. Then you can remove the symlink named `jupyter-server-extension` within that folder.  
&nbsp;
## Questions?
Refer to the [Q&A discussion board](https://github.com/MAAP-Project/jupyter-server-extension/discussions/categories/q-a).
