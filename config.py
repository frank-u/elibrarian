import os

basedir = os.path.abspath(os.path.dirname(__file__))
DB_DEV_SQLITE_URL = 'sqlite:///' + os.path.join(basedir, 'db-dev.sqlite')
DB_TEST_SQLITE_URL = 'sqlite:///' + os.path.join(basedir, 'db-test.sqlite')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'wTsYJGYWaDHE803D5Y94yNrkR1DHG'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True

    ELIBRARIAN_ITEMS_PER_PAGE = 15

    @staticmethod
    def init_app(app):
        pass


class ConfigDev(Config):
    DEBUG = True
    BOOTSTRAP_SERVE_LOCAL = True


class ConfigTestingVirtualenv(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URL') or DB_TEST_SQLITE_URL
    WTF_CSRF_ENABLED = False


class ConfigDevDocker(ConfigDev):
    # Docker image with postgres
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres@db/postgres"


class ConfigDevVirtualenv(ConfigDev):
    # DB in local project root folder
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DEV_DATABASE_URL') or DB_DEV_SQLITE_URL


config = {
    'dev_docker': ConfigDevDocker,
    'dev_virtualenv': ConfigDevVirtualenv,

    'testing_virtualenv': ConfigTestingVirtualenv,

    'default': ConfigDevVirtualenv
}
