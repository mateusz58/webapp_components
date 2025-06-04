import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database'
    SQLALCHEMY_SCHEMA = 'component_app'  # Specify the schema to use
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app/static/uploads')
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/uploads/variant_uploads', exist_ok=True)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
