import uuid
import logging

from ckanext.servicehub.model.ServiceModel import App, Call

import ckan.lib.base as base
from ckan.lib import helpers as h
from ckanext.servicehub.dictization.dictize import service_dictize
import sqlalchemy
from paste.deploy.converters import asbool
from ckan.common import OrderedDict, c, g, config, request, _
import ckan.lib.dictization
import ckan.logic as logic
import ckan.lib.navl.dictization_functions
import ckan.plugins as plugins

from ckan.common import _
from ckanext.servicehub.model import MongoClient

log = logging.getLogger('ckan.logic')

# Define some shortcuts
# Ensure they are module-private so that they don't get loaded as available
# actions in the action API.
_validate = ckan.lib.navl.dictization_functions.validate
_table_dictize = ckan.lib.dictization.table_dictize
_check_access = logic.check_access
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
_get_or_bust = logic.get_or_bust

_select = sqlalchemy.sql.select
_aliased = sqlalchemy.orm.aliased
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_desc = sqlalchemy.desc
_case = sqlalchemy.case
_text = sqlalchemy.text

object2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}


def service_list(context, data_dict):
    session = context['session']
    model = context['model']
    service_list = session.query(App).all()
    return service_list


def service_show(context, data_dict):
    model = context['model']
    session = context['session']
    id = _get_or_bust(data_dict, 'id')
    service = session.query(App).filter(App.app_id == id).first()
    return service
def call_show(context, data_dict):
    model = context['model']
    session = context['session']
    id = _get_or_bust(data_dict, 'id')
    call = session.query(Call).filter(Call.call_id == id).first()
    return call

def service_req_form_show(context, data_dict):
    return MongoClient.findReqForm(data_dict['id'])


def call_list(context, data_dict):
    session = context['session']
    model = context['model']
    user = context['user']
    call_list = session.query(Call,App).filter(Call.call_user==user and Call.app_id==App.app_id).all()
    # call_list = session.query(Call).filter(Call.call_user==user).all()
    return call_list
