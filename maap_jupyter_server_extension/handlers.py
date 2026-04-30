import json
import os
import re
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado
import subprocess
import urllib.request
import urllib.error

def is_valid_env_var_value(value: str) -> bool:
    """
    Validates that an environment variable value is 'safe':
    - Printable characters only (ASCII 32-126)
    - No nulls, control characters, or newlines
    - Not empty
    """
    pattern = re.compile(r"^[\x20-\x7E]+$")
    return bool(pattern.fullmatch(value))

def format_api_url(api_host: str) -> str:
    """
    Formats an API host to a full URL.
    If api_host is empty, returns empty string.
    Otherwise ensures the URL has https:// prefix and trailing slash.
    """
    if not api_host:
        return ""

    # Remove any trailing slashes first
    api_host = api_host.rstrip('/')

    # Add https:// if not present
    if not api_host.startswith('http://') and not api_host.startswith('https://'):
        api_host = 'https://' + api_host

    # Add trailing slash
    return api_host + '/'

class TestHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "This is /maap-jupyter-server-extension/test endpoint!"
        }))


class GetApiUrlHandler(APIHandler):
    """
        GET /maap-jupyter-server-extension/get-api-url

        This endpoint attempts to read the environment variable `MAAP_API_HOST` from
        the Jupyter server's environment and returns it as JSON. If the environment
        variable is not set, an empty string is returned. If any errors, the handler
        responds with HTTP status 500 and a JSON error message.

        Responses:
            200 OK:
                {
                    "maapApiUrl": "api_url_value" or ""
                }

            500 Internal Server Error:
                {
                    "error": "Error message"
                }
    """
    @tornado.web.authenticated
    def get(self):
        try:
            maap_api_host = os.environ.get('MAAP_API_HOST', "")
            maap_api_url = format_api_url(maap_api_host)
            self.finish(json.dumps({
                "maapApiUrl": maap_api_url
            }))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))

class InjectKeyHandler(APIHandler):
    def get(self):
        try:
            # Get MAAP API credentials from environment
            maap_api_host = os.environ.get('MAAP_API_HOST', '')
            maap_token = os.environ.get('MAAP_PGT', '')

            if not maap_api_host or not maap_token:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": "MAAP_API_HOST or MAAP_PGT not set in environment"
                }))
                return

            # Format the API URL
            api_url = format_api_url(maap_api_host)
            profile_url = f"{api_url}api/members/self"

            # Make request to MAAP API to get profile information
            req = urllib.request.Request(profile_url)
            req.add_header('cpticket', maap_token)

            try:
                with urllib.request.urlopen(req) as response:
                    profile_data = json.loads(response.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_msg = f"Failed to fetch profile from MAAP API: HTTP {e.code}"
                self.set_status(500)
                self.finish(json.dumps({"error": error_msg}))
                return
            except urllib.error.URLError as e:
                error_msg = f"Failed to connect to MAAP API: {str(e)}"
                self.set_status(500)
                self.finish(json.dumps({"error": error_msg}))
                return

            # Extract public SSH key from profile
            public_key = profile_data.get('public_ssh_key', '')

            if not public_key:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No public_ssh_key found in profile"
                }))
                return

            # Check if .ssh directory exists, if not create it
            home_dir = os.environ.get("JUPYTER_SERVER_ROOT", "/home/jovyan")
            os.chdir(home_dir)
            if not os.path.exists(".ssh"):
                os.makedirs(".ssh")

            # Check if authorized_keys file exits, if not create it
            if not os.path.exists(".ssh/authorized_keys"):
                with open(".ssh/authorized_keys", 'w'):
                    pass

            # Check if key already in file
            with open('.ssh/authorized_keys', 'r') as f:
                linelist = f.readlines()

            found = False
            for line in linelist:
                if public_key in line:
                    found = True

            # If not in file, inject key into authorized keys
            if not found:
                cmd = "echo " + public_key + " >> .ssh/authorized_keys && chmod 700 " + home_dir + " && chmod 700 .ssh/ && chmod 600 .ssh/authorized_keys"
                subprocess.check_output(cmd, shell=True)
                self.finish(json.dumps({"status": "success", "message": "SSH key injected"}))
            else:
                self.finish(json.dumps({"status": "success", "message": "SSH key already present"}))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))

class GetTokenHandler(APIHandler):
    """
        GET /maap-jupyter-server-extension/get-token

        Retrieves the value of the `MAAP_PGT_TOKEN` environment variable and returns it as a JSON response.
        If not set, returns empty string.

        Responses:
            200 OK:
                {
                    "maapToken": "token_value" or ""
                }

            500 Internal Server Error:
                {
                    "error": "Error message"
                }
    """
    @tornado.web.authenticated
    def get(self):
        try:
            token = os.environ.get('MAAP_PGT_TOKEN', "")
            self.finish(json.dumps({
                    "maapToken": token
                }))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))

class GetMaapParamsHandler(APIHandler):
    """
        GET /maap-jupyter-server-extension/get-maap-params

        Retrieves the value of the `MAAP_API_HOST`, `MAAP_PGT_TOKEN`, and `DOCKERIMAGE_PATH_DEFAULT`. If not set, returns empty string.
        If any errors, the handler responds with HTTP status 500 and a JSON error message.

        Responses:
            200 OK:
                {
                    "maapToken": "token_value" or "",
                    "maapApiUrl": "api_url_value" or "",
                    "defaultAppImage": "docker_image_path_default" or "",
                    "currentAppImage": "docker_image_path_current" or "",
                    "workspaceBucket": "workspace_bucket" or ""
                }

            500 Internal Server Error:
                {
                    "error": "Error message"
                }
    """
    @tornado.web.authenticated
    def get(self):
        try:
            token = os.environ.get('MAAP_PGT', "")
            api_host = os.environ.get('MAAP_API_HOST', "")
            api_url = format_api_url(api_host)
            docker_image_path_default = os.environ.get('DOCKERIMAGE_PATH_DEFAULT', "")
            docker_image_path_current = os.environ.get('DOCKERIMAGE_PATH_BASE_IMAGE', "")
            workspace_bucket = os.environ.get("WORKSPACE_BUCKET", "")
            self.finish(json.dumps({
                    "maapToken": token,
                    "maapApiUrl": api_url,
                    "defaultAppImage": docker_image_path_default,
                    "currentAppImage": docker_image_path_current,
                    "workspaceBucket": workspace_bucket
                }))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]

    # Routes
    test_route = url_path_join(base_url, "maap-jupyter-server-extension", "test")
    get_api_url_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-api-url")
    get_token_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-token")
    get_maap_params_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-maap-params")
    get_inject_public_key_route = url_path_join(base_url, "maap-jupyter-server-extension", "inject-public-key")

    handlers = [
        (test_route, TestHandler),
        (get_api_url_route, GetApiUrlHandler),
        (get_token_route, GetTokenHandler),
        (get_maap_params_route, GetMaapParamsHandler),
        (get_inject_public_key_route, InjectKeyHandler)
    ]
    web_app.add_handlers(host_pattern, handlers)
