import json
import os
import re
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado

def is_valid_env_var_value(value: str) -> bool:
    """
    Validates that an environment variable value is 'safe':
    - Printable characters only (ASCII 32-126)
    - No nulls, control characters, or newlines
    - Not empty
    """
    pattern = re.compile(r"^[\x20-\x7E]+$")
    return bool(pattern.fullmatch(value))

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

        This endpoint attempts to read the environment variable `MAAP_API_URL` from
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
            maap_api_url = os.environ.get('MAAP_API_URL', "")
            self.finish(json.dumps({
                "maapApiUrl": maap_api_url
            }))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


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

        Retrieves the value of the `MAAP_API_URL`, `MAAP_PGT_TOKEN`, and `DOCKERIMAGE_PATH_DEFAULT`. If not set, returns empty string.
        If any errors, the handler responds with HTTP status 500 and a JSON error message.

        Responses:
            200 OK:
                {
                    "maapToken": "token_value" or "",
                    "maapApiUrl": "api_url_value" or "",
                    "defaultAppImage": "docker_image_path_default" or ""
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
            api_url = os.environ.get('MAAP_API_URL', "")
            docker_image_path_default = os.environ.get('DOCKERIMAGE_PATH_DEFAULT', "")
            self.finish(json.dumps({
                    "maapToken": token,
                    "maapApiUrl": api_url,
                    "defaultAppImage": docker_image_path_default
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

    handlers = [
        (test_route, TestHandler), 
        (get_api_url_route, GetApiUrlHandler),
        (get_token_route, GetTokenHandler),
        (get_maap_params_route, GetMaapParamsHandler)
    ]
    web_app.add_handlers(host_pattern, handlers)
