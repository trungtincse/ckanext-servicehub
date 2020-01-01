import uuid
import logging
import json
import datetime
import socket

from ckanext.servicehub.model.ServiceModel import App

import ckan.lib.base as base
from ckan.lib import helpers as h
from ckanext.servicehub.dictization.dictize import service_dictize
from ckan.common import config
import sqlalchemy
from paste.deploy.converters import asbool
from six import string_types, text_type
from ckan.common import OrderedDict, c, g, config, request, _
import ckan.lib.dictization
import ckan.logic as logic
import ckan.logic.action
import ckan.logic.schema
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.jobs as jobs
import ckan.lib.navl.dictization_functions
import ckan.model as model
import ckan.model.misc as misc
import ckan.plugins as plugins
import ckan.lib.search as search
import ckan.lib.plugins as lib_plugins
import ckan.lib.datapreview as datapreview
import ckan.authz as authz

from ckan.common import _

log = logging.getLogger('ckan.logic')

# Define some shortcuts
# Ensure they are module-private so that they don't get loaded as available
# actions in the action API.
_validate = ckan.lib.navl.dictization_functions.validate
_table_dictize = ckan.lib.dictization.table_dictize
_check_access = logic.check_access
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
_get_or_bust = logic.get_or_bust

_select = sqlalchemy.sql.select
_aliased = sqlalchemy.orm.aliased
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_desc = sqlalchemy.desc
_case = sqlalchemy.case
_text = sqlalchemy.text
def service_list(context, data_dict):
    session=context['session']
    model = context['model']
    api = context.get('api_version')
    services = data_dict.get('services')
    group_type = data_dict.get('type', 'group')
    ref_group_by = 'id' if api == 2 else 'app_name'
    pagination_dict = {}
    limit = data_dict.get('limit')
    if limit:
        pagination_dict['limit'] = data_dict['limit']
    offset = data_dict.get('offset')
    if offset:
        pagination_dict['offset'] = data_dict['offset']
    if pagination_dict:
        pagination_dict, errors = _validate(
            data_dict, logic.schema.default_pagination_schema(), context)
        if errors:
            raise ValidationError(errors)
    sort = data_dict.get('sort') or 'title'
    q = data_dict.get('q')

    all_fields = asbool(data_dict.get('all_fields', None))

    if all_fields:
        # all_fields is really computationally expensive, so need a tight limit
        max_limit = config.get(
            'ckan.group_and_organization_list_all_fields_max', 25)
    else:
        max_limit = config.get('ckan.group_and_organization_list_max', 1000)
    if limit is None or limit > max_limit:
        limit = max_limit

    # order_by deprecated in ckan 1.8
    # if it is supplied and sort isn't use order_by and raise a warning
    order_by = data_dict.get('order_by', '')
    if order_by:
        log.warn('`order_by` deprecated please use `sort`')
        if not data_dict.get('sort'):
            sort = order_by

    # if the sort is packages and no sort direction is supplied we want to do a
    # reverse sort to maintain compatibility.
    if sort.strip() in ('packages', 'package_count'):
        sort = 'package_count desc'

    sort_info = _unpick_search(sort,
                               allowed_fields=['name', 'packages',
                                               'package_count', 'title'],
                               total=1)

    if sort_info and sort_info[0][0] == 'package_count':
        query = session.query(App.app_id,
                                    App.app_name,
                                    sqlalchemy.func.count(App.app_id))

    else:
        query = session.query(App.app_id,
                                    App.app_name)

    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)

    services = query.all()

    if all_fields:
        action = 'service_show'
        service_list = []
        for service in services:
            data_dict['id'] = service.app_id
            for key in ('include_extras', 'include_tags', 'include_users',
                        'include_services', 'include_followers'):
                if key not in data_dict:
                    data_dict[key] = False

            service_list.append(logic.get_action(action)(context, data_dict))
    else:
        service_list = [getattr(group, ref_group_by) for group in services]
    print service_list
    return service_list
def _unpick_search(sort, allowed_fields=None, total=None):
    ''' This is a helper function that takes a sort string
    eg 'name asc, last_modified desc' and returns a list of
    split field order eg [('name', 'asc'), ('last_modified', 'desc')]
    allowed_fields can limit which field names are ok.
    total controls how many sorts can be specifed '''
    sorts = []
    split_sort = sort.split(',')
    for part in split_sort:
        split_part = part.strip().split()
        field = split_part[0]
        if len(split_part) > 1:
            order = split_part[1].lower()
        else:
            order = 'asc'
        if allowed_fields:
            if field not in allowed_fields:
                raise ValidationError('Cannot sort by field `%s`' % field)
        if order not in ['asc', 'desc']:
            raise ValidationError('Invalid sort direction `%s`' % order)
        sorts.append((field, order))
    if total and len(sorts) > total:
        raise ValidationError(
            'Too many sort criteria provided only %s allowed' % total)
    return sorts
def service_show(context, data_dict):
    model = context['model']
    id = _get_or_bust(data_dict, 'id')

    service = App.get(id)
    context['service'] = service

    if asbool(data_dict.get('include_datasets', False)):
        packages_field = 'datasets'
    elif asbool(data_dict.get('include_dataset_count', True)):
        packages_field = 'dataset_count'
    else:
        packages_field = None

    try:
        include_tags = asbool(data_dict.get('include_tags', True))
        if asbool(config.get('ckan.auth.public_user_details', True)):
            include_users = asbool(data_dict.get('include_users', True))
        else:
            include_users = asbool(data_dict.get('include_users', False))
        include_groups = asbool(data_dict.get('include_groups', True))
        include_extras = asbool(data_dict.get('include_extras', True))
        include_followers = asbool(data_dict.get('include_followers', True))
    except ValueError:
        raise logic.ValidationError(_('Parameter is not an bool'))

    if service is None:
        raise NotFound
    # TODO
    # _check_access('service_show', context, data_dict)
    group_dict = service_dictize(service, context,
                                             packages_field=packages_field,
                                             include_tags=include_tags,
                                             include_extras=include_extras,
                                             include_groups=include_groups,
                                             include_users=include_users,)

    plugin_type = plugins.IGroupController

    for item in plugins.PluginImplementations(plugin_type):
        item.read(service)

    # group_plugin = lib_plugins.lookup_group_plugin(group_dict['type'])
    # try:
    #     schema = group_plugin.db_to_form_schema_options({
    #         'type': 'show',
    #         'api': 'api_version' in context,
    #         'context': context})
    # except AttributeError:
    #     schema = group_plugin.db_to_form_schema()

    # if include_followers:
    #     group_dict['num_followers'] = logic.get_action('group_follower_count')(
    #         {'model': model, 'session': model.Session},
    #         {'id': group_dict['id']})
    # else:
    #     group_dict['num_followers'] = 0

    # if schema is None:
    #     schema = logic.schema.default_show_group_schema()
    # group_dict, errors = lib_plugins.plugin_validate(
    #     group_plugin, context, group_dict, schema,
    #     'service_show')
    return group_dict
