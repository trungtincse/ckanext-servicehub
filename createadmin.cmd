#! /bin/bash
. /usr/lib/ckan/default/bin/activate &&\
cd /usr/lib/ckan/default/src/ckan &&\
paster sysadmin add seanh password=12345678 email=tin@g.g  -c /etc/ckan/default/development.ini
