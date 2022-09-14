import json
import sys
import nbformat
import subprocess
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado
from notebook.base.handlers import IPythonHandler
from maap.maap import MAAP
import functools
import os
import xml.etree.ElementTree as ET
import xmltodict
import logging
import requests

logging.basicConfig(format='%(asctime)s %(message)s')

@functools.lru_cache(maxsize=128)
def get_maap_config(host):
    print(os.environ)
    path_to_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', os.environ['ENVIRONMENTS_FILE_PATH'])
    
    with open(path_to_json) as f:
        data = json.load(f)

    match = next((x for x in data if host in x['ade_server']), None)
    maap_config = next((x for x in data if x['default_host'] == True), None) if match is None else match
    print("Printing from maap config")
    print(maap_config)
    return maap_config


def maap_api(host):
    return get_maap_config(host)['api_server']


class RouteHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "This is /jupyter-server-extension/get_example endpoint!"
        }))


class RouteTestHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "This is /jupyter-server-extension/test1 endpoint!"
        }))


class RouteTest1Handler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "This is /jupyter-server-extension/maapsec_test endpoint!"
        }))


######################################
######################################
#
# DPS
#
######################################
######################################

class ListAlgorithmsHandler(IPythonHandler):
    @tornado.web.authenticated
    def get(self):
        print("In python list algos handler")

        #maap = MAAP(not_self_signed=False)
        maap = MAAP(maap_host=maap_api(self.request.host))
        print(maap_api(self.request.host))

        try:
            print("Making query from backend.")
            r = maap.listAlgorithms()
            self.finish({"status_code": r.status_code, "response": r.json()})
        except:
            print("Failed list algorithms query.")
            self.finish({"status": r})


class DescribeAlgorithmsHandler(IPythonHandler):
    def get(self):
        #maap = MAAP(not_self_signed=False)
        maap = MAAP(maap_host=maap_api(self.request.host))

        try:
            r = maap.describeAlgorithm(self.get_argument("algo_id"))
            o = xmltodict.parse(r.text)
            self.finish({"status_code": r.status_code, "response": json.dumps(o)})
        except:
            print("Failed describe algorithms query.")
            self.finish()


class GetQueuesHandler(IPythonHandler):
    def get(self):
        #maap = MAAP(not_self_signed=False)
        maap = MAAP(maap_host=maap_api(self.request.host))
        try:
            r = maap.getQueues()
            resp = json.loads(r.text)
            # result = [e[len('maap-worker-'):] for e in resp['queues'] if 'maap-worker' in e]
            result = resp['queues']
            self.finish({"status_code": r.status_code, "response": result})
        except:
            self.finish({"status_code": r.status_code, "response": r.text})


class GetCMRCollectionsHandler(IPythonHandler):
    def get(self):
        #maap = MAAP(not_self_signed=False)
        maap = MAAP(maap_host=maap_api(self.request.host))

        try:
            r = maap.searchCollection()
            # Query returns a list -- not an object
            self.finish({"response": r})
        except Exception as e:
            print("Failed collections query: ")
            self.finish({"error": e})


class ListUserJobsHandler(IPythonHandler):
    def get(self):
        #maap = MAAP(not_self_signed=False)
        maap = MAAP(maap_host=maap_api(self.request.host))

        try:
            r = maap.listJobs(self.get_argument("username"))
            self.finish({"status_code": r.status_code, "response": r.json()})
        except:
            print("Failed list jobs query.")
            self.finish()


class SubmitJobHandler(IPythonHandler):
    def args_to_dict(self):
        # convert args to dict
        params = self.request.arguments
        for k, v in params.items():
            params[k] = v[0].decode("utf-8")
        return params

    def get(self):
        print("JOB SUBMIT")

        #test_request = {"algo_id": "test_algo", "username": "anonymous", "queue": "geospec-job_worker-32gb"}
        kwargs = self.args_to_dict()
        #maap = MAAP(not_self_signed=False)
        maap = MAAP(maap_host=maap_api(self.request.host))
        resp = maap.submitJob(**kwargs)
        #logger.debug(resp)
        status_code = resp['http_status_code']
        print("PRINT RESPONSE")
        print(resp)
        if status_code == 200:
            result = 'JobID is {}'.format(resp['job_id'])
            self.finish({"status_code": status_code, "response": result})
        elif status_code == 400:
            self.finish({"status_code": status_code, "response": resp['result']})
        else:
            self.finish({"status_code": status_code, "response": resp['status']})



class GetJobStatusHandler(IPythonHandler):
    def get(self):
        #maap = MAAP(not_self_signed=False)
        maap = MAAP(maap_host=maap_api(self.request.host))

        try:
            r = maap.getJobStatus(self.get_argument("job_id"))
            o = xmltodict.parse(r.text)
            print("job status response:")
            print(r)
            self.finish({"status_code": r.status_code, "response": json.dumps(o)})
        except:
            print("Failed job status query.")
            self.finish()


class GetJobResultHandler(IPythonHandler):
    def get(self):
        #maap = MAAP(not_self_signed=False)
        maap = MAAP(maap_host=maap_api(self.request.host))

        try:
            r = maap.getJobResult(self.get_argument("job_id"))
            o = xmltodict.parse(r.text)
            print("job result response:")
            print(r)
            self.finish({"status_code": r.status_code, "response": json.dumps(o)})
        except:
            print("Failed job result query.")
            self.finish()



