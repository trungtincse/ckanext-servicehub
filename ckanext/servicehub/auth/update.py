import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth
from ckan.common import _
from ckanext.servicehub.model.ServiceModel import App


def update_service(context, data_dict):
    """
    STOP,START: admin
    DEBUG: owner, admin
    """
    user = context['user']
    app_id = data_dict['app_id']
    session = context['session']
    app = session.query(App).filter(App.app_id == app_id).first()
    if app == None:
        return {'success': False,
                'msg': _('Application not found')}
    if authz.is_sysadmin(user):
        return {'success': True}
    if authz.has_user_permission_for_group_or_org(app.organization,user, 'update_service') and app.owner == user and app.app_status=='DEBUG':
        return {'success': True}
    return {'success': False,
            'msg': _('User %s not has permission to update application')%user}
