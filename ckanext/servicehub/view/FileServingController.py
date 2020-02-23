import os

import paste.fileapp
from flask import Blueprint, send_from_directory, send_file, jsonify

from ckan.common import OrderedDict, _, json, request, c, response
from ckan.logic import clean_dict, parse_params, tuplize_dict
import ckan.lib.navl.dictization_functions as dict_fns

file_blueprint = Blueprint('file', __name__, url_prefix=u'/file')


@file_blueprint.route('/upload', methods=['POST'])
def upload():
    try:
        request.files["file"].save(os.path.join("/home/tindang/ckan", "code.zip"))
    except:
         raise
    data= {"error":""}
    return jsonify(data), 200

@file_blueprint.route('/view/<app_id>/<file_name>', methods=['GET'])
def view(app_id,file_name):
    print "view"
    return send_file(os.path.join("/home/tindang/ckan",file_name),as_attachment=True)
