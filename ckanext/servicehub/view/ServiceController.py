# encoding: utf-8
import random

import slug
import yaml
import json
import logging
import re
from urllib import urlencode
import ckan.plugins as plugins
from six import string_types, text_type
import requests
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.lib.search as search
import ckan.model as model
import ckan.lib.plugins as lib_plugins
from ckan.common import OrderedDict, c, g, config, request, _
from flask import Blueprint
from flask.views import MethodView
from ckanext.servicehub.model.ServiceModel import *

from ckanext.servicehub.model.ModelHelper import deleteAppARelevant

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

log = logging.getLogger(__name__)

lookup_group_plugin = lib_plugins.lookup_group_plugin
lookup_group_controller = lib_plugins.lookup_group_controller
is_org = False
appserver_host = config.get('ckan.servicehub.appserver_host')


def _index_template(group_type):
    return lookup_group_plugin(group_type).index_template()


def _db_to_form_schema(group_type=None):
    u'''This is an interface to manipulate data from the database
     into a format suitable for the form (optional)'''
    return lookup_group_plugin(group_type).db_to_form_schema()


def _setup_template_variables(context, data_dict, group_type=None):
    if u'type' not in data_dict:
        context[u'group'] = group_type
    return lookup_group_plugin(group_type). \
        setup_template_variables(context, data_dict)


def _replace_group_org(string):
    u''' substitute organization for group if this is an org'''
    if is_org:
        return re.sub(u'^group', u'organization', string)
    return string


def _action(action_name):
    u''' select the correct group/org action '''
    return get_action(_replace_group_org(action_name))


def _check_access(action_name, *args, **kw):
    u''' select the correct group/org check_access '''
    return check_access(_replace_group_org(action_name), *args, **kw)


def set_org(is_organization):
    global is_org
    is_org = is_organization


def index(group_type, is_organization):
    group_type = u'service'
    extra_vars = {}
    set_org(is_organization)
    page = h.get_page_number(request.params) or 1
    items_per_page = int(config.get(u'ckan.datasets_per_page', 20))

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'with_private': False
    }

    try:
        _check_access(u'site_read', context)
        # _check_access(u'service_list', context)
    except NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    q = request.params.get(u'q', u'')
    sort_by = request.params.get(u'sort')

    # TODO: Remove
    g.q = q
    g.sort_by_selected = sort_by

    extra_vars["q"] = q
    extra_vars["sort_by_selected"] = sort_by

    if g.userobj:
        context['user_id'] = g.userobj.id
        context['user_is_admin'] = g.userobj.sysadmin

    try:
        data_dict_global_results = {
            u'all_fields': False,
            u'q': q,
            u'sort': sort_by,
            u'type': u'service',
        }
        global_results = _action(u'service_list')(context,
                                                  data_dict_global_results)
    except ValidationError as e:
        if e.error_dict and e.error_dict.get(u'message'):
            msg = e.error_dict['message']
        else:
            msg = str(e)
        h.flash_error(msg)
        extra_vars["page"] = h.Page([], 0)
        extra_vars["group_type"] = group_type
        return base.render(_index_template(group_type), extra_vars)

    data_dict_page_results = {
        u'all_fields': True,
        u'q': q,
        u'sort': sort_by,
        u'type': group_type,
        u'limit': items_per_page,
        u'offset': items_per_page * (page - 1),
        u'include_extras': True
    }
    page_results = _action(u'service_list')(context, data_dict_page_results)

    extra_vars["page"] = h.Page(
        collection=global_results,
        page=page,
        url=h.pager_url,
        items_per_page=items_per_page, )

    extra_vars["page"].items = page_results
    extra_vars["group_type"] = group_type

    # TODO: Remove
    g.page = extra_vars["page"]
    return base.render('service/index.html', extra_vars)


def _update_facet_titles(facets, group_type):
    for plugin in plugins.PluginImplementations(plugins.IFacets):
        facets = plugin.group_facets(facets, group_type, None)


