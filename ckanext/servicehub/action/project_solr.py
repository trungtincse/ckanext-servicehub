import logging

import requests

from ckan.common import request
from ckan.lib.search.common import SearchIndexError


log = logging.getLogger('ckan.logic')

# solr_url = config.get('ckan.servicehub.app_solr_url')
solr_url = 'http://localhost:8984/solr/ckanproject'


def index_project(project):
    url = solr_url + '/update/json/docs?commit=true'
    try:
        r = requests.post(url, json=project).json()
    except Exception as e:
        print('Failed to do request to Solr server')
        raise SearchIndexError(e)

    if r['responseHeader']['status'] != 0:
        raise SearchIndexError(r['error'])



facet_fields = ['organization', 'language', 'category']


def query_facets():
    facets = {}
    for field in facet_fields:
        facets[field] = {
            'type': 'terms',
            'field': field,
            'limit': 5,
            'mincount': 1
        }
    return facets


def docs(search_result):
    return search_result['response']['docs']


def ckan_search_facets(solr_response):
    """create key 'search_facets' of solr response like in action package_search"""
    facets = solr_response['facets']
    if facets['count'] == 0:
        # solr will not return any keys => fake empty response
        result = {}
        for field in facet_fields:
            result[field] = {
                'title': field,
                'items': []
            }
        return result
    else:
        result = {}
        for field in facet_fields:
            items = []
            for bucket in facets[field]['buckets']:
                item = {
                    'name': bucket['val'],
                    'display_name': bucket['val'].title() if field == 'language' else bucket['val'],
                    'count': bucket['count'],
                    'active': bucket['val'] in request.params.getlist(field)
                }
                items.append(item)

            result[field] = {
                'title': field,
                'items': items
            }
        return result