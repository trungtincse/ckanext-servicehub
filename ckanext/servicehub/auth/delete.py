import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth
from ckan.common import _

#
# # FIXME this import is evil and should be refactored
# from ckan.logic.auth.create import _check_group_auth
#
#
# @logic.auth_allow_anonymous_access
# def package_update(context, data_dict):
#     user = context.get('user')
#     package = logic_auth.get_package_object(context, data_dict)
#     if package.owner_org:
#         # if there is an owner org then we must have update_dataset
#         # permission for that organization
#         check1 = authz.has_user_permission_for_group_or_org(
#             package.owner_org, user, 'update_dataset'
#         )
#     else:
#         # If dataset is not owned then we can edit if config permissions allow
#         if authz.auth_is_anon_user(context):
#             check1 = all(authz.check_config_permission(p) for p in (
#                 'anon_create_dataset',
#                 'create_dataset_if_not_in_organization',
#                 'create_unowned_dataset',
#                 ))
#         else:
#             check1 = all(authz.check_config_permission(p) for p in (
#                 'create_dataset_if_not_in_organization',
#                 'create_unowned_dataset',
#                 )) or authz.has_user_permission_for_some_org(
#                 user, 'create_dataset')
#     if not check1:
#         return {'success': False,
#                 'msg': _('User %s not authorized to edit package %s') %
#                         (str(user), package.id)}
#     else:
#         check2 = _check_group_auth(context, data_dict)
#         if not check2:
#             return {'success': False,
#                     'msg': _('User %s not authorized to edit these groups') %
#                             (str(user))}
#
#     return {'success': True}
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
    if authz.has_user_permission_for_group_or_org( app.organization,user, 'delete_service') and app.owner == user or authz.is_sysadmin(user):
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User %s not have permission to delete application') % user}
