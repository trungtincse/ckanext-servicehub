
from ckanext.servicehub.model.BaseModel import engine

from ckanext.servicehub.model.ServiceModel import App, Call, AppParam, CallInput, CallOutput, AppRelatedDataset, \
    AppCategory

from ckanext.servicehub.model.ProjectModel import Project, ProjectCategory, ProjectTag, ProjectAppUsed, \
    ProjectDatasetUsed


# App.__table__.drop(engine)
# Call.__table__.drop(engine)
# AppParam.__table__.drop(engine)
# CallInput.__table__.drop(engine)
# CallOutput.__table__.drop(engine)
# AppRelatedDataset.__table__.drop(engine)
# AppCategory.__table__.drop(engine)
# Project.__table__.drop(engine)
# ProjectCategory.__table__.drop(engine)
# ProjectTag.__table__.drop(engine)
# ProjectAppUsed.__table__.drop(engine)
# ProjectDatasetUsed.__table__.drop(engine)

# App.__table__.create(engine)
# Call.__table__.create(engine)
# AppParam.__table__.create(engine)
# CallInput.__table__.create(engine)
# CallOutput.__table__.create(engine)
AppRelatedDataset.__table__.create(engine)
AppCategory.__table__.create(engine)
Project.__table__.create(engine)
ProjectCategory.__table__.create(engine)
ProjectTag.__table__.create(engine)
ProjectAppUsed.__table__.create(engine)
ProjectDatasetUsed.__table__.create(engine)






