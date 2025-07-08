from app import create_app, db
from app.models import Component

app = create_app()
with app.app_context():
    components = Component.query.all()
    print(f"Total components: {len(components)}")
    for comp in components[:5]:  # Show first 5
        print(f"ID: {comp.id}, Product Number: {comp.product_number}, Description: {comp.description}")
