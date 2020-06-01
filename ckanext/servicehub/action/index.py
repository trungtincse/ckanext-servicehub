import json
import os
import logging

import requests
from sqlalchemy import inspect
from ckan.common import OrderedDict, c, g, config, request, _
import ckan.logic as logic
from ckan.lib.search.common import SearchIndexError
log = logging.getLogger('ckan.logic')

solr_url = config.get('ckan.servicehub.app_solr_url')


def _asdict(obj):
    if obj == None:
        return dict(success=False, error="Not found")
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


@logic.side_effect_free
def app_index(context, data_dict):
    app = data_dict
    """
    :param app: dict
    :return:
    """
    app['data_dict'] = json.dumps(app, ensure_ascii=False)
    org = app.pop('organization', None)
    if org:
        app['organization'] = org['name']

    app['owner'] = app['owner']['name']

    url = solr_url + '/update/json/docs?commit=true'
    try:
        r = requests.post(url, json=app).json()
        if r['responseHeader']['status'] != 0:
            print('Index error: ' + json.dumps(r['error']))
    except Exception as e:
        print('Failed to do request to Solr server')
        raise SearchIndexError(e)


public_functions = {
    'app_index': app_index
}
