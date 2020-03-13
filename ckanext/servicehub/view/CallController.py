import ast

import requests
from werkzeug.datastructures import FileStorage

from ckan.lib import helpers
from flask import Blueprint, Response
import json
from ckanext.servicehub.model.ServiceModel import Call
import ckan.lib.base as base
from ckan import model, logic
from ckan.common import g, request, config
import ckan.lib.navl.dictization_functions as dict_fns
from ckan.logic import clean_dict, tuplize_dict, parse_params

get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
appserver_host = config.get('ckan.servicehub.appserver_host')

call_blueprint = Blueprint(u'call', __name__, url_prefix=u'/call')


def modify_input(data_dict):
    data_dict['ckan_resources']=data_dict.get('ckan_resources',[])
    ckan_resources=data_dict['ckan_resources'] if isinstance(data_dict['ckan_resources'],list) else [data_dict['ckan_resources']]

    data_dict['lst'] = data_dict.get('lst', [])
    lst = data_dict['lst'] if isinstance(data_dict['lst'], list) else [data_dict['lst']]

    data_dict['check_box_inputs']= data_dict.get('check_box_inputs', [])
    check_box_inputs = data_dict['check_box_inputs'] if isinstance(data_dict['check_box_inputs'], list) else [data_dict['check_box_inputs']]

    for resource in ckan_resources:
        package_id=data_dict['%s_package_id'%resource]
        resource_id=data_dict['%s_resource_id'%resource]
        file_name=data_dict['%s_file_name'%resource]
        del data_dict['%s_package_id'%resource]
        del data_dict['%s_resource_id'%resource]
        del data_dict['%s_file_name'%resource]
        data_dict[resource]="dataset/%s/resource/%s/download/%s"%(package_id,resource_id,file_name)
    for i in lst:
        data_dict[i]=data_dict[i] if isinstance(data_dict[i],list) else [data_dict[i]]
    for i in check_box_inputs:
        data_dict[i]=True if data_dict[i]=="on" else False

    del data_dict['check_box_inputs']
    del data_dict['lst']
    del data_dict['ckan_resources']
@call_blueprint.route('/create/<app_id>', methods=["POST"])
def create(app_id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True
    }
    data_dict = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
    data_dict.update(clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
    ))
    modify_input(data_dict)

    data_dict["app_id"]=app_id
    result_ins=get_action(u'call_create')(context, data_dict)
    get_action(u'push_request_call')(context, dict(call_id=result_ins['id']))

    return helpers.redirect_to('call.read',id=result_ins['id'])



@call_blueprint.route('/view', methods=["GET"])
def index():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    results = get_action(u'call_list')(context, dict())
    return base.render('call/index.html', dict(results=results, len=len(results)))
@call_blueprint.route('/read/<id>', methods=["GET"])
def read(id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    instance = get_action(u'call_show')(context, dict(id=id))
    input = get_action(u'input_show')(context, dict(call_id=id))
    output = get_action(u'output_show')(context, dict(call_id=id))
    service= get_action(u'service_show')(context, dict(id=instance['app_id']))
    return base.render('call/read.html', dict(ins=instance,input= input,output=output,service_ins=service))

