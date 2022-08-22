import json

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

logging.basicConfig(format='%(asctime)s %(message)s')

@functools.lru_cache(maxsize=128)
def get_maap_config(host):
    path_to_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../', 'maap_environments.json')

    with open(path_to_json) as f:
        data = json.load(f)

    match = next((x for x in data if host in x['ade_server']), None)
    maap_config = next((x for x in data if x['default_host'] == True), None) if match is None else match

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
            "data": "This is /jupyter-server-extension/test endpoint!"
        }))


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



def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]
    #route_pattern = url_path_join(base_url, "jupyter-server-extension", "get_example")
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

    #handlers = [(route_pattern, RouteHandler)]
    web_app.add_handlers(host_pattern, handlers)
