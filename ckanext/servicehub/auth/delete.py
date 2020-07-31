import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth
from ckan.common import _
from ckanext.servicehub.model.ServiceModel import App


def delete_service(context, data_dict):
    """
    owner + ng co quyen delete_service
    admin
    """
    user = context['user']
    app_id = data_dict['app_id']
    # for_display = data_dict.get('for_display',False)
    session = context['session']
    app = session.query(App).filter(App.app_id == app_id).first()
    if app == None:
        return {'success': False,
                'msg': _('Application not found')}
    if authz.has_user_permission_for_group_or_org( app.organization,user, 'delete_service') and app.owner == user  or authz.is_sysadmin(user):
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User %s not have permission to delete application') % user}
