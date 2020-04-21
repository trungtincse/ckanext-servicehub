import json
import keyword
import random
import string

import pika_pool
import requests
import logging

import slug
from ckanext.servicehub.model.ServiceModel import App, Call, AppCategory, AppRelatedDataset
from flask import jsonify
from werkzeug.datastructures import FileStorage

import ckan.logic as logic

from ckan.common import config

import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ckanext.servicehub.action.read import service_by_slug_show

from ckanext.servicehub.action import get_item_as_list

http_session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
http_session.mount('http://', adapter)

log = logging.getLogger(__name__)
_get_or_bust = logic.get_or_bust

appserver_host = config.get('ckan.servicehub.appserver_host')
fileserver_host = config.get('ckan.servicehub.fileserver_host')
import pika

credentials = pika.PlainCredentials('bpnkxscx', 'HJsvGjpmQdDrJiVuw5w36F1lWr63sEkR')
parameters = pika.ConnectionParameters('mustang.rmq.cloudamqp.com',
                                       5672,
                                       'bpnkxscx',
                                       credentials,
                                       connection_attempts=2, socket_timeout=10)
# connection = pika.BlockingConnection(parameters)
# params = pika.URLParameters(
#     'amqp://bpnkxscx:HJsvGjpmQdDrJiVuw5w36F1lWr63sEkR@mustang.rmq.cloudamqp.com/bpnkxscx'
#     'socket_timeout=10&'
#     'connection_attempts=2'
# )

pool = pika_pool.QueuedPool(
    create=lambda: pika.BlockingConnection(parameters=parameters),
    max_size=10,
    max_overflow=10,
    timeout=10,
    recycle=3600,
    stale=45,
)

def isidentifier(ident):
    """Determines if string is valid Python identifier."""

    ident=str(ident)

    if not ident:
        return False

    if keyword.iskeyword(ident):
        return False

    first = '_' + string.lowercase + string.uppercase
    if ident[0] not in first:
        return False

    other = first + string.digits
    for ch in ident[1:]:
        if ch not in other:
            return False

    return True
def push_request_call(context, data_dict):
    with pool.acquire() as cxn:
        cxn.channel.queue_declare(queue='call_request', durable=True)
        cxn.channel.basic_publish(exchange='',
                                  routing_key='call_request',
                                  body=data_dict['call_id'])


def service_create(context, data_dict):
    session = context['session']
    model = context['model']
    data_dict['owner'] = context['user']
    data_dict['slug_name'] = slug.slug(data_dict['app_name'])
    data_dict['image'] = data_dict['slug_name']
    data_dict['datasets'] = get_item_as_list(data_dict,'datasets')
    data_dict['var_name'] = get_item_as_list(data_dict,'var_name')
    data_dict['label'] = get_item_as_list(data_dict,'label')
    data_dict['type'] = get_item_as_list(data_dict,'type')
    ############ validate
    app_name_exist = session.query(App).filter(App.slug_name == data_dict['slug_name']).first() != None
    if app_name_exist:
        return dict(success=False, error="Service name exists")
    groups = filter(lambda x: x.state == 'active' and x.is_organization, context['userobj'].get_groups())
    if data_dict['organization'] not in map(lambda x: x.title, groups):
        return dict(success=False, error="User is not a member of the organization")
    if not all([isidentifier(i) for i in data_dict['var_name']]):
        return dict(success=False, error="Variable names are not accepted")
    for dataset in data_dict['datasets']:
        try:
            logic.get_action('package_show')(context, dict(id=dataset))
        except:
            return dict(success=False, error="Dataset not found")
    #############
    params = makeReqFormJSON(
        var_name=data_dict['var_name'],
        label=data_dict['label'],
        type=data_dict['type'])
    app_dict = dict(app_name=data_dict['app_name'],
                    organization=data_dict['organization'],
                    slug_name=data_dict['slug_name'],
                    image=data_dict['image'],
                    owner=data_dict['owner'],
                    description=data_dict['description'],
                    language=data_dict['language'],
                    params=params)
    path = appserver_host + "/app/create"
    response = http_session.post(path, files={
        'app_info': (None, json.dumps(app_dict)),
        'code_file': ('code.zip', data_dict['codeFile'].read()),
        'avatar_file': ('avatar', data_dict['avatar'].read())
    })
    #############
    print response.json()
    if 'error' in response.json().keys() and response.json()['error']:
        return dict(success=False, error=response.json()['error'])
    if 'app_id' in response.json().keys():
        for dataset in data_dict['datasets']:
            package = model.Package.get(dataset)
            ins= AppRelatedDataset(app_id=response.json()['app_id'],package_id=package.id)
            session.add(ins)
        for i in data_dict['app_category']:
            ins = AppCategory(app_id=response.json()['app_id'], tag_name=i)
            session.add(ins)
        try:
            session.commit()
        except:
            session.rollback()
        ###### ###########
    return dict(success=True)


def makeReqFormJSON(**kwargs):
    label = kwargs['label'] if isinstance(kwargs['label'], list) else [kwargs['label']]
    var_name = kwargs['var_name'] if isinstance(kwargs['var_name'], list) else [kwargs['var_name']]
    type = kwargs['type'] if isinstance(kwargs['type'], list) else [kwargs['type']]
    return [dict(label=x[0], name=x[1], type=x[2]) for x in
            zip(label, var_name, type)]


def call_create(context, data_dict):
    # session = context['session']
    user = context['user']
    app_id = data_dict['app_id']
    del data_dict['app_id']
    files = {}
    for k, v in data_dict.items():
        if isinstance(v, FileStorage):
            files[k] = (k, v.read())
        elif isinstance(v, list):
            files[k] = (None, json.dumps(v))
        else:
            files[k] = (None, v)
    path = os.path.join(appserver_host, 'app', app_id, 'execute') + '?userId=%s' % user
    response = http_session.post(path, files=files)
    # print files
    # print response.json()
    return response.json()


def storeInput(file, call_id):
    input_file = file
    file_name = input_file.filename
    path = os.path.join(fileserver_host, 'file', 'input', call_id, file_name)
    http_session.post(path,
                      files=dict(file=input_file.read())
                      )
    return path


def storeOutput(file, call_id):
    output_file = file
    file_name = output_file.filename
    path = os.path.join(fileserver_host, 'file', 'output', call_id, file_name)
    http_session.post(path,
                      files=dict(file=output_file.read())
                      )
    return path


public_functions = dict(service_create=service_create,
                        call_create=call_create,
                        push_request_call=push_request_call
                        )
