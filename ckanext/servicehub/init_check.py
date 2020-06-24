import logging

import requests

from ckan.common import config

logger = logging.getLogger('local')

def check_appserver_opening():
    appserver_host = config.get('ckan.servicehub.appserver_host')
    try:
        requests.get(appserver_host + '/ping')
        logger.info('Connect to ckan app server successfully')
    except:
        log = 'Failed to connect to ckan app server at %s' % appserver_host
        logger.error(log)
        raise Exception(log)


def check_solr_instances_running():
    check_solr_opening(config.get('ckan.servicehub.app_solr_url'))
    check_solr_opening(config.get('ckan.servicehub.prj_solr_url'))


def check_solr_opening(url):
    try:
        requests.get(url + '/admin/ping')
    except:
        raise Exception('Solr is not running: instance url: ' + url)