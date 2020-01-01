import requests

from ckan.lib import helpers
from flask import Blueprint
import json
# from ckanext.servicehub.model.ServiceModel import AppResult
from ckanext.servicehub.model.ServiceModel import Session
from ckanext.servicehub.model.ServiceModel import Call
import ckan.lib.base as base
from ckan import model
from ckan.common import g, request
import ckan.lib.navl.dictization_functions as dict_fns
from ckan.logic import clean_dict, tuplize_dict, parse_params
import os
appserver_host='http://0.0.0.0:5001'
# host= os.getenv('APP_SERVER_HOST')
# appserver_host='http://%s'%host

call_blueprint = Blueprint(u'call', __name__, url_prefix=u'/call')

@call_blueprint.route('/create',methods=["POST"])
def create():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True
    }
    user = context['user']
    session=context['session']


    data_dict = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
    data_dict.update(clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
    ))

    data=dict(zip(data_dict['custom_key'], data_dict['custom_value']))
    files=data_dict['binary_input'] if 'binary_input' in data_dict else None
    # print data_dict
    ins=Call(user,data_dict["app_id"],"Pending");
    session.add(ins)
    requestCallBatch(ins,data,files)
    session.commit()
    # return helpers.redirect_to('service.read',id=data_dict["app_id"])
    # return helpers.redirect_to('service.index')
    return helpers.redirect_to('service_user.user_service_request',user=user)
def requestCallBatch(instance,data,files=None):
    # url= '%s/execute/batch/%s'%(appserver_host,instance.call_id)
    # print data
    # print type(files)
    url= 'http://0.0.0.0:5000/test/empty'
    file_data = {
        'json':(None,json.dumps(data)),
    }
    if files!=None:
        file_data['binary']=(None,files,'application/octet-stream')
    rps=requests.post(url,files=file_data)
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
