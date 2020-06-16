import json
import os
import logging
from pprint import pprint

import pysolr
import pytz
import requests
from sqlalchemy import inspect
from ckan.common import OrderedDict, c, g, config, request, _
import ckan.logic as logic
from ckan.lib.search.common import SearchIndexError
from ckanext.servicehub.model.ServiceModel import App, AppCategory, AppRelatedDataset

log = logging.getLogger('ckan.logic')

solr_url = config.get('ckan.servicehub.app_solr_url')


def index_app(context, app, categories, datasets):
    """
    :param app: App model
    :return:
    """
    categories_json = list(map(AppCategory.as_dict, categories))
    datasets_json = list(map(AppRelatedDataset.as_dict_raw, datasets))

    app_json = app.as_dict_raw()
    app_json['category'] = categories_json
    app_json['dataset_related'] = datasets_json

    app_json['data_dict'] = json.dumps(app_json, ensure_ascii=False) # serialize first

    # change now
    app_json['category'] = [cate['tag_name'] for cate in categories_json]
    app_json['dataset_related'] = [dataset['package_id'] for dataset in datasets_json]
    try:
        url = solr_url + '/update/json/docs?commit=true'
        r = requests.post(url, json=app_json).json()
        if r['responseHeader']['status'] != 0:
            raise SearchIndexError('Solr request failed: %s' % r)
    except Exception as e:
        raise SearchIndexError(e)


def app_index_delete(context, data_dict):
    r = requests.post(solr_url + '/update?commit=true', json={
        'delete': {
            'id': data_dict['app_id']
        }
    })
    # print(r.json())


def query_app(text, categories, language, organizations, sort):
    """
    :param text: str: text in the search box
    :param categories: list[str]
    :param language: str
    :param organizations: list[str]: OR
    :return:
    """
    filters = []

    if categories:
        for cate in categories:
            filters.append('categories:"%s"' % cate)  # AND

    if language:
        filters.append('language_ci:"%s"' % language) # search case insensitive field

    if organizations:
        v = ' OR '.join('"%s"' % org for org in organizations)
        filters.append('organization:(%s)' % v)

    # if related_datasets:
    #     for dataset in related_datasets:
    #         filters.append('related_datasets:"%s"' % dataset)

    query = {
        'query': text,
        'filter': filters,
        'facet': query_facets(),
        'sort': sort
    }

    r = requests.get(solr_url + '/query', json=query).json()
    pprint(r)
    r['response']['docs'] = list(map(recover_app_data, r['response']['docs']))
    return r


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


def recover_app_data(solr_doc):
    return json.loads(solr_doc['data_dict'])

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



public_functions = {
    # 'app_index': app_index,
    'app_index_delete': app_index_delete,
    # 'app_search': app_search,
}
