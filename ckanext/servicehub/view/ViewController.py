import os

import paste.fileapp
from flask import Blueprint, send_from_directory, send_file, jsonify

from ckan.common import OrderedDict, _, json, request, c, response
from ckan.logic import clean_dict, parse_params, tuplize_dict
import ckan.lib.navl.dictization_functions as dict_fns

view_blueprint = Blueprint('file', __name__, url_prefix=u'/view')


@view_blueprint.route('<resource_io_view_id>', methods=['GET'])
def view(resource_io_view_id):
    return send_file(os.path.join("/home/tindang/ckan",file_name),as_attachment=True)
