# config.py

import os
from dotenv import load_dotenv
from data_manager import get_database_path

# Carga las variables del archivo .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_key_change_in_production')
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'
    ENV = os.getenv('FLASK_ENV', 'production')
    
    # Configuración de SQLite usando el gestor de datos
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{get_database_path()}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuraciones adicionales para SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}