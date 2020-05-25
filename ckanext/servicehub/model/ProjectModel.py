import json
from datetime import datetime

from ckan import model
from ckan.common import config
from ckan.model import meta, tag_table, package_table
from ckan.model import types as _types
from sqlalchemy import orm, types, Column, Table, ForeignKey, or_, and_, text, Integer, String, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from ckan.model.user import User
import ckan.plugins.toolkit as tk
# Session = sessionmaker(bind=engine)
from ckanext.servicehub.model.BaseModel import Base


class Project(Base):
    __tablename__ = 'project'
    id = Column(types.UnicodeText,
                primary_key=True,
                default=_types.make_uuid)
    name = Column(types.UnicodeText)
    email = Column(types.UnicodeText)
    organization_name = Column(types.UnicodeText)
    o_description = Column(types.UnicodeText)
    o_avatar_image = Column(types.UnicodeText)
    project_name = Column(types.UnicodeText)
    header_image = Column(types.UnicodeText)
    prj_summary = Column(types.UnicodeText)
    prj_goal = Column(types.UnicodeText)
    draft = Column(types.Boolean)
    active = Column(types.Boolean)

    def __init__(self):
        self.id = _types.make_uuid()
        self.active = False

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self):
        _dict = {c.key: getattr(self, c.key)
                 for c in inspect(self).mapper.column_attrs}
        return _dict


class ProjectCategory(Base):
    __tablename__ = 'project_category'
    id = Column(types.UnicodeText,
                primary_key=True,
                default=_types.make_uuid)
    project_id = Column(types.UnicodeText, ForeignKey('project.id', onupdate="CASCADE", ondelete="CASCADE"))
    # tag_id=Column(types.UnicodeText,ForeignKey(tag_table.columns["id"], onupdate="CASCADE", ondelete="CASCADE"))
    tag_name = Column(types.UnicodeText)

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class ProjectTag(Base):
    __tablename__ = 'project_tag'
    id = Column(types.UnicodeText,
                primary_key=True,
                default=_types.make_uuid)
    project_id = Column(types.UnicodeText, ForeignKey('project.id', onupdate="CASCADE", ondelete="CASCADE"))
    # tag_id=Column(types.UnicodeText,ForeignKey(tag_table.columns["id"], onupdate="CASCADE", ondelete="CASCADE"))
    tag_name = Column(types.UnicodeText)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self):
        _dict = {c.key: getattr(self, c.key)
                 for c in inspect(self).mapper.column_attrs}
        return _dict


class ProjectDatasetUsed(Base):
    __tablename__ = 'project_dataset_used'
    id = Column(types.UnicodeText,
                primary_key=True,
                default=_types.make_uuid)
    project_id = Column(types.UnicodeText, ForeignKey('project.id', onupdate="CASCADE", ondelete="CASCADE"))
    dataset_id = Column(types.UnicodeText,
                        ForeignKey(package_table.columns['id'], onupdate="CASCADE", ondelete="CASCADE"))
    link = Column(types.UnicodeText)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self):
        _dict = {c.key: getattr(self, c.key)
                 for c in inspect(self).mapper.column_attrs}
        # _dict['dataset_id']=[i.as_dict() for i in meta.Session.query(ProjectDatasetUsed).filter(ProjectDatasetUsed.project_id==self.id).all()]
        _dict['dataset_id']=model.Package.get(self.dataset_id).name
        return _dict


class ProjectAppUsed(Base):
    __tablename__ = 'project_app_used'
    id = Column(types.UnicodeText,
                primary_key=True,
                default=_types.make_uuid)
    app_id = Column(types.UnicodeText)
    project_id = Column(types.UnicodeText, ForeignKey('project.id', onupdate="CASCADE", ondelete="CASCADE"))
    link = Column(types.UnicodeText)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self):
        _dict = {c.key: getattr(self, c.key)
                 for c in inspect(self).mapper.column_attrs}
        return _dict

from ckanext.servicehub.model.BaseModel import Base, engine
Base.metadata.create_all(engine)
