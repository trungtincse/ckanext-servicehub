import ast
import cgi

import requests
from paste.deploy.converters import asbool
from werkzeug.datastructures import FileStorage
import ckan.lib.helpers as h
from ckan.controllers.home import CACHE_PARAMETERS
from ckan.controllers.package import PackageController
from ckan.lib import helpers
from flask import Blueprint, Response, jsonify
import json
import ckan.lib.base as base
from ckan import model, logic
from ckan.common import g, request, config, c, _
import ckan.lib.navl.dictization_functions as dict_fns
from ckan.logic import clean_dict, tuplize_dict, parse_params
from ckanext.servicehub.model.ServiceModel import AppRelatedDataset, App

from ckanext.servicehub.model.ProjectModel import ProjectDatasetUsed, Project

get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
appserver_host = config.get('ckan.servicehub.appserver_host')

package_blueprint = Blueprint(u'package', __name__, url_prefix=u'/dataset')


def _prepare(self, data=None):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user
    }

    return context


@package_blueprint.route('/new', methods=["GET"])
def new():
    extra_vars = PackageExtraController().new()
    return base.render('package/new.html', extra_vars)


@package_blueprint.route('/<id>', methods=["GET"])
def read(id):
    extra_vars = PackageExtraController().read(id)
    package_id = model.Package.get(id).id
    extra_vars['app_related'] = [ins.as_dict() for ins in model.Session.query(App)
        .join(AppRelatedDataset, App.app_id == AppRelatedDataset.app_id)
        .filter(AppRelatedDataset.package_id == package_id).all()]
    extra_vars['project_related'] = [ins.as_dict() for ins in model.Session.query(Project)
        .join(ProjectDatasetUsed, Project.id == ProjectDatasetUsed.project_id)
        .filter(AppRelatedDataset.package_id == package_id).all()]
    return base.render('package/read.html', extra_vars)


@package_blueprint.route('/app/<id>', methods=["GET"])
def app(id):
    extra_vars = PackageExtraController().edit(id)
    return base.render('package/relate_app.html')


@package_blueprint.route('/new_app/<id>', methods=["GET", "POST"])
def new_app(id):
    return PackageExtraController().new_app(id)


