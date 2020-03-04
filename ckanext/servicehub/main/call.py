from ckanext.servicehub.main.config_and_common import client_req, ParamType, create_input


def create_call_sample(app_id):
    # --------------CREATE_SAMPLE_HERE-------------------
    #NOT NEED CREATE ANYTHING
    #----------------------------------------------------
    resp = client_req('reqform_show', dict(app_id=app_id))
    if 'error' in resp:
        print resp
        assert False
    fields=resp.get('result', {}).get('fields', None)
    data=[('app_id',app_id)]
    files=[]
    for field in fields:
        if field['type']==ParamType.FILE:
            files.append((field['var_name'],create_input(field['type'])))
        else:
            data.append((field['var_name'],create_input(field['type'])))
    return (data,files)

########### main ############
app_id=u'c155f970-d377-41c0-87ff-f45dcdcabad0'
resp = client_req('call_create', *create_call_sample(app_id))
if 'error' in resp:
    print resp
    assert False
id = resp['result']['id']
print client_req('call_list')
print client_req('call_show', dict(id=id))
print client_req('input_show', dict(call_id=id))
print client_req('call_delete', dict(call_id=id))
