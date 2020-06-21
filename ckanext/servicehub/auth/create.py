import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth
from ckanext.servicehub.model.ServiceModel import App, Call
from ckan.common import _
from sqlalchemy import and_


def service_create(context, data_dict=None):
    """
    nguoi co quyen create_service cua 1 to chuc hoac admin
    """
    user = context['user']

    for_display = data_dict.get('for_display', False)
    if for_display and authz.has_user_permission_for_some_org(user, 'create_service'):
        return {'success': True}
    if not for_display:
        if data_dict == None or 'org_name' not in data_dict:
            return {'success': False,
                    'msg': _('Organization information not found')}
        if authz.has_user_permission_for_group_or_org(data_dict['org_name'], user, 'create_service'):
            return {'success': True}
    return {'success': False,
            'msg': _('User %s not authorized to create application') % user}


def resource_create(context, data_dict):
    model = context['model']
    user = context.get('user')

    package_id = data_dict.get('package_id')
    if not package_id and data_dict.get('id'):
        # This can happen when auth is deferred, eg from `resource_view_create`
        resource = logic_auth.get_resource_object(context, data_dict)
        package_id = resource.package_id

    if not package_id:
        raise logic.NotFound(
            _('No dataset id provided, cannot check auth.')
        )

    # check authentication against package
    pkg = model.Package.get(package_id)
    if not pkg:
        raise logic.NotFound(
            _('No package found for this resource, cannot check auth.')
        )

    pkg_dict = {'id': pkg.id}
    authorized = authz.is_authorized('package_update', context, pkg_dict).get('success')

    if not authorized:
        return {'success': False,
                'msg': _('User %s not authorized to create resources on dataset %s') %
                       (str(user), package_id)}
    else:
        return {'success': True}


def call_create(context, data_dict):
    """
    khi app START: ai cung co the goi
    khi app DEBUG: ai co quyen run_service_staging
    khi app STOP: admin
    """
    user = context['user']
    app_id = data_dict['app_id']
    session = context['session']
    app = session.query(App).filter(App.app_id == app_id).first()
    if app == None:
        return {'success': False,
                'msg': _('Application not found')}
    if app.app_status == 'START':
        return {'success': True}
    if app.app_status == 'DEBUG':
        if authz.has_user_permission_for_group_or_org(app.organization, user, 'run_service_staging'):
            return {'success': True}
        else:
            return {'success': False,
                    'msg': _('User %s not have permission to create request') % user}
    if app.app_status == 'STOP':
        return {'success': False,
                'msg': _('Application %s is not available') % app.app_name}


def report_create(context, data_dict):
    session = context['session']
    user = context['user']
    app_id = data_dict['app_id']
    # call_id=data_dict['call_id']
    app_ins = session.query(App).filter(and_(App.app_status == 'DEBUG' , App.app_id == app_id)).first()
    if app_ins == None:
        return {'success': False,
                'msg': _('Can not create report')}
    has_permission = authz.has_user_permission_for_group_or_org(app_ins.organization, user, 'run_service_staging')
    if has_permission:
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User %s not have permission to create report') % user}
