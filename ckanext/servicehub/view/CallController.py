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


@call_blueprint.route('/create/<app_id>', methods=["POST"])
def create(app_id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True
    }
    # user = context['user']
    # session = context['session']

    data_dict = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
    data_dict.update(clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
    ))
    data_dict["app_id"]=app_id
    get_action(u'call_create')(context, data_dict)

    # requestCallBatch(ins, json, files)

    return helpers.redirect_to('call.index')


def requestCallBatch(instance, data, files=None):
    url = '%s/execute/batch/%s' % (appserver_host, instance.call_id)
    file_data = {
        'json': (None, json.dumps(data)),
    }
    if files != None:
        file_data['binary'] = (None, files.read())
    rps = requests.post(url, files=file_data)
    pretty_print_POST(rps.request)


# @call_blueprint.route('/empty',methods=["POST"])

def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.
    """
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))

@call_blueprint.route('/view', methods=["GET"])
def index():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    results = get_action(u'call_list')(context, dict())
    print results
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
    return base.render('call/read.html', dict(ins=instance,input= input,output=output))