class PackageExtraController(PackageController):
    def edit(self, id, data=None, errors=None, error_summary=None):
        package_type = self._get_package_type(id)
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}

        if context['save'] and not data and request.method == 'POST':
            return self._save_edit(id, context, package_type=package_type)
        try:
            c.pkg_dict = get_action('package_show')(dict(context,
                                                         for_view=True),
                                                    {'id': id})
            context['for_edit'] = True
            old_data = get_action('package_show')(context, {'id': id})
            # old data is from the database and data is passed from the
            # user if there is a validation error. Use users data if there.
            if data:
                old_data.update(data)
            data = old_data
        except (NotFound, NotAuthorized):
            base.abort(404, _('Dataset not found'))
        # are we doing a multiphase add?
        if data.get('state', '').startswith('draft'):
            c.form_action = h.url_for(controller='package', action='new')
            c.form_style = 'new'
            return self.new(data=data, errors=errors,
                            error_summary=error_summary)

        c.pkg = context.get("package")
        c.resources_json = h.json.dumps(data.get('resources', []))

        try:
            check_access('package_update', context)
        except NotAuthorized:
            base.abort(403, _('User %r not authorized to edit %s') % (c.user, id))
        # convert tags if not supplied in data
        if data and not data.get('tag_string'):
            data['tag_string'] = ', '.join(h.dict_list_reduce(
                c.pkg_dict.get('tags', {}), 'name'))
        errors = errors or {}
        form_snippet = self._package_form(package_type=package_type)
        form_vars = {'data': data, 'errors': errors,
                     'error_summary': error_summary, 'action': 'edit',
                     'dataset_type': package_type,
                     }
        c.errors_json = h.json.dumps(errors)

        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)

        # we have already completed stage 1
        form_vars['stage'] = ['active']
        if data.get('state', '').startswith('draft'):
            form_vars['stage'] = ['active', 'complete']

        edit_template = self._edit_template(package_type)
        print edit_template
        return {'form_vars': form_vars,
                'form_snippet': form_snippet,
                'dataset_type': package_type}

    def read(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'for_view': True,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': id, 'include_tracking': True}

        # interpret @<revision_id> or @<date> suffix
        split = id.split('@')
        if len(split) == 2:
            data_dict['id'], revision_ref = split
            if model.is_id(revision_ref):
                context['revision_id'] = revision_ref
            else:
                try:
                    date = h.date_str_to_datetime(revision_ref)
                    context['revision_date'] = date
                except TypeError as e:
                    base.abort(400, _('Invalid revision format: %r') % e.args)
                except ValueError as e:
                    base.abort(400, _('Invalid revision format: %r') % e.args)
        elif len(split) > 2:
            base.abort(400, _('Invalid revision format: %r') %
                       'Too many "@" symbols')

        # check if package exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
            c.pkg = context['package']
        except (NotFound, NotAuthorized):
            base.abort(404, _('Dataset not found'))

        # used by disqus plugin
        c.current_package_id = c.pkg.id

        # can the resources be previewed?
        for resource in c.pkg_dict['resources']:
            # Backwards compatibility with preview interface
            resource['can_be_previewed'] = self._resource_preview(
                {'resource': resource, 'package': c.pkg_dict})

            resource_views = get_action('resource_view_list')(
                context, {'id': resource['id']})
            resource['has_views'] = len(resource_views) > 0

        package_type = c.pkg_dict['type'] or 'dataset'
        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)

        template = self._read_template(package_type)
        return {'dataset_type': package_type}

    def new(self, data=None, errors=None, error_summary=None):
        if data and 'type' in data:
            package_type = data['type']
        else:
            package_type = self._guess_package_type(True)

        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}
        c.pkg = "package"
        # Package needs to have a organization group in the call to
        # check_access and also to save it
        try:
            check_access('package_create', context)
        except NotAuthorized:
            base.abort(403, _('Unauthorized to create a package'))

        if context['save'] and not data and request.method == 'POST':
            return self._save_new(context, package_type=package_type)

        data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
            request.params, ignore_keys=CACHE_PARAMETERS))))
        c.resources_json = h.json.dumps(data.get('resources', []))
        # convert tags if not supplied in data
        if data and not data.get('tag_string'):
            data['tag_string'] = ', '.join(
                h.dict_list_reduce(data.get('tags', {}), 'name'))

        errors = errors or {}
        error_summary = error_summary or {}
        # in the phased add dataset we need to know that
        # we have already completed stage 1
        stage = ['active']
        if data.get('state', '').startswith('draft'):
            stage = ['active', 'complete']

        # if we are creating from a group then this allows the group to be
        # set automatically
        data['group_id'] = request.params.get('group') or \
                           request.params.get('groups__0__id')

        form_snippet = self._package_form(package_type=package_type)
        form_vars = {'data': data, 'errors': errors,
                     'error_summary': error_summary,
                     'action': 'new', 'stage': stage,
                     'dataset_type': package_type,
                     }
        c.errors_json = h.json.dumps(errors)

        self._setup_template_variables(context, {},
                                       package_type=package_type)

        new_template = self._new_template(package_type)
        return {'form_vars': form_vars,
                'form_snippet': form_snippet,
                'dataset_type': package_type}

    def new_app(self, id):
        ''' FIXME: This is a temporary action to allow styling of the
        forms. '''
        # if request.method == 'POST' and not data:
        #     save_action = request.params.get('save')
        #     data = data or \
        #            clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
        #                request.POST))))
        #     # we don't want to include save as it is part of the form
        #     del data['save']
        #     resource_id = data['id']
        #     del data['id']
        #
        #     context = {'model': model, 'session': model.Session,
        #                'user': c.user, 'auth_user_obj': c.userobj}
        #
        #     # see if we have any data that we are trying to save
        #     data_provided = False
        #     for key, value in data.iteritems():
        #         if ((value or isinstance(value, cgi.FieldStorage))
        #             and key != 'resource_type'):
        #             data_provided = True
        #             break
        #
        #     if not data_provided and save_action != "go-dataset-complete":
        #         if save_action == 'go-dataset':
        #             # go to final stage of adddataset
        #             h.redirect_to(controller='package', action='edit', id=id)
        #         # see if we have added any resources
        #         try:
        #             data_dict = get_action('package_show')(context, {'id': id})
        #         except NotAuthorized:
        #             abort(403, _('Unauthorized to update dataset'))
        #         except NotFound:
        #             abort(404, _('The dataset {id} could not be found.'
        #                          ).format(id=id))
        #         if not len(data_dict['resources']):
        #             # no data so keep on page
        #             msg = _('You must add at least one data resource')
        #             # On new templates do not use flash message
        #
        #             if asbool(config.get('ckan.legacy_templates')):
        #                 h.flash_error(msg)
        #                 h.redirect_to(controller='package',
        #                               action='new_resource', id=id)
        #             else:
        #                 errors = {}
        #                 error_summary = {_('Error'): msg}
        #                 return self.new_resource(id, data, errors,
        #                                          error_summary)
        #         # XXX race condition if another user edits/deletes
        #         data_dict = get_action('package_show')(context, {'id': id})
        #         get_action('package_update')(
        #             dict(context, allow_state_change=True),
        #             dict(data_dict, state='active'))
        #         h.redirect_to(controller='package', action='read', id=id)
        #
        #     data['package_id'] = id
        #     try:
        #         if resource_id:
        #             data['id'] = resource_id
        #             get_action('resource_update')(context, data)
        #         else:
        #             get_action('resource_create')(context, data)
        #     except ValidationError as e:
        #         errors = e.error_dict
        #         error_summary = e.error_summary
        #         return self.new_resource(id, data, errors, error_summary)
        #     except NotAuthorized:
        #         abort(403, _('Unauthorized to create a resource'))
        #     except NotFound:
        #         abort(404, _('The dataset {id} could not be found.'
        #                      ).format(id=id))
        #     if save_action == 'go-metadata':
        #         # XXX race condition if another user edits/deletes
        #         data_dict = get_action('package_show')(context, {'id': id})
        #         get_action('package_update')(
        #             dict(context, allow_state_change=True),
        #             dict(data_dict, state='active'))
        #         h.redirect_to(controller='package', action='read', id=id)
        #     elif save_action == 'go-dataset':
        #         # go to first stage of add dataset
        #         h.redirect_to(controller='package', action='edit', id=id)
        #     elif save_action == 'go-dataset-complete':
        #         # go to first stage of add dataset
        #         h.redirect_to(controller='package', action='read', id=id)
        #     else:
        #         # add more resources
        #         h.redirect_to(controller='package', action='new_resource',
        #                       id=id)

        # get resources for sidebar
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj}
        try:
            pkg_dict = get_action('package_show')(context, {'id': id})
        except NotFound:
            base.abort(404, _('The dataset {id} could not be found.').format(id=id))
        try:
            check_access(
                'resource_create', context, {"package_id": pkg_dict["id"]})
        except NotAuthorized:
            base.abort(403, _('Unauthorized to create a resource for this package'))

        package_type = 'dataset'

        vars = {'action': 'new',
                'dataset_type': package_type}
        vars['pkg_name'] = id
        # required for nav menu
        vars['pkg_dict'] = pkg_dict
        template = 'package/new_app_not_draft.html'
        return base.render(template, extra_vars=vars)
