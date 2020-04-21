import ast

import requests
from werkzeug.datastructures import FileStorage

from ckan.controllers.package import PackageController
from ckan.lib import helpers
from flask import Blueprint, Response, jsonify
import json
from ckanext.servicehub.model.ServiceModel import Call
import ckan.lib.base as base
from ckan import model, logic
from ckan.common import g, c, request, config, _
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


class ResourceNotFoundException(Exception):
    pass


def modify_input(context, data_dict):
    data_dict['ckan_resources'] = data_dict.get('ckan_resources', [])
    ckan_resources = data_dict['ckan_resources'] if isinstance(data_dict['ckan_resources'], list) else [
        data_dict['ckan_resources']]

    data_dict['lst'] = data_dict.get('lst', [])
    lst = data_dict['lst'] if isinstance(data_dict['lst'], list) else [data_dict['lst']]

    data_dict['check_box_inputs'] = data_dict.get('check_box_inputs', [])
    check_box_inputs = data_dict['check_box_inputs'] if isinstance(data_dict['check_box_inputs'], list) else [
        data_dict['check_box_inputs']]

    for resource in ckan_resources:
        resource_id = data_dict['%s_resource_id' % resource]
        del data_dict['%s_resource_id' % resource]
        resource_response = get_action(u'resource_show')(context, dict(id=resource_id))
        if not resource_response['success']:
            raise ResourceNotFoundException()
        url = resource_response['result']['url']
        data_dict[resource] = url
    for i in lst:
        data_dict[i] = data_dict[i] if isinstance(data_dict[i], list) else [data_dict[i]]
    for i in check_box_inputs:
        data_dict[i] = 'true' if data_dict[i] == 'on' else 'false'

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
    try:
        modify_input(context, data_dict)
    except ResourceNotFoundException:
        return jsonify(dict(error="Resource not found!"))
    data_dict["app_id"] = app_id
    result_ins = get_action(u'call_create')(context, data_dict)
    # get_action(u'push_request_call')(context, dict(call_id=result_ins['id']))
    return jsonify(result_ins)


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
    if instance.get('error', '') != '':
        return base.abort(404, _(u'Call not found'))
    service = get_action(u'service_show')(context, dict(id=instance['call_detail']['app_id']))
    # --------------COPY-------------
    resource_url = "covid.xls"
    try:
        c.package = model.Package.get("1d0f9207-ea64-4e00-9045-edd1fae61503").as_dict()
    except (NotFound, NotAuthorized):
        base.abort(404, _('Dataset not found'))
    print c.package.get('resources', [])
    for resource in c.package.get('resources', []):
        if resource['url'] == resource_url:
            c.resource = resource
            break
    if not c.resource:
        base.abort(404, _('Resource not found'))

    # required for nav menu
    c.pkg_dict = c.package
    dataset_type = 'ouput'

    # Deprecated: c.datastore_api - use h.action_url instead
    c.datastore_api = '%s/api/action' % \
                      config.get('ckan.site_url', '').rstrip('/')
    controller = EnhancePackageController()
    # print controller.resource_views('asdasd', resource_id)
    c.resource['can_be_previewed'] = controller._resource_preview(
        {'resource': c.resource, 'package': c.package})

    resource_views = get_action('resource_view_list')(
        context, {'id': c.resource['id']})
    c.resource['has_views'] = len(resource_views) > 0

    current_resource_view = None
    view_id = request.params.get('view_id')
    if c.resource['can_be_previewed'] and not view_id:
        current_resource_view = None
    elif c.resource['has_views']:
        if view_id:
            current_resource_view = [rv for rv in resource_views
                                     if rv['id'] == view_id]
            if len(current_resource_view) == 1:
                current_resource_view = current_resource_view[0]
            else:
                base.abort(404, _('Resource view not found'))
        else:
            current_resource_view = resource_views[0]
    vars = {'pkg': c.package,
            'resource_views': resource_views,
            'current_resource_view': current_resource_view,
            'dataset_type': dataset_type,
            'ins': instance['call_detail'],
            'service_ins': service['app_detail'],
            'res': c.resource['has_views']
            }
    return base.render('call/read.html', vars)


class EnhancePackageController(PackageController):
    def resource_view(self, id, resource_id, view_id=None):
        '''
        Embedded page for a resource view.

        Depending on the type, different views are loaded. This could be an
        img tag where the image is loaded directly or an iframe that embeds a
        webpage or a recline preview.
        '''
        context = {'model': model,
                   'session': model.Session,
                   'user': c.user,
                   'auth_user_obj': c.userobj}

        try:
            package = get_action('package_show')(context, {'id': id})
        except (NotFound, NotAuthorized):
            base.abort(404, _('Dataset not found'))

        try:
            resource = get_action('resource_show')(
                context, {'id': resource_id})
        except (NotFound, NotAuthorized):
            base.abort(404, _('Resource not found'))

        view = None
        if request.params.get('resource_view', ''):
            try:
                view = json.loads(request.params.get('resource_view', ''))
            except ValueError:
                base.abort(409, _('Bad resource view data'))
        elif view_id:
            try:
                view = get_action('resource_view_show')(
                    context, {'id': view_id})
            except (NotFound, NotAuthorized):
                base.abort(404, _('Resource view not found'))

        if not view or not isinstance(view, dict):
            base.abort(404, _('Resource view not supplied'))

        return helpers.rendered_resource_view(view, resource, package, embed=True)

    def resource_views(self, id, resource_id):
        package_type = self._get_package_type(id.split('@')[0])
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'for_view': True,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': id}

        try:
            check_access('package_update', context, data_dict)
        except NotAuthorized:
            base.abort(403, _('User %r not authorized to edit %s') % (c.user, id))
        # check if package exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
            c.pkg = context['package']
        except (NotFound, NotAuthorized):
            base.abort(404, _('Dataset not found'))

        try:
            c.resource = get_action('resource_show')(context,
                                                     {'id': resource_id})
            c.views = get_action('resource_view_list')(context,
                                                       {'id': resource_id})

        except NotFound:
            base.abort(404, _('Resource not found'))
        except NotAuthorized:
            base.abort(403, _('Unauthorized to read resource %s') % id)

        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)

        return base.render('call/resource_views.html')
