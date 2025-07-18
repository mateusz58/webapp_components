from app import create_app, db
from app.models import Supplier, Category, Color, Material, Component, Picture, ComponentType, Keyword, Brand, Subbrand, ComponentVariant

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
        'Picture': Picture,
        'ComponentType': ComponentType,
        'Keyword': Keyword,
        'Brand': Brand,  # NEW
        'Subbrand': Subbrand,  # NEW
        'ComponentVariant': ComponentVariant  # NEW
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002, debug=True)
