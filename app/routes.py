from flask import Blueprint, render_template, request, jsonify
from app import db
from sqlalchemy import text

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main.route('/test-connection')
def test_connection():
    """Test database connection"""
    try:
        # Test if we can connect to the database and query using raw SQL with schema
        result = db.session.execute(text("SELECT 1 as test"))
        value = result.fetchone()[0]
        
        # Include schema-specific testing
        schema_info = {
            'success': True,
            'message': 'Successfully connected to the database',
            'value': value
        }
        
        # Try to check if the schema exists
        try:
            schema_check = db.session.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'component_app'"))
            if schema_check.fetchone():
                schema_info['schema_exists'] = True
                schema_info['schema_name'] = 'component_app'
            else:
                schema_info['schema_exists'] = False
        except Exception as e:
            schema_info['schema_check_error'] = str(e)
        
        return jsonify(schema_info)
    except Exception as e:
        error_info = {
            'success': False,
            'message': 'Database connection error',
            'error': str(e)
        }
        return jsonify(error_info), 500
