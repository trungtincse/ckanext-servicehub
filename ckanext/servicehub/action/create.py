import mimetypes
import random

import requests
import json
import logging

import urllib3
from ckanext.servicehub.model.ServiceModel import App, Call
from werkzeug.datastructures import FileStorage

import ckan.lib.plugins as lib_plugins
import ckan.logic as logic
import ckan.lib.navl.dictization_functions
import ckan.lib.datapreview
from ckan.common import config
from ckanext.servicehub.upload.CodeUploader import CodeUploader

from ckanext.servicehub.model import MongoClient
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

http_session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
http_session.mount('http://', adapter)

log = logging.getLogger(__name__)
_validate = ckan.lib.navl.dictization_functions.validate
_check_access = logic.check_access
_get_action = logic.get_action
ValidationError = logic.ValidationError
NotFound = logic.NotFound
_get_or_bust = logic.get_or_bust

appserver_host = config.get('ckan.servicehub.appserver_host')
fileserver_host = config.get('ckan.servicehub.fileserver_host')


# http = urllib3.HTTPConnectionPool(fileserver_host, maxsize=10)
# http = urllib3.HTTPConnectionPool("localhost",3000, maxsize=10)

def service_create(context, data_dict):
    session = context['session']
    ins = App(data_dict['app_name'],
              data_dict['service_type'],
              data_dict['slug_name'],
              data_dict['image'],
              data_dict['owner'],
              data_dict['description'])
    if (data_dict['service_type'] == 'Server'):
        ins.setOption(s_port=data_dict['port'], p_port='%d' % random.randint(10000, 60000))
        requestCreateServer(ins)
    elif (data_dict['service_type'] == 'Batch'):
        ins.setOption(language=data_dict['language'])
        path = os.path.join(fileserver_host, 'requestform',ins.app_id)

        json=makeReqFormJSON(app_id=ins.app_id,
                                  var_name=data_dict.get('var_name', []),
                                  label=data_dict.get('label', []),
                                  type=data_dict.get('type', []))
        code_url = storeCodeFile(data_dict['codeFile'], ins.app_id)
        http_session.post(path, json=json)
        ins.setOption(code_url=code_url)

    try:
        ava_url = storeAvatar(data_dict['avatar'], ins.app_id)
        print ava_url
        ins.setOption(ava_url=ava_url)

        session.add(ins)
        session.commit()
    except:
        session.rollback()
        raise

def makeReqFormJSON(**kwargs):
    label = kwargs['label']
    var_name = kwargs['var_name']
    type = kwargs['type']
    record = dict(
        app_id=kwargs["app_id"],
        fields= [dict(label=x[0], var_name=x[1], type=x[2]) for x in zip(label, var_name, type)] if isinstance(label,list) else [dict(label=label, var_name=var_name, type=type)]
    )
    return record
def storeAvatar(file, app_id):
    avatar_file = file
    file_name = 'avatar.%s' % avatar_file.filename.split('.')[-1]
    path = os.path.join(fileserver_host, 'file', 'image', app_id, file_name)
    http_session.post(path,
                      files=dict(file=avatar_file.read())
                      )
    return path


def call_create(context, data_dict):
    session = context['session']
    user = context['user']
    app_id= data_dict["app_id"]
    del data_dict["app_id"]
    ins = Call(user, app_id)
    values=[]
    try:
        for k, v in data_dict.items():
            if isinstance(v, FileStorage):
                v = storeInput(v, ins.call_id)
            values.append(dict(name=k,value=v))
        path = os.path.join(fileserver_host, 'input', ins.call_id)
        http_session.post(path,json=dict(call_id=ins.call_id,values=values))
        session.add(ins)
        session.commit()
    except:
        session.rollback()
        raise


def storeInput(file, call_id):
    input_file = file
    file_name = 'avatar.%s' % input_file.filename.split('.')[-1]
    path = os.path.join(fileserver_host, 'file', 'input', call_id, file_name)
    http_session.post(path,
                      files=dict(file=input_file.read())
                      )
    return path


def storeOutput(file, call_id):
    output_file = file
    file_name = 'avatar.%s' % output_file.filename.split('.')[-1]
    path = os.path.join(fileserver_host, 'file', 'output', call_id, file_name)
    http_session.post(path,
                      files=dict(file=output_file.read())
                      )
    return path


def requestCreateServer(instance):
    url = '%s/app/new/server/%s' % (appserver_host, instance.app_id)
    print url
    response = requests.post(url)
    # return rps


def storeCodeFile(file, app_id):
    code_file = file
    file_name = 'code.zip'
    path = os.path.join(fileserver_host, 'file', 'code', app_id, file_name)
    http_session.post(path,
                      files=dict(file=code_file.read())
                      )
    # http.request('POST',
    #              os.path.join('/file','code',app_id),
    #              fields=dict(file=code_file.read(),filename=file_name)
    #              )

    return path


class StoreFileException(Exception):
    pass
