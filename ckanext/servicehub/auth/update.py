import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth
from ckan.common import _
from ckanext.servicehub.model.ServiceModel import App


def update_service(context, data_dict):
    user = context['user']
    app_id = data_dict['app_id']
    session = context['session']
    app = session.query(App).filter(app_id == app_id).first()
    if app == None:
        return {'success': False,
                'msg': _('Application not found')}
    if authz.has_user_permission_for_group_or_org(user, 'update_service',app.organization) and app.owner == user:
        return {'success': True}
    else :
        return {'success': False,
                'msg': _('User %s not has permission to update application')%user}
