import os
import platform


class Config(object):

    basedir = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    # SECRET_KEY = config('SECRET_KEY'  , default='S#perS3crEt_007')
    SECRET_KEY = os.getenv('SECRET_KEY', 'S#perS3crEt_007')
    SESSION_COOKIE_NAME = 'ieo'

    # This will create a file in <app> FOLDER
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    # PostgreSQL database 188.166.206.84
    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        os.getenv('DB_ENGINE', default='postgresql'),
        os.getenv('DB_USERNAME', default='postgres'),
        os.getenv('DB_PASS', default='1234'),
        os.getenv('DB_HOST', default='localhost'),
        os.getenv('DB_PORT', default=5432),
        os.getenv('DB_NAME', default='ieo')
    )

    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234@db:5432/vch_main'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 300

    # Assets Management
    ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets')

    SOCIAL_AUTH_GITHUB = False

    GITHUB_ID = os.getenv('GITHUB_ID')
    GITHUB_SECRET = os.getenv('GITHUB_SECRET')
    
    # SQLALCHEMY_BINDS = {
        # "thip": os.environ.get("DATABASE_THIP_URL"),
        # "thip": 'postgresql://postgres:1234@localhost:5432/THIP',
    # }

    # email
    # MAIL_SERVER = 'smtp.gmail.com'
    # MAIL_PORT = 587
    # MAIL_USERNAME = 'supawitwangasok3@gmail.com'
    # MAIL_PASSWORD = 'vqqdlkpsmryuexqn'
    # MAIL_USE_TLS = True
    # MAIL_USE_SSL = False

    # Enable/Disable Github Social Login
    # if GITHUB_ID and GITHUB_SECRET:
    #     SOCIAL_AUTH_GITHUB = True


class ProductionConfig(Config):
    DEBUG = False

    basedir = os.path.abspath(os.path.dirname(__file__))

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # PostgreSQL database 188.166.206.84
    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        os.getenv('DB_ENGINE', default='postgresql'),
        os.getenv('DB_USERNAME', default='postgres'),
        os.getenv('DB_PASS', default='1234'),
        os.getenv('DB_HOST', default='localhost'),
        os.getenv('DB_PORT', default=5432),
        os.getenv('DB_NAME', default='ieo')
    )
    # SQLALCHEMY_BINDS = {
        # "thip": os.environ.get("DATABASE_THIP_URL"),
        # "thip": 'postgresql://postgres:1234@localhost:5432/THIP',
    # }
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234@db:5432/webmeter'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 300

    # email
    # MAIL_SERVER = 'smtp.gmail.com'
    # MAIL_PORT = 587
    # MAIL_USERNAME = 'supawitwangasok3@gmail.com'
    # MAIL_PASSWORD = 'vqqdlkpsmryuexqn'
    # MAIL_USE_TLS = True
    # MAIL_USE_SSL = False


class DebugConfig(Config):
    DEBUG = True


# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
