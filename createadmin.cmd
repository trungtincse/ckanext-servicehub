#! /bin/bash
. /usr/lib/ckan/default/bin/activate &&\
cd /usr/lib/ckan/default/src/ckan &&\
paster sysadmin add seanh password=12345678 email=tin@g.g apikey=aee93875-75c7-481a-aa11-27c9bb72a2bf -c /etc/ckan/default/development.ini
