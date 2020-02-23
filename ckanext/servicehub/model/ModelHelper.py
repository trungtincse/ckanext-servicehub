from ckanext.servicehub.model.ServiceModel import  Call, App


def deleteAppARelevant(session,app_id):
    # session.query(AppPort).filter(AppPort.app_id == app_id).delete()
    # session.query(Call).filter(Call.app_id == app_id).delete()
    session.query(App).filter(App.app_id == app_id).delete()
    session.commit()
