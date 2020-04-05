from ckanext.servicehub.view import ServiceController, CallController, TestController,\
    ViewController, PackageController, ProjectController
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.servicehub.auth.create as create_auth
import ckanext.servicehub.action.create as create
import ckanext.servicehub.action.read as read
import ckanext.servicehub.action.delete as delete


class ServicehubPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    # plugins.implements(plugins.IMiddleware,inherit=True)
    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'servicehub')

    def get_blueprint(self):
        return [ServiceController.service,
                CallController.call_blueprint,
                TestController.test_blueprint,
                # AppServer.appserver_blueprint,
                ViewController.view_blueprint,
                PackageController.package_blueprint,
                ProjectController.project_blueprint
                ]

    def get_auth_functions(self):
        return {'service_create': create_auth.service_create}

    def get_actions(self):
        all_function = dict()
        all_function.update(read.public_functions)
        all_function.update(create.public_functions)
        all_function.update(delete.public_functions)
        return all_function

    # def make_middleware(self, app, config):
    #     if isinstance(app, CKANFlask):
    #         app.config['SECRET_KEY'] = 'secret!'
    #         # global socket
    #         socket = SocketIO(app)
    #     return app
