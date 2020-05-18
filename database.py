
from ckanext.servicehub.model.BaseModel import engine

from ckanext.servicehub.model.ServiceModel import App, Call, AppParam, CallInput, CallOutput, AppRelatedDataset, \
    AppCategory, AppCodeVersion

from ckanext.servicehub.model.ProjectModel import Project, ProjectCategory, ProjectTag, ProjectAppUsed, \
    ProjectDatasetUsed

#drop table: ABC.__table__.drop(engine)
#create table: ABC.__table__.create(engine)

#Application tables
App.__table__.create(engine)
Call.__table__.create(engine)
AppParam.__table__.create(engine)
AppCodeVersion.__table__.create(engine)
CallInput.__table__.create(engine)
CallOutput.__table__.create(engine)
# Project tables
AppRelatedDataset.__table__.create(engine)
AppCategory.__table__.create(engine)
Project.__table__.create(engine)
ProjectCategory.__table__.create(engine)
ProjectTag.__table__.create(engine)
ProjectAppUsed.__table__.create(engine)
ProjectDatasetUsed.__table__.create(engine)






