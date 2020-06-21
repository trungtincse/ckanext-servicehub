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
from ckan.common import c, g, request, config, _
import ckan.lib.navl.dictization_functions as dict_fns
from ckan.lib.search import SearchError
import ckan.lib.helpers as h
from ckan.logic import clean_dict, tuplize_dict, parse_params
from ckanext.servicehub.action import project_solr
from ckanext.servicehub.error.exception import CKANException
from ckanext.servicehub.model.ProjectModel import Project, ProjectCategory, ProjectTag, ProjectDatasetUsed, \
    ProjectAppUsed
from ckanext.servicehub.view import solr_common

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


def make_categories(session, tags, project_id):
    if not tags:
        return

    cate_names = []
    for tag in tags.split(','):
        cate = ProjectCategory(project_id=project_id, tag_name=tag)
        session.add(cate)
        cate_names.append(tag)

    return cate_names


def make_tags(session, tags, project_id):
    if not tags:
        return

    tag_names = []
    for tag in tags.split(','):
        cate = ProjectTag(project_id=project_id, tag_name=tag)
        session.add(cate)
        tag_names.append(tag)

    return tag_names


def map_dataset(context, project_id, name_or_id):
    session = context['session']
    if isinstance(name_or_id, list):
        pass
    else:
        name_or_id = [name_or_id]

    datasets_ids = []
    for i in name_or_id:
        try:
            result = get_action(u'package_show')(context, dict(id=i))
        except:
            raise CKANException(err_message='dataset: %s not found' % i)
        if result['private'] or result['state'] != 'active':
            raise CKANException(err_message='dataset: %s is private' % i)
        instance = ProjectDatasetUsed(project_id=project_id, dataset_id=result[u'id'], link='%s/dataset/%s' % (site_url, i))
        # instance.setOption()
        session.add(instance)
        datasets_ids.append(result['id'])
    return datasets_ids


def map_app(context, project_id, id):
    session = context['session']
    if id.startswith('http') or id.startswith('https'):
        instance = ProjectAppUsed(project_id=project_id, app_id=id, link=id)
    else:
        result = get_action(u'service_show')(context, dict(id=id))
        if 'app_detail' not in result:
            raise CKANException(err_message='application: %s not found' % id)
        instance = ProjectAppUsed(project_id=project_id, app_id=id, link='%s/service/%s' % (site_url, id))

    session.add(instance)
    return instance


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

        session = context['session']
        try:
            ins = Project()
            try:
                data_dict['o_avatar_image'] = store_file(data_dict['o_avatar_image'], "o_avatar_image", ins.id)
                data_dict['header_image'] = store_file(data_dict['header_image'], "header_image", ins.id)
            except:
                return jsonify(dict(success=False, error="Incorrect image format"))
            ins.setOption(**data_dict)
            session.add(ins)
            session.flush()
            categories_names = make_categories(session, data_dict.get('project_category'), ins.id)
            tags_names = make_tags(session, data_dict.get('project_tags'), ins.id)
            datasets_ids = map_dataset(context, ins.id, data_dict.get('dataset-id', []))
            map_app(context, ins.id, data_dict['link_or_id'])

            project_solr.index_project({
                'id': ins.id,
                'project_name': ins.project_name,
                'name': ins.name,
                'email': ins.email,
                'organization_name': ins.organization_name,
                'o_description': ins.o_description,
                'o_avatar_image': ins.o_avatar_image,
                'header_image': ins.header_image,
                'prj_summary': ins.prj_summary,
                'prj_goal': ins.prj_goal,
                'draft': ins.draft,
                'active': ins.active,
                'category': categories_names,
                'tags': tags_names,
                'datasets': datasets_ids
            })

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
                    project_solr.activate_project(id)
                    session.commit()
                except Exception as ex:
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
            project_solr.delete_project(id)
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


@project_blueprint.route('', methods=['GET'])
def index():
    search_result = project_solr.query_project(
        text=solr_common.query(),
        organization_name=request.params.get('organization_name'),
        categories=request.params.getlist('category'),
        tags=request.params.getlist('tags'),
        sort=request.params.get('sort', 'score asc, project_name asc')
    )

    page = h.Page(
        collection=search_result['response']['docs'],
        page=h.get_page_number(request.params),
        item_count=len(search_result['response']['docs'])
    )

    c.search_facets = project_solr.ckan_search_facets(search_result)
    c.search_facets_limits = False
    c.remove_url_param = solr_common.cuong_remove_url_param # override
    return base.render('project/search.html', {
        'query': request.params.get('q', ''),
        'sorting': _sorting,
        'sort_by_selected': request.params.get('sort', 'score desc, project_name asc'),
        'facet_titles': _facet_titles,
        'selected_filtered_fields': solr_common.selected_filtered_fields(),
        'selected_filtered_fields_grouped': solr_common.selected_filtered_fields_grouped(),
        'page': page,
        'search_facets': project_solr.ckan_search_facets(search_result),
        'remove_field': remove_field
    })


_facet_titles = {
    'organization_name': 'Organizations',
    'category': 'Categories',
    'tags': 'Tags'
}


_sorting = [
  ('Relevance', 'score desc, project_name asc'),
  ('Project Name Ascending', 'project_name asc'),
  ('Project Name Descending', 'project_name desc')
]


def remove_field(key, value=None, replace=None):
    return h.remove_url_param(key, value=value, replace=replace, controller='project', action='indexw')
