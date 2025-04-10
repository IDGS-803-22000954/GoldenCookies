import settings


class Config(object):
    SECRET_KEY = settings.SECRET_KEY
    SESSION_COOKIE_SECURE = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}/{settings.DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
