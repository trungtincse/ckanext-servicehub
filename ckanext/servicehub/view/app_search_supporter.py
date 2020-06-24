# encoding: utf-8
from pprint import pprint

import six

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic as logic
from ckan.common import c, g, request, _
from ckan.lib.search import SearchError
from ckanext.servicehub.action import app_solr
from ckanext.servicehub.model.ServiceModel import *
from ckanext.servicehub.view import solr_common

storage_path = config.get('ckan.storage_path')
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

# logger = logging.getLogger('ckan.appserver')


def index():
    try:
        search_result = app_solr.query_app(
            text=solr_common.query(),
            organization=request.params.get('organization'),
            categories=request.params.getlist('category'),
            language=request.params.get('language'),
            sort=request.params.get('sort', 'score asc, created_at desc')
        )

    except SearchError as e:
        c.query_error = True
        return base.render('service/search.html', {
            'query': request.params.get('q', ''),
            'sorting': _sorting,
            'sort_by_selected': request.params.get('sort', 'score desc, created_at desc'),
            'facet_titles': _facet_titles,
            'selected_filtered_fields': solr_common.selected_filtered_fields(),
            'selected_filtered_fields_grouped': solr_common.selected_filtered_fields_grouped(),
            'page': h.Page(collection=[]),
            'search_facets': app_solr.empty_search_facets(),
            'remove_field': remove_field
        })

    page = h.Page(
        collection=app_solr.docs(search_result),
        page=h.get_page_number(request.params),
        item_count=len(app_solr.docs(search_result))
    )

    c.search_facets = app_solr.ckan_search_facets(search_result)
    c.search_facets_limits = False
    c.remove_url_param = solr_common.cuong_remove_url_param # override
    return base.render('service/search.html', {
        'query': request.params.get('q', ''),
        'sorting': _sorting,
        'sort_by_selected': request.params.get('sort', 'score desc, created_at desc'),
        'facet_titles': _facet_titles,
        'selected_filtered_fields': solr_common.selected_filtered_fields(),
        'selected_filtered_fields_grouped': solr_common.selected_filtered_fields_grouped(),
        'page': page,
        'search_facets': app_solr.ckan_search_facets(search_result),
        'remove_field': remove_field
    })


_sorting = [
  ('Relevance', 'score desc, created_at desc'),
  ('App Name Ascending', 'app_name asc'),
  ('App Name Descending', 'app_name desc')
]


_facet_titles = {
    'organization': 'Organizations',
    'category': 'Categories',
    'language': 'Language'
}


def remove_field(key, value=None, replace=None):
    return h.remove_url_param(key, value=value, replace=replace, controller='service', action='index')


# register_rules()