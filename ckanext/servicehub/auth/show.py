import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth
from ckan.common import _
from ckanext.servicehub.model.ServiceModel import App
from ckanext.servicehub.model.ProjectModel import Project


def list_all_services_of_user(context, data_dict=None):
    session = context['session']
    user = context['user']
    app_list = session.query(App).all()
    if authz.is_sysadmin(user):
        return list(map(lambda app: app.app_id, app_list))
    filter_iterator = filter(lambda app: app.app_status == 'START' or
                                         (authz.has_user_permission_for_group_or_org(app.organization, user,
                                                                                     'run_service_staging')
                                          and app.app_status == 'DEBUG'), app_list)
    return list(map(lambda app: app.app_id, filter_iterator))
def list_all_prọects_of_user(context, data_dict=None):
    session = context['session']
    user = context['user']
    prj_list = session.query(Project).all()
    if authz.is_sysadmin(user):
        return list(map(lambda prj: prj.id, prj_list))
    filter_iterator = filter(lambda prj: prj.active, prj_list)
    return list(map(lambda prj: prj.id, filter_iterator))

def service_show(context, data_dict=None):
    """
    mode START: ai cung thay
    mode DEBUG: nhung nguoi co quyen run_service_staging cua 1 to chuc hoac admin
    mode STOP: admin
    """
    session = context['session']
    user = context['user']
    app_id = data_dict['app_id']
    if app_id in list_all_services_of_user(context):
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User %s not have permission to read page') % user}

def service_monitor(context, data_dict=None):
    """
    owner
    admin
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
    if authz.has_user_permission_for_group_or_org(app.organization,user, 'update_service') and app.owner == user:
        return {'success': True}
    else :
        return {'success': False,
                'msg': _('User %s not has permission to update application')%user}