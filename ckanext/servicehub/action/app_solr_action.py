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


def query_app(text, categories, language, organizations, sort):
    """
    :param text: str: text in the search box
    :param categories: list[str]: AND
    :param language: str
    :param organizations: list[str]: OR
    :return:
    """
    text = text or "*:*"  # avoid None

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
    # recover docs: deserialize 'data_dict' key
    print r
    recovered_docs = []
    for ori_doc in r['response']['docs']:
        new_doc = json.loads(ori_doc['data_dict'])
        recovered_docs.append(new_doc)
    r['response']['docs'] = recovered_docs
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
