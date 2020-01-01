from flask import Blueprint

from ckan.common import request
from ckan.logic import clean_dict, parse_params, tuplize_dict
import ckan.lib.navl.dictization_functions as dict_fns

test_blueprint=Blueprint('test',__name__, url_prefix=u'/test')
@test_blueprint.route('/empty',methods=['POST'])
def empty():
    print "Hello"
    data_dict = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.files))))
    data_dict = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
    print data_dict
