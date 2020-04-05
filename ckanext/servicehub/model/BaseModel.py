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

