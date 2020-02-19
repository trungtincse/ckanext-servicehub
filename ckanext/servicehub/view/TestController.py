import paste.fileapp
from flask import Blueprint, send_from_directory, send_file

from ckan.common import OrderedDict, _, json, request, c, response
from ckan.logic import clean_dict, parse_params, tuplize_dict
import ckan.lib.navl.dictization_functions as dict_fns

test_blueprint = Blueprint('test', __name__, url_prefix=u'/test')


@test_blueprint.route('/empty', methods=['GET'])
def empty():
    # data_dict = clean_dict(
    #     dict_fns.unflatten(tuplize_dict(parse_params(request.files))))
    # data_dict = clean_dict(
    #     dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
    # print data_dict
    print "asds"
    return send_file("/home/tindang/Downloads/code.zip",as_attachment=True)
