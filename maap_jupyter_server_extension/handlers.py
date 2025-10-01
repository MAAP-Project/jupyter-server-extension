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
        variable is not set or any other error occurs, the handler
        responds with HTTP status 500 and a JSON error message.

        Responses:
            200 OK:
                {
                    "apiUrl": "<value of MAAP_API_URL>"
                }

            500 Internal Server Error:
                {
                    "error": "<error description>"
                }
    """
    @tornado.web.authenticated
    def get(self):
        try:
            maap_api_url = os.environ.get('MAAP_API_URL')
            self.finish(json.dumps({
                "apiUrl": maap_api_url
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
        If not set, returns None.

        Responses:
            200 OK:
                {
                    "token": "token_value" or None
                }

            500 Internal Server Error:
                {
                    "error": "Error message"
                }
    """
    @tornado.web.authenticated
    def get(self):
        try:
            token = os.environ.get('MAAP_PGT_TOKEN')
            self.finish(json.dumps({
                    "token": token
                }))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


class SetTokenHandler(APIHandler):
    """
        POST /maap-jupyter-server-extension/get-token

        This endpoint expects a JSON payload with a 'token' field. If the token value is valid,
        it is set to the'MAAP_PGT_TOKEN' environment variable.

        Responses:
            200 OK:
                {
                    "token": "token_value"
                }

            400 Client Error:
                {
                    "error": "Error message"
                }

            500 Internal Server Error:
                {
                    "error": "Error message"
                }
    """
    @tornado.web.authenticated
    def post(self):
        try:
            body = json.loads(self.request.body.decode('utf-8'))
            token = body.get('token')
            raise ValueError("test")
            if not token:
                raise ValueError("Token parameter is required")
            
            if not is_valid_env_var_value(token):
                raise ValueError(f"Invalid environment variable value: {token}")
            
            os.environ['MAAP_PGT_TOKEN'] = token
            self.set_status(200)
            self.finish(json.dumps({
                "message": "Token set successfully"
            }))
        except ValueError as e:
            self.set_status(400)
            self.finish(json.dumps({
                "error": str(e)
            }))
        except json.JSONDecodeError as e:
            self.set_status(400)
            self.finish(json.dumps({
                "error": f"Invalid JSON in request body: {str(e)}"
            }))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": f"Failed to set token: {str(e)}"
            }))


def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]

    # Routes
    test_route = url_path_join(base_url, "maap-jupyter-server-extension", "test")
    get_api_url_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-api-url")
    get_token_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-token")
    set_token_route = url_path_join(base_url, "maap-jupyter-server-extension", "set-token")

    handlers = [
        (test_route, TestHandler), 
        (get_api_url_route, GetApiUrlHandler),
        (get_token_route, GetTokenHandler),
        (set_token_route, SetTokenHandler)
    ]
    web_app.add_handlers(host_pattern, handlers)
