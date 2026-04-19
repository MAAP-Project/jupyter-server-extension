import json
import os
import re
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado
import subprocess
import urllib.parse
import maap_jupyter_server_extension.constants as constants
from notebook.base.handlers import IPythonHandler
from maap.maap import MAAP #dependency on maap-py but I am not sure workaround right now 
import requests

def get_maap_config(host):
    api_host = os.getenv("MAAP_API_HOST", constants.DEFAULT_API)
    maap_api_config_endpoint = os.getenv("MAAP_API_CONFIG_ENDPOINT", "api/environment/config")
    ade_host = host if host in constants.ADE_OPTIONS else os.getenv("MAAP_ADE_HOST", constants.DEFAULT_ADE)
    environments_endpoint = "https://" + api_host + "/" + maap_api_config_endpoint + "/"+urllib.parse.quote(urllib.parse.quote("https://", safe=""))+ade_host
    return requests.get(environments_endpoint).json()

def dps_bucket_name(host):
	return get_maap_config(host)['workspace_bucket'] # Do I need WORKSPACE_BUCKET??

def maap_api_url(host):
	return 'https://{}'.format(get_maap_config(host)['api_server'])

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

class MAAPConfigEnvironmentHandler(APIHandler):
    def get(self):  
        env = get_maap_config(self.request.host)
        self.finish(env)

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

class InjectKeyHandler(IPythonHandler):
    def get(self):
        public_key = self.get_argument('key', '')

        if public_key:
            print("=== Injecting SSH KEY ===")

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
                    print("Key already in authorized_keys")
                    found = True

            # If not in file, inject key into authorized keys
            if not found:
                cmd = "echo " + public_key + " >> .ssh/authorized_keys && chmod 700 " + home_dir + " && chmod 700 .ssh/ && chmod 600 .ssh/authorized_keys"
                print(cmd)
                subprocess.check_output(cmd, shell=True)
                print("=== INJECTED KEY ===")
            else:
                print("=== KEY ALREADY PRESENT ===")

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
                    "currentAppImage": "docker_image_path_current" or ""
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
            self.finish(json.dumps({
                    "maapToken": token,
                    "maapApiUrl": api_url,
                    "defaultAppImage": docker_image_path_default,
                    "currentAppImage": docker_image_path_current
                }))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))

class Presigneds3UrlHandler(IPythonHandler):

    def get(self):
        # get arguments
        bucket = dps_bucket_name(self.request.host)
        key = self.get_argument('key', '')
        rt_path = os.path.expanduser(self.get_argument('home_path', ''))
        abs_path = os.path.join(rt_path, key)
        proxy_ticket = self.get_argument('proxy-ticket','')
        expiration = self.get_argument('duration','86400') # default 24 hrs
        # This is replacing the workspace name because the buckets correspond to the username
        username = self.get_argument('username', '')

        print('bucket is '+bucket)     
        print('key is '+key)        
        print('full path is '+abs_path) 

        # -----------------------
        # Checking for bad input
        # -----------------------
        # if directory, return error - dirs not supported
        if os.path.isdir(abs_path):
            self.finish({"status_code": 412, "message": "error", "url": "Presigned S3 links do not support folders"})
            return

        # check if file in valid folder (under mounted folder path)
        resp = subprocess.check_output("df -h | grep s3fs | awk '{print $6}'", shell=True).decode('utf-8')
        mounted_dirs = resp.strip().split('\n')
        print(mounted_dirs)
        if len(mounted_dirs) == 0:
            self.finish({"status_code": 412, "message": "error",
                "url": "Presigned S3 links can only be created for files in a mounted org or user folder" +
                    "\nMounted folders include:\n{}".format(resp)
                })
            return

        if not any([mounted_dir in abs_path for mounted_dir in mounted_dirs]):
            self.finish({"status_code": 412, "message": "error",
                "url": "Presigned S3 links can only be created for files in a mounted org or user folder" +
                    "\nMounted folders include:\n{}".format(resp)
                })
            return

        # -----------------------
        # Generate S3 Link
        # -----------------------
        # if valid path, get presigned URL
        # expiration = '43200' # 12 hrs in seconds
        print('expiration is {} seconds', expiration)

        url = '{}/api/members/self/presignedUrlS3/{}/{}?exp={}&ws={}'.format(maap_api_url(self.request.host), bucket, key, expiration, username)
        headers = {'Accept': 'application/json', 'proxy-ticket': proxy_ticket}
        r = requests.get(
            url,
            headers=headers,
            verify=False
        )
        print(r.text)

        resp = json.loads(r.text)   
        self.finish({"status_code":200, "message": "success", "url":resp['url']})

class AccountInfoPGTENVHandler(IPythonHandler):
    @tornado.web.authenticated
    def get(self):
        proxy_granting_ticket = os.environ.get('MAAP_PGT', '')

        maap = MAAP()
        profile = maap.profile.account_info(proxy_ticket = proxy_granting_ticket)
        self.finish({"profile": profile})


def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]

    # Routes
    test_route = url_path_join(base_url, "maap-jupyter-server-extension", "test")
    get_api_url_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-api-url")
    get_token_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-token")
    get_maap_params_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-maap-params")
    get_inject_public_key_route = url_path_join(base_url, "maap-jupyter-server-extension", "inject-public-key")
    get_config_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-config")
    get_account_info_pgt_token_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-account-into-pgt-token")
    get_presigned_s3_url_route = url_path_join(base_url, "maap-jupyter-server-extension", "get-presigned-s3-url")

    handlers = [
        (test_route, TestHandler), 
        (get_api_url_route, GetApiUrlHandler),
        (get_token_route, GetTokenHandler),
        (get_maap_params_route, GetMaapParamsHandler),
        {get_inject_public_key_route, InjectKeyHandler},
        {get_config_route, MAAPConfigEnvironmentHandler},
        {get_account_info_pgt_token_route, AccountInfoPGTENVHandler},
        {get_presigned_s3_url_route, Presigneds3UrlHandler}
    ]
    web_app.add_handlers(host_pattern, handlers)
