import mimetypes
import random

import requests
import json
import logging

from ckanext.servicehub.model.ServiceModel import App

import ckan.lib.plugins as lib_plugins
import ckan.logic as logic
import ckan.lib.navl.dictization_functions
import ckan.lib.datapreview
from ckan.common import config
from ckanext.servicehub.upload.CodeUploader import CodeUploader

from ckanext.servicehub.model import MongoClient

log = logging.getLogger(__name__)
_validate = ckan.lib.navl.dictization_functions.validate
_check_access = logic.check_access
_get_action = logic.get_action
ValidationError = logic.ValidationError
NotFound = logic.NotFound
_get_or_bust = logic.get_or_bust
import os

appserver_host = config.get('ckan.servicehub.appserver_host')


def service_create(context, data_dict):
    return _service_create(context, data_dict)


def _service_create(context, data_dict):
    if (data_dict['type'] == 'Server'):
        ins = App(data_dict['app_name'],
                  data_dict['type'],
                  data_dict['slug_name'],
                  data_dict['image'],
                  data_dict['owner'],
                  data_dict['description'],
                  data_dict['language'],
                  s_port=data_dict['port'],
                  p_port='%d' % random.randint(10000, 60000),
                  status=data_dict['status'],
                  )
        session = context['session']
        session.add(ins)
        try:
            session.commit()
        except:
            session.rollback()
            raise
        requestCreateServer(ins)
    elif (data_dict['type'] == 'Batch'):
        ins = App(data_dict['app_name'],
                  data_dict['type'],
                  data_dict['slug_name'],
                  data_dict['image'],
                  data_dict['owner'],
                  data_dict['description'],
                  data_dict['language']
                  )
        session = context['session']
        session.add(ins)
        try:
            storeCodeFile(data_dict['codeFile'])
            MongoClient.insertReqForm(app_id=ins.app_id,
                                      var_name=data_dict['var_name'],
                                      label=data_dict['label'],
                                      type=data_dict['type'])
            session.commit()
        except:
            session.rollback()
            raise


def requestCreateServer(instance):
    url = '%s/app/new/server/%s' % (appserver_host, instance.app_id)
    print url
    response = requests.post(url)
    # return rps


def storeCodeFile(file):
    url = "http://localhost:5000/file/upload"
    if file.content_type == 'application/zip':
        if requests.post(url,
                         files={'file': file.read()}).status_code == 200:
            return True
        else:
            raise StoreFileException('Can not store file code.zip')
    else:
        raise StoreFileException('File not has a correct format')

    # url = '%s/app/new/batch/%s' % (appserver_host, instance.app_id)
    # uploader = CodeUploader(kwargs['codeFile'], kwargs['owner'], kwargs['slug_name'])
    # uploader.upload()
    # response = requests.post(url=url, data=kwargs['codeFile'].read()).json()


class StoreFileException(Exception):
    pass
