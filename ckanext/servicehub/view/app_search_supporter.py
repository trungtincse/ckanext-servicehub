# encoding: utf-8
from pprint import pprint

import six

from ckanext.servicehub.cuong import cprint, ccprint
from collections import defaultdict

import logging

from ckanext.servicehub.action import app_solr_action

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic as logic
from ckan.common import OrderedDict, c, request, _
from flask import Blueprint
from ckanext.servicehub.model.ServiceModel import *

storage_path = config.get('ckan.storage_path')
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

# log = logging.getLogger(__name__)
logger = logging.getLogger('logserver')

# blueprint = Blueprint('appsearch', __name__, url_prefix='/app/search')


# def register_rules():
#     blueprint.add_url_rule('', view_func=index, strict_slashes=True)


def index():
    search_result = app_solr_action.query_app(
        text=query() or '*:*',
        organizations=request.params.getlist('organization'),
        categories=request.params.getlist('categories'),
        language=request.params.get('language'),
        sort=request.params.get('sort', 'score asc, created_at desc')
    )

    page = h.Page(
        collection=app_solr_action.docs(search_result),
        page=h.get_page_number(request.params),
        item_count=len(app_solr_action.docs(search_result))
    )

    # cprint(json.dumps(search_result['response'], indent=4))

    # cprint('app solr')
    # ccprint(app_solr_action.ckan_search_facets(search_result))
    # ccprint(selected_filtered_fields_grouped())
    # ccprint(app_solr_action.ckan_search_facets(search_result))
    c.search_facets = app_solr_action.ckan_search_facets(search_result)
    c.search_facets_limits = False
    c.remove_url_param = cuong_remove_url_param # override
    return base.render('service/search.html', {
        'query': request.params.get('q', ''),
        'sort_by_selected': request.params.get('sort', 'score desc, metadata_modified desc'),
        'facet_titles': facet_titles(),
        'selected_filtered_fields': selected_filtered_fields(),
        'selected_filtered_fields_grouped': selected_filtered_fields_grouped(),
        'page': page,
        'search_facets': app_solr_action.ckan_search_facets(search_result),
        'remove_field': remove_field
    })


def query():
    q=request.params.get('q')
    if q:
        return "text:"+q
    else:
        return None


def cuong_remove_url_param(key, value=None, replace=None, controller=None,
                     action=None, extras=None, alternative_url=None):
    ''' Remove one or multiple keys from the current parameters.
    The first parameter can be either a string with the name of the key to
    remove or a list of keys to remove.
    A specific key/value pair can be removed by passing a second value
    argument otherwise all pairs matching the key will be removed. If replace
    is given then a new param key=replace will be added.
    Note that the value and replace parameters only apply to the first key
    provided (or the only one provided if key is a string).

    controller action & extras (dict) are used to create the base url
    via :py:func:`~ckan.lib.helpers.url_for`
    controller & action default to the current ones

    This can be overriden providing an alternative_url, which will be used
    instead.

    '''
    if isinstance(key, six.string_types):
        keys = [key]
    else:
        keys = key

    # params_nopage = [(k, v) for k, v in request.params.items() if k != 'page']
    # params = list(params_nopage)
    params = []
    # https://tedboy.github.io/flask/generated/generated/werkzeug.ImmutableMultiDict.html
    for param in request.params.iterkeys():
        if param == 'page':
            continue
        vals = request.params.getlist(param)
        params.extend((param, v) for v in vals)

    if value:
        params.remove((keys[0], value))
    else:
        for key in keys:
            [params.remove((k, v)) for (k, v) in params[:] if k == key]
    if replace is not None:
        params.append((keys[0], replace))

    if alternative_url:
        return h._url_with_params(alternative_url, params)

    return h._create_url_with_params(params=params, controller=controller,
                                   action=action, extras=extras)


def has_more_facets(facet, limit=None, exclude_active=False):
    '''
    Returns True if there are more facet items for the given facet than the
    limit.

    Reads the complete list of facet items for the given facet from
    c.search_facets, and filters out the facet items that the user has already
    selected.

    Arguments:
    facet -- the name of the facet to filter.
    limit -- the max. number of facet items.
    exclude_active -- only return unselected facets.

    '''
    cprint('params:', request.params.items())
    cprint('getlist: organization:', request.params.getlist('organization'))
    facets = []
    for facet_item in c.search_facets.get(facet)['items']:
        # cprint('facet: %s, ["name"]: %s' % (facet, facet_item['name']), end=', ')
        if not len(facet_item['name'].strip()):
            continue
        if not (facet, facet_item['name']) in request.params.items():
            # cprint('active=false')
            facets.append(dict(active=False, **facet_item))
        elif not exclude_active:
            # cprint('active=true')
            facets.append(dict(active=True, **facet_item))
    if c.search_facets_limits and limit is None:
        limit = c.search_facets_limits.get(facet)
    if limit is not None and len(facets) > limit:
        return True
    return False




def has_more_facets(facet, limit=None, exclude_active=False):
    '''
    Returns True if there are more facet items for the given facet than the
    limit.

    Reads the complete list of facet items for the given facet from
    c.search_facets, and filters out the facet items that the user has already
    selected.

    Arguments:
    facet -- the name of the facet to filter.
    limit -- the max. number of facet items.
    exclude_active -- only return unselected facets.

    '''
    cprint('params:', request.params.items())
    cprint('getlist: organization:', request.params.getlist('organization'))
    facets = []
    for facet_item in c.search_facets.get(facet)['items']:
        # cprint('facet: %s, ["name"]: %s' % (facet, facet_item['name']), end=', ')
        if not len(facet_item['name'].strip()):
            continue
        if not (facet, facet_item['name']) in request.params.items():
            # cprint('active=false')
            facets.append(dict(active=False, **facet_item))
        elif not exclude_active:
            # cprint('active=true')
            facets.append(dict(active=True, **facet_item))
    if c.search_facets_limits and limit is None:
        limit = c.search_facets_limits.get(facet)
    if limit is not None and len(facets) > limit:
        return True
    return False


def selected_filtered_fields():
    """
    selected filtered fields. example: user selected organizations 'viettel' and 'vinamilk'
    then selected filtered fields = [('organizations', 'viettel'), ('organizations', 'vinamilk')]
    """
    result = []
    for (param, value) in search_filter_fields():
        result.append((param, value))
    # cprint('selected_filtered_fields:', result)
    return result


def selected_filtered_fields_grouped():
    # like selected fields, by group by field name
    result = defaultdict(list)
    for (param, value) in search_filter_fields():
        result[param].append(value)
    # cprint('selected_filtered_fields_grouped:', result)
    return result


def search_filter_fields():
    for (param, value) in request.params.items():
        if param not in ['q', 'page', 'sort'] and value != '' and not param.startswith('_'):
            yield param, value


def facet_titles():
    default_facet_titles = {
        'organization': _('Organizations'),
        'category': _('Categories'),
        'language': _('Language')
    }

    return default_facet_titles


def remove_field(key, value=None, replace=None):
    return h.remove_url_param(key, value=value, replace=replace, controller='appsearch', action='index')


# register_rules()