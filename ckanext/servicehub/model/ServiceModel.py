import json
from datetime import datetime
import os
import pytz

from ckan import model
from ckan.common import config
from ckan.model import meta, package_table, domain_object
from ckan.model import types as _types
from sqlalchemy import orm, types, Column, Table, ForeignKey, or_, and_, text, Integer, String, inspect, DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from ckan.model.user import User
import ckan.plugins.toolkit as tk
# Session = sessionmaker(bind=engine)
from ckanext.servicehub.model.BaseModel import Base

storage_path = config.get('ckan.storage_path')
site_url = config.get('ckan.site_url')


class Call(Base):
    __tablename__ = 'app_call'

    call_id = Column(types.UnicodeText,
                     primary_key=True,
                     default=_types.make_uuid)
    app_id = Column(types.UnicodeText, ForeignKey('app_info.app_id', onupdate="CASCADE", ondelete="CASCADE"))
    user_id = Column(types.UnicodeText)
    elapsed_seconds = Column(types.BIGINT)
    call_status = Column(types.UnicodeText)
    logs = Column(types.UnicodeText)
    created_at = Column(DateTime(timezone=True), default=func.now())

    def __init__(self, user_id, app_id, call_status="PENDING"):
        self.call_id = _types.make_uuid()
        self.user_id = user_id
        self.app_id = app_id
        self.call_status = call_status

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self):
        _dict = {c.key: getattr(self, c.key)
                 for c in inspect(self).mapper.column_attrs}
        _dict['created_at'] = self.created_at.strftime("%d-%m-%Y %H:%M:%S")

        return _dict


class App(Base):
    __tablename__ = 'app_info'

    app_id = Column(types.UnicodeText,
                    primary_key=True,
                    default=_types.make_uuid)
    app_name = Column(types.UnicodeText)
    avatar_path = Column(types.UnicodeText)
    type = Column(types.UnicodeText)
    slug_name = Column(types.UnicodeText, unique=True)
    owner = Column(types.UnicodeText)
    organization = Column(types.UnicodeText)  # optional both
    description = Column(types.UnicodeText, default=u'No description')
    language = Column(types.UnicodeText)  # optional batch
    created_at = Column(DateTime(timezone=True), default=func.now())  # optional both
    curr_code_id = Column(types.UnicodeText)
    app_status = Column(types.UnicodeText, default=u'DEBUG')  # optional both

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def strftime(self):
        self.created_at = self.created_at.strftime("%d-%m-%Y %H:%M:%S")

    def as_dict(self):
        _dict = {c.key: getattr(self, c.key)
                 for c in inspect(self).mapper.column_attrs}
        _dict['dataset_related'] = [dataset.as_dict() for dataset in meta.Session.query(AppRelatedDataset).filter(
            AppRelatedDataset.app_id == self.app_id).all()]
        _dict['category'] = [tag.as_dict() for tag in
                             meta.Session.query(AppCategory).filter(AppCategory.app_id == self.app_id).all()]
        return _dict

    def as_dict_raw(self):
        result = {c.key: getattr(self, c.key)
                  for c in inspect(self).mapper.column_attrs}
        result['created_at'] = self.created_at.isoformat()
        return result


class AppCodeVersion(Base):
    __tablename__ = 'app_code_version'
    code_id = Column(types.UnicodeText,
                     primary_key=True,
                     default=_types.make_uuid)
    app_id = Column(ForeignKey('app_info.app_id', onupdate="CASCADE", ondelete="CASCADE"))
    code_path = Column(types.UnicodeText)
    image = Column(types.UnicodeText)
    image_id = Column(types.UnicodeText)
    build_status = Column(types.UnicodeText, default=u'BUILDING')  # optional both
    created_at = Column(DateTime(timezone=True), default=func.now())  # optional both

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self):
        _dict = {c.key: getattr(self, c.key)
                 for c in inspect(self).mapper.column_attrs}
        return _dict


class AppParam(Base):
    __tablename__ = 'app_param'

    app_id = Column(ForeignKey('app_info.app_id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    # code_id = Column(ForeignKey('app_code_version.code_id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    name = Column(types.UnicodeText, primary_key=True)
    type = Column(types.UnicodeText)
    label = Column(types.UnicodeText)
    description = Column(types.UnicodeText, default=u'No description')

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self):
        _dict = {c.key: getattr(self, c.key)
                 for c in inspect(self).mapper.column_attrs}
        return _dict


class CallInput(Base):
    __tablename__ = 'call_input'

    call_id = Column(ForeignKey('app_call.call_id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    name = Column(types.UnicodeText, primary_key=True)
    type = Column(types.UnicodeText)
    value = Column(types.UnicodeText)

    def as_dict(self):
        _dict = dict(call_id=self.call_id, name=self.name, type=self.type, value=self.value)
        if self.type == 'FILE':
            _dict['value'] = os.path.join('/call', 'file', 'input', self.call_id, self.name)
        return _dict


class CallOutput(Base):
    __tablename__ = 'call_output'

    call_id = Column(ForeignKey('app_call.call_id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    name = Column(types.UnicodeText, primary_key=True)
    type = Column(types.UnicodeText)
    value = Column(types.UnicodeText)

    def as_dict(self):
        _dict = dict(call_id=self.call_id, name=self.name, type=self.type, value=self.value)
        if self.type not in ['TEXT', 'LIST', 'BOOLEAN', 'INTEGER', 'DOUBLE']:
            if self.type != 'FILE':
                self.name = self.name + "." + self.type.lower()
                _dict['name']=self.name
            _dict['value'] = os.path.join('/call', 'file', 'output', self.call_id, self.name)
        return _dict


class AppCategory(Base):
    __tablename__ = 'app_category'
    id = Column(types.UnicodeText,
                primary_key=True,
                default=_types.make_uuid)
    app_id = Column(types.UnicodeText, ForeignKey('app_info.app_id', onupdate="CASCADE", ondelete="CASCADE"))
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


class AppRelatedDataset(Base):
    __tablename__ = 'app_related_dataset'
    id = Column(types.UnicodeText,
                primary_key=True,
                default=_types.make_uuid)
    app_id = Column(types.UnicodeText, ForeignKey('app_info.app_id', onupdate="CASCADE", ondelete="CASCADE"))
    package_id = Column(types.UnicodeText,
                        ForeignKey(package_table.columns['id'], onupdate="CASCADE", ondelete="CASCADE"))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def setOption(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self):
        # _dict = {c.key: getattr(self, c.key)
        #          for c in inspect(self).mapper.column_attrs}
        # del _dict['package_id']
        return dict(app_id=self.app_id, package_name=model.Package.get(self.package_id).name)

    def as_dict_raw(self):
        return {
            'id': self.id,
            'app_id': self.app_id,
            'package_id': self.package_id,
            'package_name': model.Package.get(self.package_id).name
        }


class AppTestReport(Base):
    __tablename__ = 'app_test_report'
    app_id = Column(types.UnicodeText, ForeignKey('app_info.app_id', onupdate="CASCADE", ondelete="CASCADE"),
                    primary_key=True)
    call_id = Column(types.UnicodeText, ForeignKey('app_call.call_id', onupdate="CASCADE", ondelete="CASCADE"),
                     primary_key=True)
    code_using = Column(types.UnicodeText, default=u'')
    note = Column(types.UnicodeText, default=u'')

    def __init__(self, app_id, call_id, code_using):
        self.app_id = app_id
        self.call_id = call_id
        self.code_using = code_using
