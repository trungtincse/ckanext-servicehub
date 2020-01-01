import random

import requests
import json
import logging

from ckanext.servicehub.model.ServiceModel import App, AppPort

import ckan.lib.plugins as lib_plugins
import ckan.logic as logic
import ckan.lib.navl.dictization_functions
import ckan.lib.uploader as uploader
import ckan.lib.datapreview

log = logging.getLogger(__name__)
_validate = ckan.lib.navl.dictization_functions.validate
_check_access = logic.check_access
_get_action = logic.get_action
ValidationError = logic.ValidationError
NotFound = logic.NotFound
_get_or_bust = logic.get_or_bust
import os
# host= os.getenv('APP_SERVER_HOST')
# appserver_host='http://%s'%host
appserver_host='http://0.0.0.0:5001'
def service_create(context, data_dict):
    _check_access('service_create', context, data_dict)
    return _service_create(context, data_dict)


def _service_create(context, data_dict):
    if(data_dict['type']=='Server'):
        ins = App(data_dict['app_name'],
                  data_dict['type'],
                  data_dict['slug_name'],
                  data_dict['image'],
                  data_dict['description'],
                  data_dict['owner'],
                  data_dict['language'],
                  # port2port=data_dict['port2port'],
                  status=data_dict['status'],
                  )
        session = context['session']
        # check port
        is_port_avai=False
        while not is_port_avai:
            container_port = '%d'%random.randint(10000, 60000)
            port_in_use=session.query(AppPort).filter(AppPort.port==container_port)
            is_port_avai = True if port_in_use.count() <1 else False
        app_port_ins=AppPort(ins.app_id,container_port)
        ins.port2port=container_port
        session.add(ins)
        session.add(app_port_ins)
        session.commit()
        requestCreateServer(ins)
    elif(data_dict['type']=='Batch'):
        ins = App(data_dict['app_name'],
                  data_dict['type'],
                  data_dict['slug_name'],
                  data_dict['image'],
                  data_dict['description'],
                  data_dict['owner'],
                  data_dict['language'],
                  json_input=data_dict['json_input'],
                  binary_input=data_dict['binary_input'],
                  )
        session = context['session']
        session.add(ins)
        session.commit()
        requestCreateBatch(ins,data_dict['codeFile'])
def requestCreateServer(instance):
    url='%s/app/new/server/%s'%(appserver_host,instance.app_id)
    print url
    response=requests.post(url)
    # return rps
def requestCreateBatch(instance,data_request):
    url='%s/app/new/batch/%s'%(appserver_host,instance.app_id)
    print url
    response=requests.post(url=url,data=data_request.read()).json()
