from ckanext.servicehub.view import ServiceController, CallController, UserController, TestController, AppServer, \
    FileServingController

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.servicehub.auth.create as create_auth
import ckanext.servicehub.action.create as create
import ckanext.servicehub.action.read as read


class ServicehubPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    # plugins.implements(plugins.IMiddleware)
    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'servicehub')

    def get_blueprint(self):
        return [ServiceController.service,
                CallController.call_blueprint,
                UserController.user_blueprint,
                TestController.test_blueprint,
                AppServer.appserver_blueprint,
                FileServingController.file_blueprint
                ]

    def get_auth_functions(self):
        return {'service_create': create_auth.service_create}

    def get_actions(self):
        return {'service_create': create.service_create,
                'call_create': create.call_create,
                'service_list': read.service_list,
                'service_show': read.service_show,
                'call_show': read.call_show,
                'service_req_form_show': read.service_req_form_show,
                'call_list': read.call_list
                }

    # def make_middleware(self, app, config):
    #     from ckan.config.middleware.flask_app import CKANFlask
    #     if isinstance(app,CKANFlask):
    #         app.config["REDIS_URL"] = "redis://localhost"
