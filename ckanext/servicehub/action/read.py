import os
import logging

import requests
from ckanext.servicehub.model.ServiceModel import App, Call, AppParam, AppCodeVersion
from requests.adapters import HTTPAdapter
from sqlalchemy import inspect
from urllib3 import Retry
from ckan.common import OrderedDict, c, g, config, request, _
import ckan.logic as logic

log = logging.getLogger('ckan.logic')

_get_or_bust = logic.get_or_bust

# http_session = requests.Session()
# retry = Retry(connect=3, backoff_factor=0.5)
# adapter = HTTPAdapter(max_retries=retry)
# http_session.mount('http://', adapter)
appserver_host = config.get('ckan.servicehub.appserver_host')
fileserver_host = config.get('ckan.servicehub.fileserver_host')

object2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}


def _asdict(obj):
    if obj == None:
        return dict(success=False, error="Not found")
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


@logic.side_effect_free
def service_list(context, data_dict):
    session = context['session']
    model = context['model']
    service_list = session.query(App).all()
    # map(lambda x:x.strftime(),service_list)
    return [i.as_dict() for i in service_list]


@logic.side_effect_free
def service_show(context, data_dict):
    model = context['model']
    session = context['session']
    path = os.path.join(appserver_host, 'app', data_dict['id'])
    service = session.query(App).filter(App.app_id == data_dict['id']).first()
    if service != None:
        params = session.query(AppParam).filter(AppParam.app_id == data_dict['id']).all()
        code = session.query(AppCodeVersion).filter(AppCodeVersion.code_id == service.curr_code_id).first()
        assert code != None
        params = [i.as_dict() for i in params]
        service = _asdict(service)
        service['params'] = params
        service['code'] = _asdict(code)
        return service
    else:
        return _asdict(service)


def service_by_slug_show(context, data_dict):
    model = context['model']
    session = context['session']
    slug_name = _get_or_bust(data_dict, 'slug_name')
    service = session.query(App).filter(App.slug_name == slug_name).first()
    return _asdict(service)


def call_show(context, data_dict):
    model = context['model']
    session = context['session']
    id = _get_or_bust(data_dict, 'id')
    path = os.path.join(appserver_host, 'call', id)
    return requests.get(path).json()


def call_list(context, data_dict):
    session = context['session']
    model = context['model']
    user = context['user']
    call_list = session.query(Call, App).join(App, Call.app_id == App.app_id).filter(Call.user_id == user).all()
    result = []
    for c, a in call_list:
        dict_c = _asdict(c)
        dict_a = _asdict(a)
        dict_a.update(dict_c)
        result.append(dict_a)
    return result


# def resource_io_view_show(context,data_dict):


public_functions = dict(service_list=service_list,
                        call_list=call_list,
                        service_show=service_show,
                        call_show=call_show,
                        # reqform_show=reqform_show,
                        # input_show=input_show,
                        # output_show=output_show,
                        service_by_slug_show=service_by_slug_show
                        )
