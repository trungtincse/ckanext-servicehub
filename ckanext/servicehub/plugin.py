import logging

from ckanext.servicehub.action import app_solr_action
from ckanext.servicehub.view import ServiceController, CallController, \
    PackageController, ProjectController,AdminController
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.servicehub.auth.create as create_auth
import ckanext.servicehub.auth.update as update_auth
import ckanext.servicehub.auth.delete as delete_auth
import ckanext.servicehub.auth.admin as admin_auth
import ckanext.servicehub.auth.show as show_auth
import ckanext.servicehub.action.create as create
import ckanext.servicehub.action.show as show
import ckanext.servicehub.action.delete as delete


class ServicehubPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IDatasetForm)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'servicehub')

    def get_blueprint(self):
        return [ServiceController.service,
                AdminController.app_admin_blueprint,
                AdminController.prj_admin_blueprint,
                CallController.call_blueprint,
                PackageController.package_blueprint,
                ProjectController.project_blueprint,
                ]

    def get_auth_functions(self):
        return {'service_create': create_auth.service_create,
                'call_create': create_auth.call_create,
                'update_service': update_auth.update_service,
                'delete_service': delete_auth.delete_service,
                'service_show':show_auth.service_show,
                'service_monitor':show_auth.service_monitor,
                'is_admin':admin_auth.is_admin,
                }

    def get_actions(self):
        all_function = dict()
        all_function.update(show.public_functions)
        all_function.update(create.public_functions)
        all_function.update(delete.public_functions)
        all_function.update(app_solr_action.public_functions)
        return all_function

    def create_package_schema(self):
        # let's grab the default schema in our plugin
        schema = super(ServicehubPlugin, self).create_package_schema()
        # our custom field
        schema['owner_org'] = [toolkit.get_validator(u'ignore_missing')]
        schema['private'] = [toolkit.get_validator(u'ignore_missing'), toolkit.get_validator(u'boolean_validator')]
        return schema

    def update_package_schema(self):
        # let's grab the default schema in our plugin
        schema = super(ServicehubPlugin, self).update_package_schema()
        # our custom field
        schema['owner_org'] = [toolkit.get_validator(u'ignore_missing')]
        schema['private'] = [toolkit.get_validator(u'ignore_missing'), toolkit.get_validator(u'boolean_validator')]
        return schema

    def package_types(self):
        return [u'output']

    def is_fallback(self):
        return False

    def show_package_schema(self):
        # let's grab the default schema in our plugin
        schema = super(ServicehubPlugin, self).show_package_schema()
        # our custom field
        schema['owner_org'] = [toolkit.get_validator(u'ignore_missing')]
        return schema
# logger= logging.getLogger('ckanapp')
# logger.info("id=125&info=Tindang")
