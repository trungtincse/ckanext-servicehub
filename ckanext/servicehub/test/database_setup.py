from ckan.model.user import User
from ckan.model import meta
from ckan.model import types as _types
from sqlalchemy import orm, types, Column, Table, ForeignKey, or_, and_, text, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('postgresql://ckan_default:ckan_default@localhost/ckan_default')
Session = sessionmaker(bind=engine)
session = Session()


class Service(Base):
    __tablename__ = 'service'

    id = Column(types.UnicodeText,
                primary_key=True,
                default=_types.make_uuid)
    name = Column(types.UnicodeText)
    owner = Column(types.UnicodeText, ForeignKey(User.name))
    description = Column(types.UnicodeText)
    pod_json = Column(_types.JsonDictType)
    service_json = Column(_types.JsonDictType)
    api_json = Column(_types.JsonDictType)

    def __init__(self, name, owner, description, pod_json, service_json, api_json):
        self.name = name
        self.owner = owner
        self.pod_json = pod_json
        self.service_json = service_json
        self.description = description
        self.api_json = api_json

    def __str__(self):
        return 'Name: {}\tOwner: {}'.format(self.name, self.owner)


Base.metadata.create_all(engine)
