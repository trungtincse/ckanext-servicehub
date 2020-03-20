import json
import random

import pika_pool
import requests
import logging
from ckanext.servicehub.model.ServiceModel import App, Call
from flask import jsonify
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


def push_request_call(context, data_dict):
    with pool.acquire() as cxn:
        cxn.channel.queue_declare(queue='call_request', durable=True)
        cxn.channel.basic_publish(exchange='',
                                  routing_key='call_request',
                                  body=data_dict['call_id'])


def service_create(context, data_dict):
    data_dict['owner'] = context['user']

    # session = context['session']
    params = makeReqFormJSON(
        var_name=data_dict.get('var_name', []),
        label=data_dict.get('label', []),
        type=data_dict.get('type', []))
    app_dict = dict(app_name=data_dict['app_name'],
                    # data_dict['service_type'],
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
    return response.json()


def makeReqFormJSON(**kwargs):
    label = kwargs['label'] if isinstance(kwargs['label'], list) else [kwargs['label']]
    var_name = kwargs['var_name'] if isinstance(kwargs['var_name'], list) else [kwargs['var_name']]
    type = kwargs['type'] if isinstance(kwargs['type'], list) else [kwargs['type']]
    return [dict(label=x[0], name=x[1], type=x[2]) for x in
            zip(label, var_name, type)]



def call_create(context, data_dict):
    # session = context['session']
    user = context['user']
    app_id= data_dict['app_id']
    del data_dict['app_id']
    files = {}
    for k, v in data_dict.items():
        print k
        if isinstance(v, FileStorage):
            print k,v
            files[k] = (k, v.read())
        elif isinstance(v, list) :
            files[k]=(None,json.dumps(v))
        else:
            files[k] = (None, v)
    path = os.path.join(appserver_host, 'app', app_id, 'execute')+'?userId=%s'%user
    response=http_session.post(path, files=files)
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
