import requests
import json

def service_handle(context,data_dict):
    rs=requests.get('http://192.168.1.102:8001/api/v1/namespaces/default/services/'+data_dict['url_part'])
    print data_dict['url_part']
    return rs.text;
