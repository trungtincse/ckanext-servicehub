import json

from flask import Blueprint
from ckan.common import g, request
from ckanext.servicehub.model.ServiceModel import *

appserver_blueprint = Blueprint('appserver', __name__, url_prefix='/notify')


@appserver_blueprint.route('/server/<id>', methods=["POST"])
def notify_server(id):
    # print request.data
    result = {"error": ""}
    return json.dump(result)


@appserver_blueprint.route('/batch/<id>', methods=["POST"])
def notify_batch(id):
    result = {"error": ""}
    return json.dump(result)
