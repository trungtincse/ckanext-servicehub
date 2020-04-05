# from ckanext.servicehub.model.ServiceModel import App, Call, engine, AppParam, CallParam
from ckanext.servicehub.model.ProjectModel import Project, ProjectCategory, ProjectDatasetUsed, ProjectTag, \
    ProjectAppUsed
from ckanext.servicehub.model.BaseModel import engine

# App.__table__.drop(engine)
# Call.__table__.drop(engine)
# AppParam.__table__.drop(engine)
# CallParam.__table__.drop(engine)


# App.__table__.create(engine)
# Call.__table__.create(engine)
# AppParam.__table__.create(engine)
# CallParam.__table__.create(engine)

# Project.__table__.create(engine)
# ProjectCategory.__table__.drop(engine)
# ProjectTag.__table__.drop(engine)
ProjectCategory.__table__.create(engine)
ProjectTag.__table__.create(engine)
# ProjectDatasetUsed.__table__.drop(engine)
# ProjectAppUsed.__table__.drop(engine)
ProjectDatasetUsed.__table__.create(engine)
ProjectAppUsed.__table__.create(engine)
