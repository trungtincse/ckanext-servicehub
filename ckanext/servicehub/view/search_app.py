# encoding: utf-8
from __future__ import print_function
cprint = print
from collections import defaultdict
import errno
import keyword
import mimetypes
import os
import random
import string
from pprint import pprint

import slug
import json
import logging

from ckanext.servicehub.action import indexapp

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
from ckanext.servicehub.action.create import build_code
from ckan.common import OrderedDict, c, g, config, request, _
from flask import Blueprint, jsonify, send_file
from flask.views import MethodView
from ckanext.servicehub.model.ServiceModel import *
from ckan.model import types as _types
from ckanext.servicehub.model.ServiceModel import App

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

appserver_host = config.get('ckan.servicehub.appserver_host')


blueprint = Blueprint('appsearch', __name__, url_prefix='/app/search')


def register_rules():
    blueprint.add_url_rule('/', view_func=index, strict_slashes=False)


def index():
    # co`ntext = {
    #     'model': model,
    #     'session': model.Session,
    #     'user': g.user,
    #     # 'for_view': True
    # }

    search_result = indexapp.query_app(
        text=query() or '*:*',
        organizations=request.params.getlist('organization'),
        categories=request.params.getlist('categories'),
        language=request.params.get('language')
    )

    c.page = h.Page(collection=docs(search_result), page=h.get_page_number(request.params), item_count=len(docs(search_result)))
    return base.render('service/search.html', {
        'query': query() or '',
        'sort_by_selected': request.params.get('sort', 'score desc, metadata_modified desc'),
        'selected_filtered_fields': selected_filtered_fields(),
        'selected_filtered_fields_grouped': selected_filtered_fields_grouped()
    })


def query():
    request.params.get('q')


def docs(search_result):
    return search_result['response']['docs']


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


register_rules()