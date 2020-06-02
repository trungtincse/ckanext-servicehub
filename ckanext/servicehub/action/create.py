import errno
import json
import keyword
import mimetypes
import random
import string
from ckan.model import types as _types
import pika_pool
import requests
import logging

import slug

from ckanext.servicehub.error.exception import CKANException
from ckanext.servicehub.model.ServiceModel import App, Call, AppCategory, AppRelatedDataset, AppCodeVersion, AppParam
from flask import jsonify
from werkzeug.datastructures import FileStorage

import ckan.logic as logic

from ckan.common import config

import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ckanext.servicehub.action.read import service_by_slug_show

from ckanext.servicehub.action import get_item_as_list

# http_session = requests.Session()
# retry = Retry(connect=3, backoff_factor=0.5)
# adapter = HTTPAdapter(max_retries=retry)
# http_session.mount('http://', adapter)

log = logging.getLogger(__name__)
_get_or_bust = logic.get_or_bust

appserver_host = config.get('ckan.servicehub.appserver_host')
fileserver_host = config.get('ckan.servicehub.fileserver_host')
storage_path = config.get('ckan.storage_path')
logger = logging.getLogger('logserver')


def isidentifier(ident):
    """Determines if string is valid Python identifier."""

    ident = str(ident)

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


def service_create(context, data_dict):
    session = context['session']
    model = context['model']
    data_dict['owner'] = context['user']
    data_dict['slug_name'] = slug.slug(data_dict['app_name'])
    data_dict['image'] = data_dict['slug_name']
    data_dict['datasets'] = get_item_as_list(data_dict, 'datasets')
    data_dict['var_name'] = get_item_as_list(data_dict, 'var_name')
    data_dict['label'] = get_item_as_list(data_dict, 'label')
    data_dict['type'] = get_item_as_list(data_dict, 'type')
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
    app_id = _types.make_uuid()
    type = mimetypes.guess_type(data_dict['avatar'].filename)
    if type[0] != None and type[0].find('image') >= 0:
        avatar_path = os.path.join(storage_path, 'avatars', app_id)
        if not os.path.exists(os.path.dirname(avatar_path)):
            try:
                os.makedirs(os.path.dirname(avatar_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        data_dict['avatar'].save(avatar_path)
    else:
        return dict(success=False, error="Avatar is not image format")

    app_dict = dict(app_id=app_id,
                    app_name=data_dict['app_name'],
                    avatar_path=avatar_path,
                    organization=data_dict['organization'],
                    slug_name=data_dict['slug_name'],
                    type='BATCH',
                    owner=data_dict['owner'],
                    description=data_dict['description'],
                    language=data_dict['language'])
    ####
    params = makeReqFormJSON(
        var_name=data_dict['var_name'],
        label=data_dict['label'],
        type=data_dict['type'])
    try:
        session = context['session']
        app = App()

        app.setOption(**app_dict)
        session.add(app)
        session.flush()
        # logger.info('app_id=%s&message=Application %s creating success.' % (app_id, app_dict['app_name']))
        code_id = build_code(session, data_dict['codeFile'], app)
    except Exception as ex:
        logger.error(ex.message)
        session.delete(app)
        session.commit()
        return dict(success=False, error='Creating application is not success: ' + str(ex.message))

    logger.info('Build app success, app_id=%s, code_id=%s' % (app_id, code_id))

    logic.get_action('app_index')({}, {
        'id': app.app_id,
        'name': app.app_name,
        'language': app.language,
        'organization': session.query(model.Group.id == app.organization).first(),
        'owner': session.query(model.User.id == app.owner).first(),
        'categories': session.query(AppCategory.app_id == app_id).all(),
        'description': app.description,
    })

    # success
    for param in params:
        param_dict = dict(app_id=app_id,
                          label=param['label'],
                          name=param['name'],
                          type=param['type'])
        param_ins = AppParam()
        param_ins.setOption(**param_dict)
        session.add(param_ins)

    for dataset in data_dict['datasets']:
        package = model.Package.get(dataset)
        ins = AppRelatedDataset(app_id=app_id, package_id=package.id)
        session.add(ins)

    for i in data_dict['app_category']:
        ins = AppCategory(app_id=app_id, tag_name=i)
        session.add(ins)
    session.commit()
    return dict(success=True, code_id=code_id, app_id=app_id)



class BuildAppFailed(Exception):
    pass

def build_code(session, code_file, app):
    code_id = _types.make_uuid()
    app_id = app.app_id
    slug_name = app.slug_name
    type = mimetypes.guess_type(code_file.filename)
    if type[0] != None and type[0].find('zip') >= 0:
        code_path = os.path.join(storage_path, 'codes', code_id)
        if not os.path.exists(os.path.dirname(code_path)):
            try:
                os.makedirs(os.path.dirname(code_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        assert code_path != None
        code_file.save(code_path)
    else:
        return dict(success=False, error="Code file is not zip format")
    code_dict = dict(
        code_id=code_id,
        app_id=app_id,
        code_path=code_path,
        image=slug_name
    )
    code = AppCodeVersion()
    code.setOption(**code_dict)
    try:
        session.add(code)

        build_url = os.path.join(appserver_host, 'app', app_id, code_id, 'build')
        # WILL DO
        session.commit() # make appserver see code version
        r = requests.post(build_url).json()
        if r['error']:
            session.delete(code)
            raise BuildAppFailed(r['error'])

        # success
        app.curr_code_id = code_id
        session.add(app)
        session.commit()

        return code_id
    except Exception as ex:
        session.delete(code)
        raise


def makeReqFormJSON(**kwargs):
    label = kwargs['label'] if isinstance(kwargs['label'], list) else [kwargs['label']]
    var_name = kwargs['var_name'] if isinstance(kwargs['var_name'], list) else [kwargs['var_name']]
    type = kwargs['type'] if isinstance(kwargs['type'], list) else [kwargs['type']]
    return [dict(label=x[0], name=x[1], type=x[2]) for x in
            zip(label, var_name, type)]


def call_create(context, data_dict):
    session = context['session']
    user = context['user']
    app_id = data_dict.get('app_id', None)
    if app_id == None:
        return dict(success=False, error="Miss app_id field.")
    if isinstance(app_id,list):
        return dict(success=False, error="Duplicate app_id.")
    app = session.query(App).filter(App.app_id == app_id).first()
    if app == None:
        return dict(success=False, error="Application not found.")
    curr_code_id = app.curr_code_id
    assert curr_code_id != None
    del data_dict['app_id']
    files = {}
    param_inses = session.query(AppParam).filter(AppParam.app_id == app_id).all()
    ### validate
    for ins in param_inses:
        param_value = data_dict.get(ins.name, None)
        if param_value == None:
            return dict(success=False, error="Parameter not found.")
        if ins.type.find("FILE") >= 0 :
            if not isinstance(param_value, FileStorage):
                return dict(success=False, error="Parameter %s is not a %s type." % (ins.name,ins.type))
        elif ins.type.find("LIST") >= 0:
            if not isinstance(param_value, list):
                data_dict[ins.name]=[param_value]
                param_value=[param_value]
            for e in param_value:
                if not isinstance(e,unicode):
                    return dict(success=False, error="Parameter %s is not a %s type." % (ins.name,ins.type))
        elif ins.type.find("BOOLEAN") >= 0:
            if not isinstance(param_value, unicode) or param_value.lower() not in ['false', 'true']:
                return dict(success=False, error="Parameter %s is not a %s type." % (ins.name, ins.type))
        else:
            if not isinstance(param_value, unicode):
                return dict(success=False, error="Parameter %s is not a %s type." % (ins.name, ins.type))
    ####
    for k, v in data_dict.items():
        if isinstance(v, FileStorage):
            files[k] = (k, v.read())
        elif isinstance(v, list):
            files[k] = (None, json.dumps(v))
        else:
            files[k] = (None, v)
    path = os.path.join(appserver_host, 'app', app_id, curr_code_id, 'execute') + '?userId=%s' % user
    response = requests.post(path, files=files)
    return response.json()


def storeInput(file, call_id):
    input_file = file
    file_name = input_file.filename
    path = os.path.join(fileserver_host, 'file', 'input', call_id, file_name)
    requests.post(path,
                  files=dict(file=input_file.read())
                  )
    return path


def storeOutput(file, call_id):
    output_file = file
    file_name = output_file.filename
    path = os.path.join(fileserver_host, 'file', 'output', call_id, file_name)
    requests.post(path,
                  files=dict(file=output_file.read())
                  )
    return path


public_functions = dict(service_create=service_create,
                        call_create=call_create,
                        # push_request_call=push_request_call
                        )
