import json
import os
import logging

import pysolr
import requests
from sqlalchemy import inspect
from ckan.common import OrderedDict, c, g, config, request, _
import ckan.logic as logic
from ckan.lib.search.common import SearchIndexError
from ckanext.servicehub.cuong import cprint

log = logging.getLogger('ckan.logic')

solr_url = config.get('ckan.servicehub.app_solr_url')


def index_app(context, data_dict):
    app = data_dict
    """
    :param app: dict
    :return:
    """
    app['data_dict'] = json.dumps(app, ensure_ascii=False)
    url = solr_url + '/update/json/docs?commit=true'
    try:
        r = requests.post(url, json=app).json()
        if r['responseHeader']['status'] != 0:
            print('Index error: ' + json.dumps(r['error']))
    except Exception as e:
        print('Failed to do request to Solr server')
        raise SearchIndexError(e)


def app_index_delete(context, data_dict):
    r = requests.post(solr_url + '/update?commit=true', json={
        'delete': {
            'id': data_dict['app_id']
        }
    })
    # print(r.json())


# @logic.side_effect_free
# def app_search(context, data_dict):
#
#     return query_app(
#         text=data_dict.get('text'),
#         categories=data_dict.get('categories'),
#         language=data_dict.get('language'),
#         organizations=data_dict.get('organizations'),
#         # related_datasets=data_dict.get('related_datasets'),
#     )


def query_app(text, categories, language, organizations, related_datasets=None):
    """
    :param text: str: text in the search box
    :param categories: list[str]: AND
    :param language: str
    :param organizations: list[str]: OR
    :param related_datasets: list[str]: AND
    :return:
    """
    text = text or "*:*"  # avoid None

    filters = []

    if categories:
        for cate in categories:
            filters.append('categories:"%s"' % cate)  # AND

    if language:
        filters.append('language:"%s"' % language)

    if organizations:
        v = ' OR '.join('"%s"' % org for org in organizations)
        filters.append('organization:(%s)' % v)

    if related_datasets:
        for dataset in related_datasets:
            filters.append('related_datasets:"%s"' % dataset)

    query = {
        'query': text,
        'filter': filters,
        'facet': query_facets()
    }

    r = requests.get(solr_url + '/query', json=query).json()
    # cprint(json.dumps(r, indent=4))
    return r


facet_fields = ['organization', 'language', 'categories']


def query_facets():
    facets = {}
    for field in facet_fields:
        facets[field] = {
            'type': 'terms',
            'field': field,
            'limit': 5
        }
    return facets


def ckan_search_facets(solr_response):
    """create key 'search_facets' of solr response like in action package_search"""
    result = {}
    facets = solr_response['facets']
    for field in facet_fields:
        items = []
        for bucket in facets[field]['buckets']:
            item = {
                'name': bucket['val'],
                'display_name': bucket['val'].title() if field == 'language' else bucket['val'],
                'count': bucket['count']
            }
            items.append(item)

        result[field] = items
    return result


public_functions = {
    # 'app_index': app_index,
    'app_index_delete': app_index_delete,
    # 'app_search': app_search,
}
