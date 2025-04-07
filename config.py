import os
from sqlalchemy import create_engine
import urllib

class Config(object):
    SECRET_KEY='clave nueva'
    SESION_COOKIE_SECURE=False

class DevelopmentConfig(Config):
    DEBUG=True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:12345@127.0.0.1/gc_db' #Mi url mas bdidgs801
    SQLALCHEMY_TRACK_MODIFICATIONS=False