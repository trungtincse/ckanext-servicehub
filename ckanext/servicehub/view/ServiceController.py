# encoding: utf-8
import collections
import errno
import keyword
import mimetypes
import os
import random
import string
from pprint import pprint

import slug
import json
import logging
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
from ckanext.servicehub.action.create import build_code
from ckan.common import OrderedDict, c, g, config, request, _
from flask import Blueprint, jsonify, send_file
from flask.views import MethodView

from ckanext.servicehub.main.config_and_common import ServiceLanguage
from ckanext.servicehub.model.ServiceModel import *
from ckan.model import types as _types
from ckanext.servicehub.model.ServiceModel import App
from ckanext.servicehub.view import app_search_supporter
from ckanext.servicehub.auth.show import list_all_services_of_user
import ckan.authz as authz
import ckan.logic

storage_path = config.get('ckan.storage_path')
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
_check_access = ckan.logic.check_access
# log = logging.getLogger(__name__)
logger = logging.getLogger('logserver')

appserver_host = config.get('ckan.servicehub.appserver_host')
logserver_host = config.get('ckan.servicehub.logserver_host')

import ast


def index():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'with_private': False
    }

    # results = get_action(u'service_list')(context, dict())
    # return base.render('service/index.html', dict(results=results, len=len(results), appserver_host=appserver_host))
    return app_search_supporter.index()


