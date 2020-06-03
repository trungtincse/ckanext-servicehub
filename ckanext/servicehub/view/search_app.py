# encoding: utf-8

from ckanext.servicehub.cuong import cprint
from collections import defaultdict

import logging

from ckanext.servicehub.action import app_solr

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

blueprint = Blueprint('appsearch', __name__, url_prefix='/app/search')


def register_rules():
    blueprint.add_url_rule('/', view_func=index, strict_slashes=False)


def index():
    search_result = app_solr.query_app(
        text=query() or '*:*',
        organizations=request.params.getlist('organization'),
        categories=request.params.getlist('categories'),
        language=request.params.get('language')
    )

    page = h.Page(
        collection=app_solr.docs(search_result),
        page=h.get_page_number(request.params),
        item_count=len(app_solr.docs(search_result))
    )

    # cprint(json.dumps(search_result['response'], indent=4))

    # cprint(app_solr.ckan_search_facets(search_result))
    return base.render('service/search.html', {
        'query': query() or '',
        'sort_by_selected': request.params.get('sort', 'score desc, metadata_modified desc'),
        'selected_filtered_fields': selected_filtered_fields(),
        'selected_filtered_fields_grouped': selected_filtered_fields_grouped(),
        'page': page,
        'facet_titles': facet_titles(),
        'search_facets': app_solr.ckan_search_facets(search_result),
        'remove_field': remove_field
    })


def query():
    request.params.get('q')


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
        'categories': _('Categories'),
        'language': _('Language')
    }

    return default_facet_titles


def remove_field(key, value=None, replace=None):
    return h.remove_url_param(key, value=value, replace=replace, controller='appsearch', action='index')


def facets():
    result = OrderedDict()



    for facet in h.facets():
        if facet in default_facet_titles:
            result[facet] = default_facet_titles[facet]
        else:
            result[facet] = facet

    # Facet titles
    for plugin in p.PluginImplementations(p.IFacets):
        result = plugin.dataset_facets(result, package_type)

    c.facet_titles = result



register_rules()