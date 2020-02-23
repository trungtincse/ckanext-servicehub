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
    input_id = Column(types.UnicodeText)
    output_id = Column(types.UnicodeText)

    def __init__(self, call_user, app_id,container_id=None, status="PENDING",input_id=None,output_id=None):
        self.call_id = _types.make_uuid()
        self.call_user = call_user
        self.app_id = app_id
        self.status = status
        self.container_id = container_id
        self.input_id=input_id
        self.output_id=output_id


class App(Base):
    __tablename__ = 'app_info'

    app_id = Column(types.UnicodeText,
                    primary_key=True,
                    default=_types.make_uuid)
    app_name = Column(types.UnicodeText)
    type = Column(types.UnicodeText)
    slug_name = Column(types.UnicodeText,unique=True)
    image = Column(types.UnicodeText)
    owner = Column(types.UnicodeText)
    description = Column(types.UnicodeText)
    s_port = Column(types.UnicodeText)  # optional server
    d_port = Column(types.UnicodeText,unique=True)  # optional server
    language = Column(types.UnicodeText)  # optional batch
    status = Column(types.UnicodeText)  # optional both

    def __init__(self, app_name, type, slug_name, image, owner, description,
                 s_port=None,d_port=None,language=None , status="PENDING"):
        self.app_id = _types.make_uuid()
        self.app_name = app_name
        self.type = type
        self.slug_name = slug_name
        self.image = image
        self.s_port = s_port
        self.d_port = d_port
        self.language = language
        self.status = status
        self.description = description
        self.owner = owner
        self.app_id = _types.make_uuid()



# main-zone
def main():
    # App.__table__.create(engine)
    # Call.__table__.create(engine)
    pass
