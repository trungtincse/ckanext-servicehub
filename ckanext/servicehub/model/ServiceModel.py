from ckan.model import meta
from ckan.model import types as _types
from sqlalchemy import orm, types, Column, Table, ForeignKey, or_, and_, text, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from ckan.model.user import User
import ckan.plugins.toolkit as tk

Base = declarative_base()
engine = create_engine(
    tk.config.get('sqlalchemy.url') or "postgresql://ckan_default:ckan_default@localhost/ckan_default")
Session = sessionmaker(bind=engine)


class Call(Base):
    __tablename__ = 'app_call'

    call_id = Column(types.UnicodeText,
                     primary_key=True,
                     default=_types.make_uuid)
    call_user = Column(types.UnicodeText)
    app_id = Column(types.UnicodeText)
    container_id = Column(types.UnicodeText)
    status = Column(types.UnicodeText)
    duration = Column(types.BIGINT)
    stdout = Column(types.UnicodeText)
    stderr = Column(types.UnicodeText)

    def __init__(self, call_user, app_id,status):
        self.call_user = call_user
        self.app_id = app_id
        self.call_id=_types.make_uuid()
        self.status=status

    @classmethod
    def get(cls, reference):
        '''Returns a group object referenced by its id or name.'''
        session = Session()
        if not reference:
            return None

        member = session.query(cls).get(reference)
        if member is None:
            member = cls.by_name(reference)
        return member

    @classmethod
    def by_name(cls, name, autoflush=True):
        session = Session()
        obj = session.query(cls).autoflush(autoflush) \
            .filter_by(name=name).first()
        return obj


class App(Base):
    __tablename__ = 'app_info'

    app_id = Column(types.UnicodeText,
                    primary_key=True,
                    default=_types.make_uuid)
    app_name = Column(types.UnicodeText)
    type = Column(types.UnicodeText)
    slug_name = Column(types.UnicodeText)
    image = Column(types.UnicodeText)
    owner = Column(types.UnicodeText)
    description = Column(types.UnicodeText)
    port2port = Column(types.UnicodeText)  # optional
    language = Column(types.UnicodeText)  # optional
    json_input = Column(types.Boolean)  # optional
    binary_input = Column(types.Boolean)  # optional
    status = Column(types.UnicodeText)  # optional

    def __init__(self, app_name, type, slug_name, image,description,owner,language, port2port=None, json_input=None,
                 binary_input=None, status=None):
        self.app_name = app_name
        self.type = type
        self.slug_name = slug_name
        self.image = image
        self.port2port = port2port
        self.language = language
        self.json_input = json_input
        self.binary_input = binary_input
        self.status = status
        self.description=description
        self.owner=owner
        self.app_id=_types.make_uuid()
    @classmethod
    def get(cls, reference):
        '''Returns a group object referenced by its id or name.'''
        session = Session()
        if not reference:
            return None

        member = session.query(cls).get(reference)
        if member is None:
            member = cls.by_name(reference)
        return member

    @classmethod
    def by_name(cls, name, autoflush=True):
        session = Session()
        obj = session.query(cls).autoflush(autoflush) \
            .filter_by(app_id=name).first()
        return obj
class AppPort(Base):
    __tablename__ = 'app_port'

    id = Column(types.UnicodeText,
                    primary_key=True,
                    default=_types.make_uuid)
    app_id = Column(types.UnicodeText)
    port = Column(types.UnicodeText)

    def __init__(self,app_id,port):
        self.id=_types.make_uuid()
        self.app_id=app_id
        self.port=port
    @classmethod
    def get(cls, reference):
        '''Returns a group object referenced by its id or name.'''
        session = Session()
        if not reference:
            return None

        member = session.query(cls).get(reference)
        if member is None:
            member = cls.by_name(reference)
        return member

    @classmethod
    def by_name(cls, name, autoflush=True):
        session = Session()
        obj = session.query(cls).autoflush(autoflush) \
            .filter_by(name=name).first()
        return obj