def _read(id, limit, group_type):
    u''' This is common code used by both read and bulk_process'''
    extra_vars = {}
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'schema': _db_to_form_schema(group_type=group_type),
        u'for_view': True,
        u'extras_as_string': True
    }

    q = request.params.get(u'q', u'')

    # TODO: Remove
    # ckan 2.9: Adding variables that were removed from c object for
    # compatibility with templates in existing extensions
    g.q = q

    # Search within group
    if g.group_dict.get(u'is_organization'):
        fq = u' owner_org:"%s"' % g.group_dict.get(u'id')
    else:
        fq = u' groups:"%s"' % g.group_dict.get(u'name')

    extra_vars["q"] = q

    g.description_formatted = \
        h.render_markdown(g.group_dict.get(u'description'))

    context['return_query'] = True

    page = h.get_page_number(request.params)

    # most search operations should reset the page counter:
    params_nopage = [(k, v) for k, v in request.params.items() if k != u'page']
    sort_by = request.params.get(u'sort', None)

    def search_url(params):
        controller = lookup_group_controller(group_type)
        action = u'bulk_process' if getattr(
            g, u'action', u'') == u'bulk_process' else u'read'
        url = h.url_for(u'.'.join([controller, action]), id=id)
        params = [(k, v.encode(u'utf-8')
        if isinstance(v, string_types) else str(v))
                  for k, v in params]
        return url + u'?' + urlencode(params)

    def drill_down_url(**by):
        return h.add_url_param(
            alternative_url=None,
            controller=u'group',
            action=u'read',
            extras=dict(id=g.group_dict.get(u'name')),
            new_params=by)

    extra_vars["drill_down_url"] = drill_down_url

    def remove_field(key, value=None, replace=None):
        controller = lookup_group_controller(group_type)
        return h.remove_url_param(
            key,
            value=value,
            replace=replace,
            controller=controller,
            action=u'read',
            extras=dict(id=g.group_dict.get(u'name')))

    extra_vars["remove_field"] = remove_field

    def pager_url(q=None, page=None):
        params = list(params_nopage)
        params.append((u'page', page))
        return search_url(params)

    try:
        extra_vars["fields"] = fields = []
        extra_vars["fields_grouped"] = fields_grouped = {}
        search_extras = {}
        for (param, value) in request.params.items():
            if param not in [u'q', u'page', u'sort'] \
                and len(value) and not param.startswith(u'_'):
                if not param.startswith(u'ext_'):
                    fields.append((param, value))
                    q += u' %s: "%s"' % (param, value)
                    if param not in fields_grouped:
                        fields_grouped[param] = [value]
                    else:
                        fields_grouped[param].append(value)
                else:
                    search_extras[param] = value

        # TODO: Remove
        # ckan 2.9: Adding variables that were removed from c object for
        # compatibility with templates in existing extensions
        g.fields = fields
        g.fields_grouped = fields_grouped

        facets = OrderedDict()

        default_facet_titles = {
            u'organization': _(u'Organizations'),
            u'groups': _(u'Groups'),
            u'tags': _(u'Tags'),
            u'res_format': _(u'Formats'),
            u'license_id': _(u'Licenses')
        }

        for facet in h.facets():
            if facet in default_facet_titles:
                facets[facet] = default_facet_titles[facet]
            else:
                facets[facet] = facet

        # Facet titles
        _update_facet_titles(facets, group_type)

        extra_vars["facet_titles"] = facets

        data_dict = {
            u'q': q,
            u'fq': fq,
            u'include_private': True,
            u'facet.field': facets.keys(),
            u'rows': limit,
            u'sort': sort_by,
            u'start': (page - 1) * limit,
            u'extras': search_extras
        }

        context_ = dict((k, v) for (k, v) in context.items() if k != u'schema')
        query = get_action(u'package_search')(context_, data_dict)

        extra_vars["page"] = h.Page(
            collection=query['results'],
            page=page,
            url=pager_url,
            item_count=query['count'],
            items_per_page=limit)

        # TODO: Remove
        # ckan 2.9: Adding variables that were removed from c object for
        # compatibility with templates in existing extensions
        g.group_dict['package_count'] = query['count']

        extra_vars["search_facets"] = g.search_facets = query['search_facets']
        extra_vars["search_facets_limits"] = g.search_facets_limits = {}
        for facet in g.search_facets.keys():
            limit = int(
                request.params.get(u'_%s_limit' % facet,
                                   config.get(u'search.facets.default', 10)))
            g.search_facets_limits[facet] = limit
        extra_vars["page"].items = query['results']

        extra_vars["sort_by_selected"] = sort_by

    except search.SearchError as se:
        log.error(u'Group search error: %r', se.args)
        extra_vars["query_error"] = True
        extra_vars["page"] = h.Page(collection=[])

    # TODO: Remove
    # ckan 2.9: Adding variables that were removed from c object for
    # compatibility with templates in existing extensions
    g.facet_titles = facets
    g.page = extra_vars["page"]

    extra_vars["group_type"] = group_type
    _setup_template_variables(context, {u'id': id}, group_type=group_type)
    return extra_vars


def read(group_type, is_organization, id=None, limit=20):
    extra_vars = {}
    set_org(is_organization)
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'schema': _db_to_form_schema(group_type=group_type),
        u'for_view': True
    }
    data_dict = {u'id': id, u'type': group_type}

    # unicode format (decoded from utf8)
    q = request.params.get(u'q', u'')

    extra_vars["q"] = q

    try:
        # Do not query for the group datasets when dictizing, as they will
        # be ignored and get requested on the controller anyway
        data_dict['include_datasets'] = False

        # Do not query group members as they aren't used in the view
        data_dict['include_users'] = False

        group_dict = _action(u'service_show')(context, data_dict)
        group = context['service']
    except (NotFound, NotAuthorized):
        base.abort(404, _(u'Service not found'))
    g.q = q
    g.group_dict = group_dict
    g.group = group

    extra_vars = _read(id, limit, group_type)

    extra_vars["group_dict"] = group_dict
    session = context['session']
    service_ins = session.query(App).filter(App.app_id == id)[0]
    extra_vars['ins'] = service_ins
    extra_vars['appserver_host'] = appserver_host
    log.debug(appserver_host)
    return base.render('service/read.html', extra_vars)


