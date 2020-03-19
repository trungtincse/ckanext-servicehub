from ckanext.servicehub.model.ServiceModel import App, Call, engine, AppParam, CallParam

App.__table__.drop(engine)
Call.__table__.drop(engine)
AppParam.__table__.drop(engine)
CallParam.__table__.drop(engine)


App.__table__.create(engine)
Call.__table__.create(engine)
AppParam.__table__.create(engine)
CallParam.__table__.create(engine)
