from ckanext.servicehub.model.ServiceModel import App, Call, engine

# App.__table__.drop(engine)
# Call.__table__.drop(engine)
App.__table__.create(engine)
Call.__table__.create(engine)
