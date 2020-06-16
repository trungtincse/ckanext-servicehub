import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth
from ckan.common import _
from ckanext.servicehub.model.ServiceModel import App


def list_all_service_of_user(context, data_dict=None):
    session = context['session']
    user = context['user']
    app_list = session.query(App).all()
    filter_iterator = filter(lambda app: app.app_status == 'START' or
                                         (authz.has_user_permission_for_group_or_org(app.organization, user,
                                                                                     'run_service_staging')
                                          and app.app_status == 'DEBUG'), app_list)
    return list(map(lambda app: app.app_id, filter_iterator))


def service_show(context, data_dict=None):
    session = context['session']
    user = context['user']
    app_id = data_dict['app_id']
    if app_id in list_all_service_of_user(context):
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User %s not have permission to read page') % user}