def read(id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        _check_access('service_show', context, dict(app_id=id))
    except Exception as ex:
        return base.abort(404, _(u'Page not found'))
    service_ins = get_action(u'service_show')(context, dict(id=id))
    if service_ins.get('error', '') != '':
        base.abort(404, _(u'Service not found'))

    return base.render('service/read.html', dict(ins=service_ins))


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
            data_dict['app_category'] = data_dict['app_category'].split(',')
            message = get_action(u'service_create')(context, data_dict)
            url_create_dashboard = os.path.join(logserver_host, "kibana", "createDashboardSearch",
                                                slug.slug(data_dict['app_name']))
            setting=dict(index="ckan",fields=["@timestamp","message"],
                         condition="user:%s and app_name:%s"%(context['user'],slug.slug(data_dict['app_name'])))
            try:
                request.post(url_create_dashboard,json=setting)
            except:
                pass
            # logger.info("app_id=%s&message=Application %s start to create")
        except (NotFound, NotAuthorized, ValidationError, dict_fns.DataError) as e:
            base.abort(404, _(u'Not found'))
        return jsonify(message)

    def get(self):
        extra_vars = {}
        context = self._prepare()
        context['userobj'] = g.userobj
        model = context['model']
        # print logic.get_action('package_show')(context,dict(id='covid-191'))
        # assert False
        extra_vars["is_code"] = True
        extra_vars['app_category'] = model.Vocabulary.by_name('app_category').tags.all()
        if g.userobj == None:
            base.abort(404, _(u'Page not found'))
        extra_vars['groups'] = filter(lambda x: x.state == 'active' and x.is_organization, g.userobj.get_groups())
        has_create_app = authz.has_user_permission_for_some_org(context['user'], 'create_service')
        if not has_create_app:
            base.abort(404, _(u'User %s can not create application') % context['user'])
        extra_vars['languages'] = ({'text': language.ui_text, 'value': language.appserver_value} for language in
                                   ServiceLanguage)
        form = base.render(
            'service/new_service_form.html', extra_vars)
        g.form = form
        extra_vars["form"] = form
        return base.render('service/new.html', extra_vars)


service = Blueprint(u'service', __name__, url_prefix=u'/service')


def register_rules(blueprint):
    blueprint.add_url_rule(u'', view_func=index, strict_slashes=True)
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
    try:
        _check_access('service_monitor', context, dict(app_id=id))
    except Exception as ex:
        base.abort(404, _(u'Page not found'))
    service_ins = get_action(u'service_show')(context, dict(id=id))
    if service_ins.get('error', '') != '':
        base.abort(404, _(u'Service not found'))

    return base.render('service/monitor.html', dict(ins=service_ins))


@service.route('/<string:id>/code', methods=['GET'])
def code(id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        _check_access('service_monitor', context, dict(app_id=id))
    except Exception as ex:
        base.abort(404, _(u'Page not found'))
    service_ins = get_action(u'service_show')(context, dict(id=id))
    if service_ins.get('error', '') != '':
        base.abort(404, _(u'Service not found'))

    return base.render('service/code.html', dict(ins=service_ins))


@service.route('/<string:id>/code/ajax', methods=['GET'])
def code_ajax(id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        _check_access('service_monitor', context, dict(app_id=id))
    except Exception as ex:
        base.abort(404, _(u'Page not found'))
    service_ins = get_action(u'service_show')(context, dict(id=id))
    session = context['session']
    if service_ins.get('error', '') != '':
        base.abort(404, _(u'Service not found'))
    code_ins_lst = session.query(AppCodeVersion).filter(AppCodeVersion.app_id == id).all()
    code_lst = map(
        lambda code: [code.code_id, code.created_at, "YES" if code.code_id == service_ins['curr_code_id'] else "",
                      '/service/%s/code/%s' % (id, code.code_id), ], code_ins_lst)
    return jsonify(code_lst)


@service.route('/<string:id>/code/<string:code_id>', methods=['GET'])
def get_code(id, code_id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        _check_access('service_monitor', context, dict(app_id=id))
    except Exception as ex:
        base.abort(404, _(u'Page not found'))
    service_ins = get_action(u'service_show')(context, dict(id=id))
    session = context['session']
    if service_ins.get('error', '') != '':
        base.abort(404, _(u'Service not found'))
    code = session.query(AppCodeVersion).filter(
        AppCodeVersion.app_id == id and AppCodeVersion.code_id == code_id).first()
    if code == None:
        base.abort(404, _(u'Code not found'))
    return send_file(code.code_path)


@service.route('/<string:id>/setting', methods=['POST'])
def setting(id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        _check_access('update_service', context, dict(app_id=id))
    except Exception as ex:
        base.abort(404, _(u'Page not found'))
    data_dict = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
    session = context['session']
    try:
        ins = session.query(App).filter(App.app_id == id).first()
        if ins == None:
            ex = Exception()
            ex.message = "Application not found"
            raise ex
        app_id = ins.app_id
        log_app_status = ins.app_status
        log_description = ins.description
        log_curr_code_id = ins.curr_code_id
        ins.app_status = data_dict.get('mode', ins.app_status)
        ins.description = data_dict.get('description', ins.description)
        ins.curr_code_id = data_dict.get('version', ins.curr_code_id)
        session.add(ins)
        session.commit()
        if log_app_status != ins.app_status:
            logger.info('app_id=%s&message=Mode is updated.' % app_id)
        if log_description != ins.description:
            logger.info('app_id=%s&message=Description is updated.' % app_id)
        if log_curr_code_id != ins.curr_code_id:
            logger.info('app_id=%s&message=Version of source code is updated.' % app_id)
    except Exception as ex:
        session.rollback()
        error = getattr(ex, "err_message", 'Opps! Something is wrong')
        return jsonify(dict(success=False, error=error))
    return jsonify(dict(success=True))


@service.route('/<string:id>/avatar', methods=['GET'])
def getAvatar(id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    session = context['session']
    try:
        ins = session.query(App).filter(App.app_id == id).first()
        if ins == None:
            ex = Exception()
            ex.message = "Application not found"
            raise ex
        file_path = ins.avatar_path
        return send_file(file_path)
    except Exception as ex:
        print ex
        error = getattr(ex, "err_message", 'Opps! Something is wrong')
        return jsonify(dict(success=False, error=error))
    # return jsonify(dict(success=True))


@service.route('/<string:id>/update', methods=['POST'])
def update(id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        _check_access('update_service', context, dict(app_id=id))
    except Exception as ex:
        base.abort(404, _(u'Page not found'))
    data_dict = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
    data_dict.update(clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
    ))
    session = context['session']
    try:
        app = session.query(App).filter(App.app_id == id).first()
        if app == None:
            raise
    except:
        base.abort(404, _(u'Service not found'))
    try:
        build_code(session, data_dict['codeFile'], app)
    except Exception as ex:
        session.rollback()
        error = getattr(ex, "err_message", 'Opps! Something is wrong')
        return jsonify(dict(success=False, error=error))
    return jsonify(dict(success=True))
