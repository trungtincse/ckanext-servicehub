import requests
from PIL import Image
from io import BytesIO, StringIO


APIKEY = 'aee93875-75c7-481a-aa11-27c9bb72a2bf'  # get apikey on CKAN user profile page


def simple_binary_file():
    file = BytesIO(b'some initial text data')
    file.name = 'code.zip'
    file.seek(0)
    return file.read()


def simple_img_file():
    file = BytesIO()
    image = Image.new('RGBA', size=(50, 50), color=(256, 0, 0))
    image.save(file, 'png')
    file.name = 'avatar.png'
    file.seek(0)
    return file.read()


class ServiceLanguage:
    PYTHON = 'Python'
    JAVA = 'Java'


class ServiceType:
    BATCH = 'Batch'
    SERVER = 'Server'


class ParamType:
    FILE = 'file'
    TEXT = 'text'
    NUMBER = 'number'


def client_req(action_name, data=None, files=None):
    headers = {
        'X-CKAN-API-Key': APIKEY,
        'Authorization': APIKEY
    }
    return requests.post('http://localhost:5000/api/action/%s' % action_name, files=files, data=data,
                         headers=headers).json()


def dict_to_tuple(*args):
    return [(k, v)
            for arg in args
            for k, v in arg.items()]


def create_input(type):
    if type==ParamType.FILE:
        return simple_binary_file()
    elif type==ParamType.NUMBER:
        return 1
    elif type==ParamType.TEXT:
        return 'abc'

