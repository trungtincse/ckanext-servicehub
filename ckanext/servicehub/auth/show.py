from sphinx.locale import _

from ckan.lib.plugins import get_permission_labels
from ckan.logic.auth import get_package_object


def package_show(context, data_dict):
    user = context.get('user')
    package = get_package_object(context, data_dict)
    labels = get_permission_labels()
    ###
    extras= package.as_dict().get('extras',[])
    output_owner=extras.get('user','')
    ###
    user_labels = labels.get_user_dataset_labels(context['auth_user_obj'])
    authorized = any(
        dl in user_labels for dl in labels.get_dataset_labels(package))
    ###
    authorized=any([authorized,output_owner==user])
    ###
    if not authorized:
        return {
            'success': False,
            'msg': _('User %s not authorized to read package %s') % (user, package.id)}
    else:
        return {'success': True}
