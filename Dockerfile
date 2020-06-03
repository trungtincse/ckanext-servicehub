#FROM trungtincse/ckan
FROM trungtincse/ckan-psql:latest
WORKDIR /project/ckanext-servicehub
COPY development.ini /etc/ckan/default/
COPY ./ ./

RUN ["chmod", "+x", "/project/ckanext-servicehub/createadmin.cmd"]

RUN cd /project/ckanext-servicehub &&\
	. /usr/lib/ckan/default/bin/activate &&\
	python setup.py develop &&\
	service postgresql start &&\
	python database.py &&\
	pip install -r dev-requirements.txt

CMD cd /usr/lib/ckan/default/src/ckan &&\
	service postgresql start &&\
	. /usr/lib/ckan/default/bin/activate &&\
	paster serve /etc/ckan/default/development.ini

EXPOSE 5000
EXPOSE 5432

