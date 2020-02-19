import os
from datetime import datetime

from ckan import logic
from ckan.common import config
from ckan.lib import munge
from ckan.lib.uploader import get_storage_path, ALLOWED_UPLOAD_TYPES, _get_underlying_file, _copy_file


class CodeUploader(object):
    def __init__(self, upload_file, id, name):
        ''' Setup upload by creating a subdirectory of the storage directory
        of name object_type. old_filename is the name of the file in the url
        field last time'''
        now = datetime.now()
        now_str = now.strftime("D%d-%m-%YT%H:%M:%S")
        self.storage_path = None
        self.name = name
        self.time=now_str
        path = get_storage_path()
        if not path:
            return
        self.storage_path = os.path.join(path, 'code',
                                         id, self.name)
        try:
            os.makedirs(self.storage_path)
        except OSError as e:
            pass
        self.tmp_filepath = os.path.join(self.storage_path, '%s_tmp' %  self.time)
        self.filepath = os.path.join(self.storage_path,  self.time)
        self.upload_file = upload_file
    def upload(self, max_size=2):
        ''' Actually upload the file.
        This should happen just before a commit but after the data has
        been validated and flushed to the db. This is so we do not store
        anything unless the request is actually good.
        max_size is size in MB maximum of the file'''

        with open(self.tmp_filepath, 'wb+') as output_file:
            try:
                _copy_file(self.upload_file, output_file, max_size)
            except logic.ValidationError:
                os.remove(self.tmp_filepath)
                raise
            finally:
                self.upload_file.close()
        os.rename(self.tmp_filepath, self.filepath)