class CreateServiceView(MethodView):
    u'''Create service view '''

    def _prepare(self, data=None):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'save': u'save' in request.params,
            u'parent': request.params.get(u'parent', None),
        }

        try:
            _check_access(u'service_create', context)
        except NotAuthorized:
            base.abort(403, _(u'Unauthorized to create a group'))

        return context

    def post(self, group_type, is_organization):
        set_org(is_organization)
        context = self._prepare()
        try:
            data_dict = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
            data_dict.update(clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
            ))
            data_dict['type'] = 'Server'
            data_dict['slug_name'] = slug.slug(data_dict['app_name'])
            # data_dict['port2port']= '%s:%d'%(data_dict['port'],random.randint(10000, 60000))
            # data_dict['port2port']= '%s:%d'%(data_dict['port'],random.randint(10000, 60000))
            data_dict['owner'] = context['user']
            data_dict['status'] = 'Pending'
            data_dict['language'] = 'DockerImage'
            service = _action(u'service_create')(context, data_dict)
        except (NotFound, NotAuthorized) as e:
            base.abort(404, _(u'Service not found'))
        except dict_fns.DataError:
            base.abort(400, _(u'Integrity Error'))
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(group_type, is_organization,
                            data_dict, errors, error_summary)

        return h.redirect_to(u'service.index')
        # return h.redirect_to(u'service.index',status=service['status']['phase'] if isinstance(service['status'],dict) else service['status'])

    def get(self, group_type, is_organization,
            data=None, errors=None, error_summary=None):
        extra_vars = {}
        set_org(is_organization)
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
            u'action': u'new',
            u'group_type': group_type
        }
        _setup_template_variables(
            context, data, group_type=group_type)
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
            u'user': g.user,
            u'save': u'save' in request.params,
            u'parent': request.params.get(u'parent', None),
        }

        try:
            _check_access(u'service_create', context)
        except NotAuthorized:
            base.abort(403, _(u'Unauthorized to create a group'))

        return context

    def post(self, group_type, is_organization):
        set_org(is_organization)
        context = self._prepare()
        try:
            data_dict = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
            data_dict.update(clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.files)))
            ))
            print "aasaas"
            # print request.files
            """
                chuyen qua cho Cuong
            """
            data_dict['type'] = 'Batch'
            data_dict['slug_name'] = slug.slug(data_dict['app_name'])
            data_dict['image'] = data_dict['slug_name']
            data_dict['owner'] = context['user']
            data_dict['json_input'] = 'json_input' in data_dict
            data_dict['binary_input'] = 'binary_input' in data_dict
            data_dict['json_input'] = True if not (data_dict['json_input'] or data_dict['binary_input']) else data_dict[
                'binary_input']
            _action(u'service_create')(context, data_dict)

        except (NotFound, NotAuthorized, ValidationError, dict_fns.DataError) as e:
            base.abort(404, _(u'Not found'))

        return h.redirect_to(u'service.index')

    def get(self, group_type, is_organization,
            data=None, errors=None, error_summary=None):
        extra_vars = {}
        set_org(is_organization)
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
            u'action': u'new',
            u'group_type': group_type
        }
        _setup_template_variables(
            context, data, group_type=group_type)
        extra_vars["is_code"] = True;
        form = base.render(
            'service/new_service_form.html', extra_vars)

        # TODO: Remove
        # ckan 2.9: Adding variables that were removed from c object for
        # compatibility with templates in existing extensions
        g.form = form

        extra_vars["form"] = form
        return base.render('service/new.html', extra_vars)


# def getResult(id):
#     ins=AppResult.query().filter(id=id)
#     return ins.stdout
service = Blueprint(u'service', __name__, url_prefix=u'/service',
                    url_defaults={u'group_type': u'service',
                                  u'is_organization': False})


def register_group_plugin_rules(blueprint):
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


register_group_plugin_rules(service)

@service.route('/<string:id>/delete', methods=['GET','POST'])
def delete(id, group_type, is_organization):
    print id
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
    }
    deleteAppARelevant(context[u'session'],id)
    return h.redirect_to(u'service.index')
@service.route('/huhu/huhu', methods=['GET','POST'])
def abc(group_type, is_organization):
    print "asd"
    return  base.render('page.html')
