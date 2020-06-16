import logging

import requests

from ckan.common import config

logger = logging.getLogger('ckan.ckanapp')


def check_appserver_opening():
    appserver_host = config.get('ckan.servicehub.appserver_host')
    try:
        requests.get(appserver_host + '/ping')
        logger.info('Connect to ckan app server successfully')
    except:
        log = 'Failed to connect to ckan app server at %s' % appserver_host
        logger.error(log)
        raise Exception(log)