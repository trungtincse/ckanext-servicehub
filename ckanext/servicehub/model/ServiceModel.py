import json
from datetime import datetime

from ckan.common import config
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
# Session = sessionmaker(bind=engine)


class Call(Base):
    __tablename__ = 'app_call'

    call_id = Column(types.UnicodeText,
                     primary_key=True,
                     default=_types.make_uuid)
    call_user = Column(types.UnicodeText)
    app_id = Column(types.UnicodeText, ForeignKey('app_info.app_id'))
    container_id = Column(types.UnicodeText)
    status = Column(types.UnicodeText)
    create_at = Column(types.UnicodeText)  # optional both

    def __init__(self, call_user, app_id,container_id=None, status="PENDING"):
        self.call_id = _types.make_uuid()
        self.call_user = call_user
        self.app_id = app_id
        self.status = status
        self.container_id = container_id
        self.create_at=datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    def setOption(self,**kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

class App(Base):
    __tablename__ = 'app_info'

    app_id = Column(types.UnicodeText,
                    primary_key=True,
                    default=_types.make_uuid)
    app_name = Column(types.UnicodeText)
    ava_url = Column(types.UnicodeText)
    type = Column(types.UnicodeText)
    slug_name = Column(types.UnicodeText,unique=True)
    image = Column(types.UnicodeText)
    owner = Column(types.UnicodeText)
    description = Column(types.UnicodeText)
    s_port = Column(types.UnicodeText)  # optional server
    d_port = Column(types.UnicodeText,unique=True)  # optional server
    language = Column(types.UnicodeText)  # optional batch
    code_url = Column(types.UnicodeText)  # optional batch
    status = Column(types.UnicodeText)  # optional both
    create_at = Column(types.UnicodeText)  # optional both

    def __init__(self, app_name, type, slug_name, image, owner, description, status="PENDING"):
        self.app_id = _types.make_uuid()
        self.app_name = app_name
        self.type = type
        self.slug_name = slug_name
        self.image = image
        self.status = status
        self.description = description
        self.owner = owner
        self.app_id = _types.make_uuid()
        self.create_at = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    def setOption(self,**kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)


