import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth
from ckan.common import _
def is_admin(context, data_dict):
    user = context['user']
    session = context['session']
    if authz.is_sysadmin(user):
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User %s is not admin') % user}
