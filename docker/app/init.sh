#!/bin/bash
# docker/app/init.sh (Updated - removed database wait logic)
set -e

# Test database connection (optional - will fail gracefully if DB is not ready)
echo "Testing database connection..."
python3 -c "
try:
    from app import create_app, db
    from sqlalchemy import text
    app = create_app()
    with app.app_context():
        result = db.session.execute(text('SELECT 1'))
        print('✅ Database connection successful')
except Exception as e:
    print(f'⚠️  Database connection failed: {e}')
    print('Application will start anyway - check your DATABASE_URL')
" || echo "Database connection test failed, but continuing..."

# Start the application
if [ "$FLASK_ENV" = "development" ]; then
    echo "Starting Flask development server..."
    exec python run.py
else
    echo "Starting Gunicorn production server..."
    exec gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --access-logfile - --error-logfile - run:app
fi