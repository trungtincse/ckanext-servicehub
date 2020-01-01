from ckanext.servicehub.model.ServiceModel import Call

from ckan import logic
from flask import Blueprint
import ckan.lib.base as base
import ckan.model as model
from ckan.common import g
from ckan.views.user import _extra_template_variables
import ckan.lib.helpers as h
get_action = logic.get_action
user_blueprint=Blueprint(u'service_user', __name__, url_prefix=u'/service/user')
@user_blueprint.route('/<user>')
def user_service_request(user):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj
    }
    data_dict = {
        u'user': user,
        u'user_obj': g.userobj,
        u'include_datasets': True,
        u'include_num_followers': True
    }
    session=context['session']
    # user=context['user']
    instances=session.query(Call).filter(Call.call_user==user)

    extra_vars = _extra_template_variables(context, data_dict)
    extra_vars["instances"]=instances
    print instances
    if extra_vars is None:
        return h.redirect_to(u'user.login')
    return base.render('user/service_requests_read.html',extra_vars)

