# encoding: utf-8
import random

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
from flask import Blueprint
from flask.views import MethodView
from ckanext.servicehub.model.ServiceModel import *

from ckanext.servicehub.model.ModelHelper import deleteAppARelevant, modifyApp

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

log = logging.getLogger(__name__)

is_org = False
appserver_host = config.get('ckan.servicehub.appserver_host')





def index():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'with_private': False
    }


    results = get_action(u'service_list')(context,dict())

    return base.render('service/index.html', dict(results=results,len=len(results)))





def read(id):
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    service_ins = get_action(u'service_show')(context, dict(id=id))
    req_form = get_action(u'service_req_form_show')(context, dict(id=id))
    print req_form
    extra_vars['req_form'] = req_form
    extra_vars['ins'] = service_ins
    extra_vars['appserver_host'] = appserver_host
    return base.render('service/read.html', extra_vars)


class  CreateServiceView(MethodView):
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
        try:
            data_dict = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
            data_dict.update(clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
            ))
            data_dict['service_type'] = 'Server'
            data_dict['slug_name'] = slug.slug(data_dict['app_name'])
            data_dict['owner'] = context['user']
            data_dict['status'] = 'Pending'
            data_dict['language'] = 'DockerImage'
            service = get_action(u'service_create')(context, data_dict)
        except (NotFound, NotAuthorized) as e:
            base.abort(404, _(u'Service not found'))
        except dict_fns.DataError:
            base.abort(400, _(u'Integrity Error'))

        return h.redirect_to(u'service.index')

    def get(self,
            data=None, errors=None, error_summary=None):
        extra_vars = {}
        context = self._prepare()
        data = data or {}
        if not data.get(u'image_url', u'').startswith(u'http'):
            data.pop(u'image_url', None)
        errors = errors or {}
        error_summary = error_summary or {}
        extra_vars = {
            u'data': data,
            u'errors': errors,
            u'error_summary': error_summary,
            u'action': u'new'
        }

        extra_vars["is_code"] = False;
        form = base.render(
            'service/new_service_form.html', extra_vars)

        g.form = form

        extra_vars["form"] = form
        return base.render('service/new.html', extra_vars)


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
        try:
            data_dict = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
            data_dict.update(clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
            ))

            print data_dict
            data_dict['service_type'] = 'Batch'
            data_dict['slug_name'] = slug.slug(data_dict['app_name'])
            data_dict['image'] = data_dict['slug_name']
            data_dict['owner'] = context['user']
            get_action(u'service_create')(context, data_dict)

        except (NotFound, NotAuthorized, ValidationError, dict_fns.DataError) as e:
            base.abort(404, _(u'Not found'))

        return h.redirect_to(u'service.index')

    def get(self):
        extra_vars = {}
        context = self._prepare()

        extra_vars["is_code"] = True;
        form = base.render(
            'service/new_service_form.html', extra_vars)
        g.form = form

        extra_vars["form"] = form
        return base.render('service/new.html', extra_vars)



service = Blueprint(u'service', __name__, url_prefix=u'/service')


def register_rules(blueprint):
    blueprint.add_url_rule(u'/', view_func=index, strict_slashes=False)
    blueprint.add_url_rule(
        u'/new',
        methods=[u'GET', u'POST'],
        view_func=CreateServiceView.as_view(str(u'new')))
    blueprint.add_url_rule(
        u'/new_from_code',
        methods=[u'GET', u'POST'],
        view_func=CreateFromCodeServiceView.as_view(str(u'new_from_code')))
    blueprint.add_url_rule(u'/<id>', methods=[u'GET'], view_func=read)


register_rules(service)

@service.route('/<string:id>/delete', methods=['GET','POST'])
def delete(id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
    }
    deleteAppARelevant(context[u'session'],id)
    return h.redirect_to(u'service.index')

@service.route('/<string:id>/manage', methods=['POST'])
def manage(id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
    }
    data_dict = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
    modifyApp(context[u'session'],id,**data_dict)
    return h.redirect_to(u'service.read',id=id)
