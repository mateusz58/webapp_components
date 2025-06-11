# run.py - The main entry point for the Flask application
"""
This is the main entry point that starts your Flask application.
When you run 'python run.py', this file is executed.
"""

from app import create_app

# Create the Flask application instance using the app factory pattern
app = create_app()

if __name__ == '__main__':
    # This runs only when the script is executed directly (not imported)
    # host='0.0.0.0' makes the app accessible from any IP address
    # port=5000 is the default Flask port
    # debug=True enables debug mode for development (shows detailed errors)
    app.run(host='0.0.0.0', port=5000, debug=True)