import ast
import os

import requests
from werkzeug.datastructures import FileStorage

from ckan.lib import helpers
from flask import Blueprint, Response, jsonify, send_file, redirect
import json
from ckanext.servicehub.model.ServiceModel import Call, App
from ckanext.servicehub.model.ProjectModel import Project
import ckan.lib.base as base
from ckan.model.user import User
from ckan import model, logic, authz
from ckan.common import g, c, request, config, _
import ckan.lib.navl.dictization_functions as dict_fns
from ckan.logic import clean_dict, tuplize_dict, parse_params

_check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
appserver_host = config.get('ckan.servicehub.appserver_host')
storage_path = config.get('ckan.storage_path')
app_admin_blueprint = Blueprint(u'appadmin', __name__, url_prefix=u'/appadmin')
prj_admin_blueprint = Blueprint(u'prjadmin', __name__, url_prefix=u'/prjadmin')


@app_admin_blueprint.route('', methods=["GET"])
def index():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        authz.is_sysadmin(context['user'])
    except Exception as ex:
        return base.abort(404, _(u'Page not found'))
    return base.render('admin/app_index.html', None)


@prj_admin_blueprint.route('', methods=["GET"])
def index():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        authz.is_sysadmin(context['user'])
    except Exception as ex:
        return base.abort(404, _(u'Page not found'))
    return base.render('admin/prj_index.html', None)


@app_admin_blueprint.route('/ajax', methods=["GET"])
def getajax():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        authz.is_sysadmin(context['user'])
    except Exception as ex:
        return base.abort(404, _(u'Page not found'))
    session = context[u'session']
    appInsLst = session.query(App).all()
    appLst = map(lambda ins: [ins.app_id, ins.app_name, ins.owner, ins.organization, ins.app_status], appInsLst)
    return jsonify(appLst)


@prj_admin_blueprint.route('/ajax', methods=["GET"])
def getajax():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        authz.is_sysadmin(context['user'])
    except Exception as ex:
        return base.abort(404, _(u'Page not found'))
    session = context[u'session']
    prjInsLst = session.query(Project).all()
    prjLst = map(lambda ins: [ins.id, ins.project_name, ins.name, ins.email, ins.organization_name, 'YES' if ins.active else 'NO'],
                 prjInsLst)
    return jsonify(prjLst)


@app_admin_blueprint.route('/action/<action_name>', methods=["GET"])
def action(action_name):
    app_id = request.params.get('app_id', None)
    if app_id == None:
        base.abort(404, _(u'App not found'))
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        authz.is_sysadmin(context['user'])
    except Exception as ex:
        return base.abort(404, _(u'Page not found'))
    session = context['session']
    service_ins = session.query(App).filter(App.app_id == app_id).first()
    if service_ins == None:
        base.abort(404, _(u'App not found'))
    try:
        if action_name == 'stop':
            service_ins.app_status = 'STOP'
            session.add(service_ins)
        elif action_name == 'debug':
            service_ins.app_status = 'DEBUG'
            session.add(service_ins)
        elif action_name == 'start':
            service_ins.app_status = 'START'
            session.add(service_ins)
        elif action_name == 'delete':
            session.delete(service_ins)
        session.commit()
    except:
        session.rollback()
    return redirect('/appadmin')

@prj_admin_blueprint.route('/action/<action_name>', methods=["GET"])
def action(action_name):
    prj_id = request.params.get('prj_id', None)
    if prj_id == None:
        base.abort(404, _(u'Project not found'))
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }
    try:
        authz.is_sysadmin(context['user'])
    except Exception as ex:
        return base.abort(404, _(u'Page not found'))
    session = context['session']
    project_ins = session.query(Project).filter(Project.id == prj_id).first()
    if project_ins == None:
        base.abort(404, _(u'Project not found'))
    try:
        if action_name == 'approve':
            project_ins.active = True
            session.add(project_ins)
        elif action_name == 'reject':
            project_ins.active = False
            session.add(project_ins)
        if action_name == 'delete':
            session.delete(project_ins)
        session.commit()
    except:
        session.rollback()
    return redirect('/prjadmin')