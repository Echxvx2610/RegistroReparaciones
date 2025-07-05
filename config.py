# config.py

import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_key')
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'
    ENV = os.getenv('FLASK_ENV', 'production')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')