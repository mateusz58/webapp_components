import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database'
    SQLALCHEMY_SCHEMA = 'component_app'  # Specify the schema to use
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # WebDAV configuration - no local file system mounting needed
    WEBDAV_BASE_URL = 'http://31.182.67.115/webdav/components'  # Direct WebDAV URL
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    # Legacy upload folder for backward compatibility (if needed for temp files)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app/static/uploads')
    LOCAL_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app/static/uploads')
