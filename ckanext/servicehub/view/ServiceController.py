# encoding: utf-8
import collections
import keyword
import random
import string

import slug
import yaml
import json
import logging
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
from ckan.common import OrderedDict, c, g, config, request, _
from flask import Blueprint, jsonify
from flask.views import MethodView
from ckanext.servicehub.model.ServiceModel import *

from ckanext.servicehub.model.ServiceModel import App

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

log = logging.getLogger(__name__)

appserver_host = config.get('ckan.servicehub.appserver_host')

import ast





def index():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'with_private': False
    }

    results = get_action(u'service_list')(context, dict())
    return base.render('service/index.html', dict(results=results, len=len(results), appserver_host=appserver_host))


def read(id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    service_ins = get_action(u'service_show')(context, dict(id=id))
    if service_ins.get('error', '') != '':
        base.abort(404, _(u'Service not found'))

    return base.render('service/read.html', dict(ins=service_ins.get('app_detail')))


class CreateFromCodeServiceView(MethodView):
    u'''Create service view '''

    def _prepare(self, data=None):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user
        }

        return context


    def post(self):
        context = self._prepare()
        context['userobj'] = g.userobj
        try:
            data_dict = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
            data_dict.update(clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
            ))
            data_dict['app_category']=data_dict['app_category'].split(',')
            message = get_action(u'service_create')(context, data_dict)

        except (NotFound, NotAuthorized, ValidationError, dict_fns.DataError) as e:
            base.abort(404, _(u'Not found'))
        print message
        return jsonify(message)

    def get(self):
        extra_vars = {}
        context = self._prepare()
        context['userobj']=g.userobj
        model=context['model']
        # print logic.get_action('package_show')(context,dict(id='covid-191'))
        # assert False
        extra_vars["is_code"] = True;
        extra_vars['app_category']=model.Vocabulary.by_name('app_category').tags.all()
        extra_vars['groups']=filter(lambda x: x.state=='active' and x.is_organization,g.userobj.get_groups())
        form = base.render(
            'service/new_service_form.html', extra_vars)
        g.form = form
        extra_vars["form"] = form
        return base.render('service/new.html', extra_vars)


service = Blueprint(u'service', __name__, url_prefix=u'/service')


def register_rules(blueprint):
    blueprint.add_url_rule(u'/', view_func=index, strict_slashes=False)
    # blueprint.add_url_rule(
    #     u'/new',
    #     methods=[u'GET', u'POST'],
    #     view_func=CreateServiceView.as_view(str(u'new')))
    blueprint.add_url_rule(
        u'/new',
        methods=[u'GET', u'POST'],
        view_func=CreateFromCodeServiceView.as_view(str(u'new')))
    blueprint.add_url_rule(u'/<id>', methods=[u'GET'], view_func=read)


register_rules(service)


@service.route('/<string:id>/delete', methods=['GET', 'POST'])
def delete(id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
    }
    get_action(u'service_delete')(context, dict(id=id))
    return h.redirect_to(u'service.index')


@service.route('/<string:id>/monitor', methods=['GET'])
def monitor(id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    service_ins = get_action(u'service_show')(context, dict(id=id))
    if service_ins.get('error', '') != '':
        base.abort(404, _(u'Service not found'))

    return base.render('service/monitor.html', dict(ins=service_ins.get('app_detail')))


@service.route('/<string:id>/setting', methods=['POST'])
def setting(id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    data_dict = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
    session = context['session']
    try:
        ins = session.query(App).filter(App.app_id == id).first()
        if ins == None:
            ex = Exception()
            ex.message = "Application not found"
            raise ex
        ins.sys_status = data_dict.get('mode', ins.sys_status)
        ins.description = data_dict.get('description', ins.description)
        session.add(ins)
        session.commit()
    except Exception as ex:
        session.rollback()
        error = getattr(ex, "err_message", 'Opps! Something is wrong')
        return jsonify(dict(success=False, error=error))
    return jsonify(dict(success=True))
