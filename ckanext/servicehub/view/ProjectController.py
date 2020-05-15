import ast
import os
import shutil

import requests
from flask.views import MethodView
from werkzeug.datastructures import FileStorage

from ckan.lib import helpers
from flask import Blueprint, Response, jsonify, send_from_directory
import json
import ckan.lib.base as base
from ckan import model, logic
from ckan.common import g, request, config, _
import ckan.lib.navl.dictization_functions as dict_fns
from ckan.logic import clean_dict, tuplize_dict, parse_params
from ckanext.servicehub.error.exception import CKANException
from ckanext.servicehub.model.ProjectModel import Project, ProjectCategory, ProjectTag, ProjectDatasetUsed, \
    ProjectAppUsed

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
site_url = config.get('ckan.site_url')

project_blueprint = Blueprint(u'project', __name__, url_prefix=u'/project')



def store_file(upload_file, type, project_id):
    dir_path = os.path.join(storage_path, 'project',
                            project_id, type)
    try:
        os.makedirs(dir_path)
    except OSError as e:
        raise Exception()
    filepath = os.path.join(dir_path, type)
    upload_file.save(filepath)
    return os.path.join(site_url, 'project', 'file',
                        project_id, type)


def delete_file(type, project_id):
    dir_path = os.path.join(storage_path, 'project',
                            project_id, type)

    filepath = os.path.join(dir_path, type)
    if os.path.exists(filepath):
        os.remove(filepath)


def make_tag(session, tags, type, project_id):
    if tags == None or tags == '': return;
    tag_list = tags.split(',')
    data = [dict(project_id=project_id, tag_name=i) for i in tag_list]
    if type == 'project_category':
        instances = [ProjectCategory() for x in data]
    elif type == 'project_tags':
        instances = [ProjectTag() for x in data]
    map(lambda x: x[1].setOption(**data[x[0]]), enumerate(instances))
    map(lambda x: session.add(x), instances)


def  map_dataset(context, project_id, name_or_id):
    session = context['session']
    model = context['model']
    if isinstance(name_or_id, list):
        pass
    else:
        name_or_id = [name_or_id]
    for i in name_or_id:
        try:
            result = get_action(u'package_show')(context, dict(id=i))
        except:
            raise CKANException(err_message='dataset: %s not found' % i)
        if result['private'] or result['state'] != 'active':
            raise CKANException(err_message='dataset: %s is private' % i)
        instance = ProjectDatasetUsed()
        instance.setOption(project_id=project_id, dataset_id=result[u'id'], link='%s/dataset/%s' % (site_url, i))
        session.add(instance)


def map_app(context, project_id, id):
    session = context['session']
    if id.find('http')>=0 or id.find('https')>=0:
        instance = ProjectAppUsed(project_id=project_id, app_id=id, link=id)
        session.add(instance)
        return
    result = get_action(u'service_show')(context, dict(id=id))
    if 'app_detail' not in result:
        raise CKANException(err_message='application: %s not found' % id)
    instance = ProjectAppUsed(project_id=project_id, app_id=id, link='%s/service/%s' % (site_url, id))
    session.add(instance)


def _prepare():
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }

    return context