class GetJobMetricsHandler(IPythonHandler):
    def get(self):
        #maap = MAAP(not_self_signed=False)
        maap = MAAP(maap_host=maap_api(self.request.host))

        try:
            r = maap.getJobMetrics(self.get_argument("job_id"))
            o = xmltodict.parse(r.text)
            print("job result response:")
            print(r)
            self.finish({"status_code": r.status_code, "response": json.dumps(o)})
        except:
            print("Failed job result query.")
            self.finish()


######################################
######################################
#
# EDSC
#
######################################
######################################

class GetGranulesHandler(IPythonHandler):
    def printUrls(self, granules):
        url_list = '[\n'
        for res in granules:
            if res.getDownloadUrl():
                url_list = url_list + '\'' + res.getDownloadUrl() + '\',\n'
        url_list = url_list + ']'
        return url_list

    def get(self):

        maap = MAAP(maap_api(self.request.host))
        cmr_query = self.get_argument('cmr_query', '')
        limit = str(self.get_argument('limit', ''))
        print("cmr_query", cmr_query)

        query_string = maap.getCallFromCmrUri(cmr_query, limit=limit)
        granules = eval(query_string)
        query_result = self.printUrls(granules)
        try:
            print("Response is: ", query_result)
        except:
            print("Could not print results")
        self.finish({"granule_urls": query_result})


class GetQueryHandler(IPythonHandler):
    def get(self):
        maap = MAAP(maap_api(self.request.host))
        cmr_query = self.get_argument('cmr_query', '')
        limit = str(self.get_argument('limit', ''))
        query_type = self.get_argument('query_type', 'granule')
        print("cmr_query", cmr_query)

        query_string = maap.getCallFromCmrUri(cmr_query, limit=limit, search=query_type)
        print("Response is: ", query_string)
        self.finish({"query_string": query_string})


class IFrameHandler(IPythonHandler):
    def initialize(self, welcome=None, sites=None):
        self.sites = sites
        self.welcome = welcome

    def get(self):
        self.finish(json.dumps({'welcome': self.welcome or '', 'sites': self.sites}))


class IFrameProxyHandler(IPythonHandler):
    def get(self):
        url = self.request.get_argument('url', '')
        if url:
            self.finish(requests.get(url, headers=self.request.headers).text)
        else:
            self.finish('')


######################################
######################################
#
# MAAPSEC
#
######################################
######################################

class MaapEnvironmentHandler(IPythonHandler):
    def get(self, **params):  
        env = get_maap_config(self.request.host)
        self.finish(env)

class MaapLoginHandler(IPythonHandler):
    def get(self, **params):
        try:    
            param_ticket = self.request.query_arguments['ticket'][0].decode('UTF-8')     
            param_service = self.request.query_arguments['service'][0].decode('UTF-8') 
            env = get_maap_config(self.request.host)
            print("More testing")
            print(env)
            auth_server = 'https://{auth_host}/cas'.format(auth_host=env['auth_server'])

            url = '{base_url}/p3/serviceValidate?ticket={ticket}&service={service}&pgtUrl={base_url}&state='.format(
                base_url=auth_server, ticket=param_ticket, service=param_service)

            print('auth url: ' + url)

            auth_response = requests.get(
                url, 
                verify=False
            )

            print('auth response:')
            print(auth_response)

            xmldump = auth_response.text.strip()
            
            print('xmldump:')
            print(xmldump)

            is_valid = True if "cas:authenticationSuccess" in xmldump or \
                            "cas:proxySuccess" in xmldump else False

            if is_valid:
                tree = ElementTree(fromstring(xmldump))
                root = tree.getroot()

                result = {}
                for i in root.iter():
                    if "PGTIOU" in i.tag:
                        continue
                    result[i.tag.replace("cas:", "").replace("{http://www.yale.edu/tp/cas}", "")] = i.text

                self.finish({"status_code": auth_response.status_code, "attributes": json.dumps(result)})
            else:
                self.finish({"status_code": 403, "response": xmldump, "json_object": {}})
            
        except ValueError:
            self.finish({"status_code": 500, "result": auth_response.reason, "json_object": {}})

    def _get_cas_attribute_value(self, attributes, attribute_key):

        if attributes and "cas:" + attribute_key in attributes:
            return attributes["cas:" + attribute_key]
        else:
            return ''


def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]

    # DPS
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "get_example"), RouteHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "test"), RouteTestHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "listAlgorithms"), ListAlgorithmsHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "describeAlgorithms"), DescribeAlgorithmsHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "getQueues"), GetQueuesHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "getCMRCollections"), GetCMRCollectionsHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "listUserJobs"), ListUserJobsHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "submitJob"), SubmitJobHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "getJobStatus"), GetJobStatusHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "getJobResult"), GetJobResultHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "getJobMetrics"), GetJobMetricsHandler)])

    # MAAPSEC
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "maapsec", "environment"), MaapEnvironmentHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "maapsec", "login"), MaapLoginHandler)])

    # EDSC
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "edsc", "getGranules"), GetGranulesHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "edsc", "getQuery"), GetQueryHandler)])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, "jupyter-server-extension", "edsc"), IFrameHandler, {'welcome': welcome, 'sites': sites}), (url_path_join(base_url, 'jupyter-server-extension/edsc/proxy'), IFrameProxyHandler)])



    web_app.add_handlers(host_pattern, handlers)
    
