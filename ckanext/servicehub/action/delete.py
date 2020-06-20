import random
import requests
import logging
from ckanext.servicehub.model.ServiceModel import App, Call
from werkzeug.datastructures import FileStorage

import ckan.logic as logic

from ckan.common import config
import ckan.logic
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

http_session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
http_session.mount('http://', adapter)

log = logging.getLogger(__name__)
_get_or_bust = logic.get_or_bust
_check_access = ckan.logic.check_access
appserver_host = config.get('ckan.servicehub.appserver_host')
fileserver_host = config.get('ckan.servicehub.fileserver_host')
central_logger = logging.getLogger('logserver')
local_logger = logging.getLogger('local')

def service_delete(context, data_dict):
    app_id = data_dict['id']
    _check_access(u'delete_service',context,dict(app_id=app_id))
    session = context['session']
    try:
        session.query(App).filter(App.app_id == app_id).delete()
        session.commit()
    except:
        central_logger.info("user=%s&action=service_delete&error_code=1" % context['user'])
        local_logger.info("%s %s %s" % (context['user'], "service_delete", "Can not delete application %s"%app_id))
        return dict(success=False,error="Can not delete application %s"%app_id)
    logic.get_action('app_index_delete')(context, {'app_id': app_id})
    central_logger.info("user=%s&action=service_delete&error_code=0" % context['user'])
    local_logger.info("%s %s %s"%(context['user'],"service_delete","Delete app %s success"%app_id))
    return dict(success=True)

# def call_delete(context, data_dict):
#     call_id = data_dict['call_id']
#     session = context['session']
#     session.query(Call).filter(Call.call_id == call_id).delete()
#     input_delete(context,data_dict)
#     output_delete(context,data_dict)
#     session.commit()
#     return dict(success=True)
#
#
# def reqform_delete(context, data_dict):
#     path = os.path.join(fileserver_host, 'requestform', data_dict['app_id'])
#     return http_session.delete(path).json()
#
#
# def input_delete(context, data_dict):
#     path = os.path.join(fileserver_host, 'input', data_dict['call_id'])
#     return http_session.delete(path).json()
#
#
# def output_delete(context, data_dict):
#     path = os.path.join(fileserver_host, 'output', data_dict['call_id'])
#     return http_session.delete(path).json()

def file_delete(context, data_dict):
    pass
public_functions = dict(service_delete=service_delete,
                        # call_delete=call_delete,
                        # reqform_delete=reqform_delete,
                        # input_delete=input_delete,
                        # output_delete=output_delete,
                        )
