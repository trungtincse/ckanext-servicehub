import os
import logging
import ckan.logic
import requests
from ckan import authz
from ckanext.servicehub.model.ServiceModel import App, Call, AppParam, AppCodeVersion, CallInput, CallOutput
from requests.adapters import HTTPAdapter
from sqlalchemy import inspect
from urllib3 import Retry
from ckan.common import OrderedDict, c, g, config, request, _
import ckan.logic as logic

log = logging.getLogger('ckan.logic')

_get_or_bust = logic.get_or_bust
_check_access = ckan.logic.check_access
# http_session = requests.Session()
# retry = Retry(connect=3, backoff_factor=0.5)
# adapter = HTTPAdapter(max_retries=retry)
# http_session.mount('http://', adapter)
appserver_host = config.get('ckan.servicehub.appserver_host')
fileserver_host = config.get('ckan.servicehub.fileserver_host')
central_logger = logging.getLogger('logserver')
local_logger = logging.getLogger('local')

object2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}


def _asdict(obj):
    if obj == None:
        return dict(success=False, error="Not found")
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


# @logic.side_effect_free
# def service_list(context, data_dict):
#     session = context['session']
#     model = context['model']
#     service_list = session.query(App).all()
#     # map(lambda x:x.strftime(),service_list)
#     return [i.as_dict() for i in service_list]


@logic.side_effect_free
def service_show(context, data_dict):
    model = context['model']
    session = context['session']
    try:
        _check_access('service_show', context, dict(app_id=data_dict['id']))
    except Exception as ex:
        central_logger.info("user=%s&action=service_show&error_code=1" % context['user'])
        local_logger.info("%s %s %s" % (context['user'], "service_show", ex.message))
        return dict(success=False, error=ex.message)

    path = os.path.join(appserver_host, 'app', data_dict['id'])
    service = session.query(App).filter(App.app_id == data_dict['id']).first()
    if service != None:
        params = session.query(AppParam).filter(AppParam.app_id == data_dict['id']).all()
        code = session.query(AppCodeVersion).filter(AppCodeVersion.code_id == service.curr_code_id).first()
        all_codes = session.query(AppCodeVersion).filter(AppCodeVersion.app_id == data_dict['id']).all()
        assert code != None
        params = [i.as_dict() for i in params]
        service = _asdict(service)
        service['params'] = params
        service['code'] = _asdict(code)
        service['all_codes'] = [i.as_dict() for i in all_codes]
        central_logger.info("user=%s&action=service_show&error_code=0" % context['user'])
        local_logger.info("%s %s %s" % (context['user'], "service_show", "Success"))
        return service
    else:
        central_logger.info("user=%s&action=service_show&error_code=0" % context['user'])
        local_logger.info("%s %s %s" % (context['user'], "service_show", "Success"))
        return _asdict(service)


def service_by_slug_show(context, data_dict):
    model = context['model']
    session = context['session']
    slug_name = _get_or_bust(data_dict, 'slug_name')
    service = session.query(App).filter(App.slug_name == slug_name).first()
    if service == None:
        central_logger.info("user=%s&action=service_by_slug_show&error_code=1" % context['user'])
        local_logger.info(
            "%s %s %s" % (context['user'], "service_by_slug_show", "Application %s not found") % slug_name)
    else:
        central_logger.info("user=%s&action=service_by_slug_show&error_code=0" % context['user'])
        local_logger.info("%s %s %s" % (context['user'], "service_by_slug_show", "Success"))
        return _asdict(service)


def call_show(context, data_dict):
    model = context['model']
    session = context['session']
    id = _get_or_bust(data_dict, 'id')
    try:
        _check_access('call_show', context, dict(call_id=id))
    except Exception as ex:
        pass
    inputs = session.query(CallInput).filter(CallInput.call_id == id).all()
    outputs = session.query(CallOutput).filter(CallOutput.call_id == id).all()
    call = session.query(Call).filter(Call.call_id == id).first()
    if call == None:
        central_logger.info("user=%s&action=call_show&error_code=1" % context['user'])
        local_logger.info("%s %s %s" % (context['user'], "call_show", "Call %s not found" % id))
        return dict(success=False, error="Not found")
    else:
        call = call.as_dict()
        call['inputs'] = [i.as_dict() for i in inputs]
        call['outputs'] = [o.as_dict() for o in outputs]
        central_logger.info("user=%s&action=call_show&error_code=0" % context['user'])
        local_logger.info("%s %s %s" % (context['user'], "call_show", str(call)))
        return call


@logic.side_effect_free
def call_result(context, data_dict):
    model = context['model']
    session = context['session']
    id = _get_or_bust(data_dict, 'id')
    try:
        _check_access('call_show', context, dict(call_id=id))
    except Exception as ex:
        pass
    inputs = session.query(CallInput).filter(CallInput.call_id == id).all()
    outputs = session.query(CallOutput).filter(CallOutput.call_id == id).all()
    call = session.query(Call).filter(Call.call_id == id).first()
    if call == None:
        central_logger.info("user=%s&action=call_show&error_code=1" % context['user'])
        local_logger.info("%s %s %s" % (context['user'], "call_result", "Call %s not found" % id))
        return dict(success=False, error="Not found")
    else:
        if call.call_status == 'STARTED':
            call = dict(message="Call is handling")
            central_logger.info("user=%s&action=call_show&error_code=1" % context['user'])
            local_logger.info("%s %s %s" % (context['user'], "call_result", str(call)))
            return call
        elif call.call_status == 'TIMEOUT':
            call = dict(message="Call is timeout")
            central_logger.info("user=%s&action=call_show&error_code=1" % context['user'])
            local_logger.info("%s %s %s" % (context['user'], "call_result", str(call)))
            return call
        elif call.call_status == 'FAILED':
            call = dict(message="Call is failed")
            central_logger.info("user=%s&action=call_show&error_code=1" % context['user'])
            local_logger.info("%s %s %s" % (context['user'], "call_result", str(call)))
            return call
        else:
            call =dict()
            call['inputs'] = [i.as_dict_for_api() for i in inputs]
            call['outputs'] = [o.as_dict_for_api() for o in outputs]
            central_logger.info("user=%s&action=call_show&error_code=0" % context['user'])
            local_logger.info("%s %s %s" % (context['user'], "call_result", str(call)))
            return call


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
    central_logger.info("user=%s&action=call_list&error_code=0" % context['user'])
    local_logger.info("%s %s %s" % (context['user'], "call_list", "Success"))
    return result


public_functions = dict(
    call_result=call_result,
    call_list=call_list,
    service_show=service_show,
    call_show=call_show,
    service_by_slug_show=service_by_slug_show
)
