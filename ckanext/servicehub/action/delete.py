import random
import requests
import logging
from ckanext.servicehub.model.ServiceModel import App, Call
from werkzeug.datastructures import FileStorage

import ckan.logic as logic

from ckan.common import config

import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

http_session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
http_session.mount('http://', adapter)

log = logging.getLogger(__name__)
_get_or_bust = logic.get_or_bust

appserver_host = config.get('ckan.servicehub.appserver_host')
fileserver_host = config.get('ckan.servicehub.fileserver_host')


def service_delete(context, data_dict):
    app_id = data_dict['id']
    session = context['session']
    session.query(App).filter(App.app_id == app_id).delete()
    session.commit()
    # logic.get_action('app_index_delete')({}, {'app_id': app_id})


def call_delete(context, data_dict):
    call_id = data_dict['call_id']
    session = context['session']
    session.query(Call).filter(Call.call_id == call_id).delete()
    input_delete(context,data_dict)
    output_delete(context,data_dict)
    session.commit()


def reqform_delete(context, data_dict):
    path = os.path.join(fileserver_host, 'requestform', data_dict['app_id'])
    return http_session.delete(path).json()


def input_delete(context, data_dict):
    path = os.path.join(fileserver_host, 'input', data_dict['call_id'])
    return http_session.delete(path).json()


def output_delete(context, data_dict):
    path = os.path.join(fileserver_host, 'output', data_dict['call_id'])
    return http_session.delete(path).json()

def file_delete(context, data_dict):
    pass
public_functions = dict(service_delete=service_delete,
                        call_delete=call_delete,
                        reqform_delete=reqform_delete,
                        input_delete=input_delete,
                        output_delete=output_delete,
                        )
