import json
import logging
from pprint import pprint

import requests

from ckan import logic, authz
from ckan.common import g, config, request
from ckan.lib.search.common import SearchIndexError, SearchError
from ckanext.servicehub.main.config_and_common import ServiceLanguage
from ckanext.servicehub.model.ServiceModel import AppCategory, AppRelatedDataset

log = logging.getLogger('ckan.logic')

solr_url = config.get('ckan.servicehub.app_solr_url')


def index_app(app, categories, datasets):
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
    # group_id = model.Group.get(app.organization).id
    # app_json['permission_labels'] = index_permission_label(group_id)
    try:
        url = solr_url + '/update/json/docs?commit=true'
        r = requests.post(url, json=app_json).json()
        if r['responseHeader']['status'] != 0:
            raise SearchIndexError('Solr request failed: %s' % r)
    except Exception as e:
        raise SearchIndexError(e)


def delete_app(data_dict):
    r = requests.post(solr_url + '/update?commit=true', json={
        'delete': {
            'id': data_dict['app_id']
        }
    }).json()

    if 'error' in r:
        raise SearchError(r['error']['msg'])


def query_app(text, categories, language, organization, sort):
    """
    :param text: str: text in the search box
    :param categories: list[str]
    :param language: str
    :param organization: str
    :param sort: find values in ServiceController
    :return:
    """
    filters = []

    if categories:
        for cate in categories:
            filters.append('category:"%s"' % cate)  # AND

    if language:
        filters.append('language_ci:"%s"' % language) # search case insensitive field

    if organization:
        filters.append('organization:"%s"' % organization)

    # permission
    if authz.is_sysadmin(g.user):
        # pprint('is admin: show all')
        pass
    elif g.user:
        # a user logged in
        filters.append('app_status:START OR (organization:(%s))' % ' OR '.join(user_groups_names(g.user))) # 0 groups is ok
        # pprint('groups: %s' % list(user_groups_names(g.user)))
    else:
        # anonymous user/not login
        filters.append('app_status:START')
        # pprint('Anonymous user')

    query = {
        'query': text,
        'filter': filters,
        'facet': query_facets(),
        'sort': sort
    }

    r = requests.get(solr_url + '/query', json=query).json()
    if r.get('error'):
        raise SearchError(r['error']['msg'])

    r['response']['docs'] = list(map(recover_app_data, r['response']['docs']))
    return r

#########################
# private functions

def index_permission_label(group_id):
    return ['public']


def search_permission_labels(user_id):
    labels = ['public']
    orgs = logic.get_action('organization_list_for_user')({'user': user_id}, {'permission': 'read'})
    for org in orgs:
        labels.append('member-' + org['id'])
    return labels

def user_groups_names(user_id):
    orgs = logic.get_action('organization_list_for_user')({'user': user_id}, {'permission': 'read'})
    for org in orgs:
        yield org['name']


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
        # result = e
        return empty_search_facets()
    else:
        result = {}
        for field in facet_fields:
            items = []
            for bucket in facets[field]['buckets']:
                item = {
                    'name': bucket['val'],
                    'display_name': language_display_name(bucket['val']) if field == 'language' else bucket['val'],
                    'count': bucket['count'],
                    'active': bucket['val'] in request.params.getlist(field)
                }
                items.append(item)

            result[field] = {
                'title': field,
                'items': items
            }
        return result


def empty_search_facets():
    return {field: { 'title': field, 'items': [] } for field in facet_fields}


def language_display_name(formal_language_val):
    for language in ServiceLanguage:
        if language.formal_text == formal_language_val:
            return language.ui_text
    else:
        raise ValueError('Unknown language: ' + formal_language_val)


public_functions = {
    # 'app_index': app_index,
    'app_index_delete': delete_app,
    # 'app_search': app_search,
}
