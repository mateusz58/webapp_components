from app import create_app, db
from app.models import Supplier, Category, Color, Material, Component, Picture

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'Supplier': Supplier, 
        'Category': Category,
        'Color': Color, 
        'Material': Material, 
        'Component': Component, 
        'Picture': Picture
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
