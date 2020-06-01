import os
import logging

import requests
from sqlalchemy import inspect
from ckan.common import OrderedDict, c, g, config, request, _
import ckan.logic as logic

log = logging.getLogger('ckan.logic')

solr_url = config.get('ckan.servicehub.app_solr_url')


def _asdict(obj):
    if obj == None:
        return dict(success=False, error="Not found")
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


@logic.side_effect_free
def app_search(context, data_dict):

    return query_app(
        text=data_dict.get('text'),
        categories=data_dict.get('categories'),
        language=data_dict.get('language'),
        organizations=data_dict.get('organizations'),
        # related_datasets=data_dict.get('related_datasets'),
    )


def query_app(text=None, categories=None, language=None, organizations=None, related_datasets=None):
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
            filters.append('categories:"%s"' % cate) # AND

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
        'facet': {
            'language': {
                'terms': {
                    'field': 'language',
                    'limit': 5
                }
            },
            'organization': {
                'terms': {
                    'field': 'organization',
                    'limit': 5
                }
            },
            'related_datasets': {
                'terms': {
                    'field': 'related_datasets',
                    'limit': 5
                }
            },
        }
    }

    r = requests.get(solr_url + '/query', json=query).json()
    return r


public_functions = {
    'app_search': app_search
}
