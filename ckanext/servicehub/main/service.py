import slug
from ckanext.servicehub.main.config_and_common import client_req, ServiceLanguage, ServiceType, simple_img_file, \
    simple_binary_file, dict_to_tuple, ParamType


def create_service_sample(service_name):
    data_dict = {'app_name': service_name,
                 'language': ServiceLanguage.PYTHON,
                 'image': slug.slug(service_name),
                 'slug_name': slug.slug(service_name),
                 'service_type': ServiceType.BATCH,
                 'description': u'Create a Service'}
    request_form = [dict(label=u'Name',type= ParamType.TEXT,var_name= u'name'),
                    dict(label=u'Count', type=ParamType.NUMBER, var_name=u'count')]
                    # dict(label=u'File',type= ParamType.FILE,var_name= u'file')]

    files = {
        'avatar': simple_img_file(),
        'codeFile': simple_binary_file()
    }
    return (dict_to_tuple(data_dict, *request_form), files)


resp = client_req('service_create', *create_service_sample(u'service_name'))
if 'error' in resp:
    print resp
    assert False
id = resp['result']['id']
print id
print client_req('service_list')
print client_req('service_show', dict(id=id))
print client_req('reqform_show', dict(app_id=id))
print client_req('service_delete', dict(id=id))
