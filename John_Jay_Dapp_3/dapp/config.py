import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_APP = os.environ.get('FLASK_APP')
    FLASK_ENV = os.environ.get('FLASK_ENV')
    SERVER_NAME = os.environ.get('SERVER_NAME')
    CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS')
    WALLET_PRIVATE_KEY = os.environ.get('WALLET_PRIVATE_KEY')
    WALLET_ADDRESS = os.environ.get('WALLET_ADDRESS')
    WEB3_PROVIDER = os.environ.get('WEB_PROVIDER')

    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    MAX_CONTENT_LENGTH = 1024 * 1024
    UPLOAD_EXTENSIONS = ['.txt']
    UPLOAD_PATH = 'uploads'
    SEND_FILE_MAX_AGE_DEFAULT = 0
