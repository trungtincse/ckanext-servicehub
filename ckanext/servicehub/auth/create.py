import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth

from ckan.common import _
def service_create(context, data_dict=None):
    user = context['user']
    user = authz.get_user_id_for_username(user, allow_none=True)

    if user and authz.check_config_permission('user_create_services'):
        return {'success': True}
    return {'success': False,
            'msg': _('User %s not authorized to create services') % user}