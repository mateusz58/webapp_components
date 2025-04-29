from app import db
from datetime import datetime

# Define a base class with the schema setting
class Base(db.Model):
    __abstract__ = True
    __table_args__ = {'schema': 'component_app'}

class Supplier(Base):
    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(db.String(50), unique=True, nullable=False)
    address = db.Column(db.String(255))
    components = db.relationship('Component', backref='supplier', lazy=True)

    def __repr__(self):
        return f'<Supplier {self.supplier_code}>'

class Category(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    components = db.relationship('Component', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Color(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    components = db.relationship('Component', backref='color', lazy=True)

    def __repr__(self):
        return f'<Color {self.name}>'

class Material(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    components = db.relationship('Component', backref='material', lazy=True)

    def __repr__(self):
        return f'<Material {self.name}>'

class Component(Base):
    id = db.Column(db.Integer, primary_key=True)
    product_number = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    supplier_id = db.Column(db.Integer, db.ForeignKey('component_app.supplier.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('component_app.category.id'), nullable=False)
    color_id = db.Column(db.Integer, db.ForeignKey('component_app.color.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('component_app.material.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pictures = db.relationship('Picture', backref='component', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Component {self.product_number}>'

class Picture(Base):
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey('component_app.component.id'), nullable=False)
    picture_name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    picture_order = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        db.UniqueConstraint('component_id', 'picture_order', name='_component_picture_order_uc'),
        {'schema': 'component_app'}  # Override the schema setting from Base
    )

    def __repr__(self):
        return f'<Picture {self.picture_name}>'
