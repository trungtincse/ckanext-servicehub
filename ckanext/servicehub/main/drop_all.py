
from ckanext.servicehub.model.BaseModel import engine

from ckanext.servicehub.model.ServiceModel import App, Call, AppParam, CallInput, CallOutput, AppRelatedDataset, \
    AppCategory, AppCodeVersion

from ckanext.servicehub.model.ProjectModel import Project, ProjectCategory, ProjectTag, ProjectAppUsed, \
    ProjectDatasetUsed

#drop table: ABC.__table__.drop(engine)
#create table: ABC.__table__.create(engine)

#Application tables
App.__table__.drop(engine)
Call.__table__.drop(engine)
AppParam.__table__.drop(engine)
AppCodeVersion.__table__.drop(engine)
CallInput.__table__.drop(engine)
CallOutput.__table__.drop(engine)
# Project tables
AppRelatedDataset.__table__.drop(engine)
AppCategory.__table__.drop(engine)
Project.__table__.drop(engine)
ProjectCategory.__table__.drop(engine)
ProjectTag.__table__.drop(engine)
ProjectAppUsed.__table__.drop(engine)
ProjectDatasetUsed.__table__.drop(engine)
