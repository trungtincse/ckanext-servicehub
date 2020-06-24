import json
import logging
from pprint import pprint

import requests

from ckan import authz
from ckan.common import request, config, g
from ckan.lib.search.common import SearchIndexError, SearchError

log = logging.getLogger('ckan.logic')

solr_url = config.get('ckan.servicehub.prj_solr_url')
# solr_url = 'http://localhost:8984/solr/ckanproject'

def index_project(project):
    url = solr_url + '/update/json/docs?commit=true'
    try:
        r = requests.post(url, json=project).json()
    except Exception as e:
        print('Failed to do request to Solr server')
        raise SearchIndexError(e)

    if r['responseHeader']['status'] != 0:
        raise SearchIndexError(r['error'])


def query_project(text, organization_name, categories, tags, sort):
    filters = []

    if organization_name:
        filters.append('organization_name:"%s"' % organization_name)

    if categories:
        for cate in categories:
            filters.append('category:"%s"' % cate)  # AND

    if tags:
        for tag in tags:
            filters.append('tags:"%s"' % tag)

    if authz.is_sysadmin(g.user):
        pass
        # pprint('is admin: show all projects')
    else:
        filters.append('active:"true"')
        # pprint('Not admin: just show active projects')

    query = {
        'query': text,
        'filter': filters,
        'facet': query_facets,
        'sort': sort
    }

    r = requests.get(solr_url + '/query', json=query).json()
    if r.get('error'):
        raise SearchError(r['error']['msg'])

    return r


def activate_project(project_id):
    r = requests.post(solr_url + '/update?commit=true', json=[
        {
            'id': project_id,
            'active': {'set': True}
        }
    ]).json()
    if 'error' in r:
        raise SearchError(r['error']['msg'])
def deactivate_project(project_id):
    r = requests.post(solr_url + '/update?commit=true', json=[
        {
            'id': project_id,
            'active': {'set': False}
        }
    ]).json()
    if 'error' in r:
        raise SearchError(r['error']['msg'])

def delete_project(project_id):
    r = requests.post(solr_url + '/update?commit=true', json={
        'delete': {
            'id': project_id
        }
    }).json()

    if 'error' in r:
        raise SearchError(r['error']['msg'])


facet_fields = ['organization_name', 'category', 'tags']


query_facets = {field: {
    'type': 'terms',
    'field': field,
    'limit': 5,
    'mincount': 1} for field in facet_fields}


def ckan_search_facets(solr_response):
    """create key 'search_facets' of solr response like in action package_search"""
    facets = solr_response['facets']
    if facets['count'] == 0:
        # solr will not return any keys => fake empty response
        return empty_search_facets
    else:
        result = {}
        for field in facet_fields:
            items = []
            for bucket in facets[field]['buckets']:
                item = {
                    'name': bucket['val'],
                    'display_name': bucket['val'],
                    'count': bucket['count'],
                    'active': bucket['val'] in request.params.getlist(field)
                }
                items.append(item)

            result[field] = {
                'title': field,
                'items': items
            }
        return result


empty_search_facets = {field: {'title': field, 'items': []} for field in facet_fields}