class ProjectCreateView(MethodView):
    def post(self):
        context = _prepare()
        data_dict = clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.form))))

        data_dict.update(clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.files)))))
        try:
            session = context['session']
            model = context['model']

            ins = Project()
            data_dict['o_avatar_image'] = store_file(data_dict['o_avatar_image'], "o_avatar_image", ins.id)
            data_dict['header_image'] = store_file(data_dict['header_image'], "header_image", ins.id)
            ins.setOption(**data_dict)
            session.add(ins)
            session.flush()
            make_tag(session, data_dict.get('project_category', None), 'project_category', ins.id)

            make_tag(session, data_dict.get('project_tags', None), 'project_tags', ins.id)
            map_dataset(context, ins.id, data_dict.get('dataset-id', []))
            # assert False

            map_app(context, ins.id, data_dict['link_or_id'])
            session.commit()
        except Exception as ex:
            session.rollback()
            print type(ex)
            print ex.message
            error = getattr(ex, "err_message", 'Opps! Something is wrong')
            return jsonify(dict(success=False, error=error))
        return jsonify(dict(success=True))

    def get(self):
        extra_vars = {}
        context = _prepare()
        project_tags = get_action(u'vocabulary_show')(context, dict(id='project_tags'))['tags']
        project_category = get_action(u'vocabulary_show')(context, dict(id='project_category'))['tags']
        extra_vars['project_category'] = project_category
        extra_vars['project_tags'] = project_tags
        return base.render('project/new.html', extra_vars)


@project_blueprint.route('/', methods=['GET'])
def index():
    context = _prepare()
    session = context['session']
    instances = session.query(Project).all()
    additions = []
    extra_vars = {}
    for ins in instances:
        id = ins.id
        adds = {}
        adds['category'] = session.query(ProjectCategory).filter(ProjectCategory.project_id == id).all()
        adds['tags'] = session.query(ProjectTag).filter(ProjectTag.project_id == id).all()
        additions.append(adds)
    extra_vars['projects'] = zip(instances, additions)
    return base.render('project/index.html', extra_vars=extra_vars)


class ProjectReadView(MethodView):
    def get(self, id):
        extra_vars = {}
        context = _prepare()
        session = context['session']
        ins = session.query(Project).filter(Project.id == id).first()
        if ins == None:
            base.abort(404, 'Page not found')
        else:
            extra_vars['category'] = session.query(ProjectCategory).filter(ProjectCategory.project_id == id).all()
            extra_vars['tags'] = session.query(ProjectTag).filter(ProjectTag.project_id == id).all()
            extra_vars['datasets'] = [i.as_dict() for i in session.query(ProjectDatasetUsed).filter(
                ProjectDatasetUsed.project_id == id).all()]
            extra_vars['apps'] = session.query(ProjectAppUsed).filter(ProjectAppUsed.project_id == id).all()
            extra_vars['instance'] = ins
            print extra_vars
            return base.render('project/read.html', extra_vars=extra_vars)

    def post(self, id):
        extra_vars = {}
        context = _prepare()
        session = context['session']
        ins = session.query(Project).filter(Project.id == id).first()
        if request.params['action'] == 'approve':
            if ins == None:
                return jsonify(success=False, error='Not Exists')
            else:
                ins.active = True
                session.add(ins)
                try:
                    session.commit()
                except Exception as  ex:
                    session.rollback()
                    return jsonify(dict(success=False, error='Opps! Something is wrong'))
            return jsonify(success=True, error='')

    def delete(self, id):
        context = _prepare()
        session = context['session']
        ins = session.query(Project).filter(Project.id == id).first()
        try:
            session.delete(ins)
            session.commit()
        except Exception as  ex:
            session.rollback()
            return jsonify(dict(success=False, error='Opps! Something is wrong'))
        dir_path = os.path.join(storage_path, 'project',
                                id)
        shutil.rmtree(dir_path)
        return jsonify(success=True)


@project_blueprint.route('/file/<id>/<type>', methods=['GET', 'DELETE'])
def file(id, type):
    if request.method == "DELETE":
        delete_file(type, id)
        return jsonify(success=True)
    elif request.method == "GET":
        dir_path = os.path.join(storage_path, 'project',
                                id, type)
        return send_from_directory(dir_path, type)


project_blueprint.add_url_rule(
    u'/new',
    methods=[u'GET', u'POST'],
    view_func=ProjectCreateView.as_view(str(u'new')))
project_blueprint.add_url_rule(
    u'/read/<id>',
    methods=[u'GET', u'POST', u'DELETE'],
    view_func=ProjectReadView.as_view(str(u'read')))
