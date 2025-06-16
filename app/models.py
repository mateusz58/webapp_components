from app import db
from datetime import datetime
import json
from sqlalchemy.orm.attributes import flag_modified

# Define a base class with the schema setting
class Base(db.Model):
    __abstract__ = True
    __table_args__ = {'schema': 'component_app'}

class ComponentType(Base):
    __tablename__ = 'component_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relationship to components
    components = db.relationship('Component', backref='component_type', lazy=True)
    
    # NEW: Relationship to component type properties
    type_properties = db.relationship('ComponentTypeProperty', backref='component_type', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ComponentType {self.name}>'

class ComponentTypeProperty(Base):
    """Model for component_type_property table - maps component types to their properties"""
    __tablename__ = 'component_type_property'
    
    id = db.Column(db.Integer, primary_key=True)
    component_type_id = db.Column(db.Integer, db.ForeignKey('component_app.component_type.id'), nullable=False)
    property_name = db.Column(db.String(100), nullable=False)
    property_type = db.Column(db.String(50), nullable=False)  # 'text', 'select', 'multiselect'
    is_required = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('component_type_id', 'property_name'),
        {'schema': 'component_app'}
    )
    
    def __repr__(self):
        return f'<ComponentTypeProperty {self.component_type.name}.{self.property_name}>'
    
    @property
    def display_name(self):
        """Return a human-readable property name"""
        return self.property_name.replace('_', ' ').title()
    
    def get_options(self):
        """Get options for this property based on property_name"""
        # Define options based on property name and type
        if self.property_type == 'select':
            if self.property_name == 'material':
                return ['cotton', 'polyester', 'wool', 'silk', 'linen', 'denim', 'satin', 'velvet', 'leather', 'synthetic', 'plastic', 'metal', 'wood', 'bone', 'mother of pearl', 'acrylic', 'brass', 'steel', 'nylon', 'nickel', 'aluminum', 'cardboard', 'paper', 'vinyl', 'fabric']
            elif self.property_name == 'color':
                return ['black', 'white', 'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'brown', 'gray', 'navy', 'beige', 'cream', 'silver', 'gold', 'bronze', 'copper', 'chrome', 'antique brass']
        elif self.property_type == 'multiselect':
            if self.property_name == 'gender':
                return ['ladies', 'men', 'unisex', 'all', 'kids']
            elif self.property_name == 'style':
                return ['casual', 'formal', 'sport', 'winter', 'summer', 'vintage', 'modern', 'classic']
            elif self.property_name == 'subbrand':
                return ['MAR Sport', 'MAR Classic', 'MMC Pro', 'MMC Casual', 'UBL Premium', 'UBL Basic']
        return []
    
    def get_placeholder(self):
        """Get placeholder text for this property"""
        if self.property_type == 'text':
            if self.property_name == 'finish':
                return 'e.g., waterproof, matte, glossy, brushed'
            elif self.property_name == 'weight':
                return 'e.g., 120gsm, 200gsm'
            elif self.property_name == 'size':
                return 'e.g., 12mm, 15mm, 18mm, 20mm'
            elif self.property_name == 'subcategory':
                return 'e.g., jacket, pants, dress, shirt'
        return ''

class Supplier(Base):
    __tablename__ = 'supplier'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(db.String(50), unique=True, nullable=False, default='NO CODE')
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # REMOVE onupdate since database trigger handles it
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)  # Remove: onupdate=datetime.utcnow
    
    # Relationship to components
    components = db.relationship('Component', backref='supplier', lazy=True)

    def __repr__(self):
        return f'<Supplier {self.supplier_code}>'

class Category(Base):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relationship to components  
    components = db.relationship('Component', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Color(Base):
    __tablename__ = 'color'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relationship to component variants
    component_variants = db.relationship('ComponentVariant', backref='color', lazy=True)

    def __repr__(self):
        return f'<Color {self.name}>'

class Material(Base):
    __tablename__ = 'material'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Material {self.name}>'

class Brand(Base):
    __tablename__ = 'brand'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)  # Database trigger handles updates

    # Relationships
    subbrands = db.relationship('Subbrand', backref='brand', lazy=True, cascade='all, delete-orphan')
    # Use the ComponentBrand association object for the relationship
    component_associations = db.relationship('ComponentBrand', back_populates='brand', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Brand {self.name}>'

    def get_active_subbrands(self):
        """Get all active subbrands for this brand"""
        return [sb for sb in self.subbrands]

    def get_components_count(self):
        """Get count of components using this brand"""
        return len(self.component_associations)

    @property
    def components(self):
        """Get components associated with this brand"""
        return [assoc.component for assoc in self.component_associations]

class Subbrand(Base):
    __tablename__ = 'subbrand'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('component_app.brand.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)  # Database trigger handles updates

    # Ensure unique subbrand name per brand
    __table_args__ = (
        db.UniqueConstraint('name', 'brand_id', name='_brand_subbrand_uc'),
        {'schema': 'component_app'}
    )

    def __repr__(self):
        return f'<Subbrand {self.brand.name}/{self.name}>'

    def get_full_name(self):
        """Get full name including brand"""
        return f"{self.brand.name} - {self.name}"

class Keyword(Base):
    __tablename__ = 'keyword'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Keyword {self.name}>'

# Association table for many-to-many keyword-component relationship
keyword_component = db.Table('keyword_component',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('component_id', db.Integer, db.ForeignKey('component_app.component.id'), nullable=False),
    db.Column('keyword_id', db.Integer, db.ForeignKey('component_app.keyword.id'), nullable=False),
    db.UniqueConstraint('component_id', 'keyword_id'),
    schema='component_app'
)

class ComponentBrand(Base):
    """Association object for Component-Brand many-to-many relationship with additional fields"""
    __tablename__ = 'component_brand'

    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey('component_app.component.id', ondelete='CASCADE'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('component_app.brand.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('component_id', 'brand_id'),
        {'schema': 'component_app'}
    )

    # Relationships
    component = db.relationship('Component', back_populates='brand_associations')
    brand = db.relationship('Brand', back_populates='component_associations')

    def __repr__(self):
        return f'<ComponentBrand {self.component.product_number} - {self.brand.name}>'

class Component(Base):
    __tablename__ = 'component'
    
    id = db.Column(db.Integer, primary_key=True)
    product_number = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    
    # MANDATORY foreign keys (all components must have these)
    component_type_id = db.Column(db.Integer, db.ForeignKey('component_app.component_type.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('component_app.supplier.id'), nullable=True)  # Now optional
    category_id = db.Column(db.Integer, db.ForeignKey('component_app.category.id'), nullable=False)
    
    # STATUS TRACKING (Product-wide status - applies to all variants)
    proto_status = db.Column(db.String(20), default='pending')  # 'pending', 'ok', 'not_ok'
    proto_comment = db.Column(db.Text)
    proto_date = db.Column(db.DateTime)
    
    sms_status = db.Column(db.String(20), default='pending')  # 'pending', 'ok', 'not_ok'
    sms_comment = db.Column(db.Text)
    sms_date = db.Column(db.DateTime)
    
    pps_status = db.Column(db.String(20), default='pending')  # 'pending', 'ok', 'not_ok'
    pps_comment = db.Column(db.Text)
    pps_date = db.Column(db.DateTime)
    
    # FLEXIBLE properties as JSONB
    properties = db.Column(db.JSON, default={})
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # RELATIONSHIPS
    variants = db.relationship('ComponentVariant', backref='component', lazy=True, cascade='all, delete-orphan')
    keywords = db.relationship('Keyword', secondary=keyword_component, lazy='subquery',
                              backref=db.backref('components', lazy=True))

    # Use the ComponentBrand association object for the brand relationship
    brand_associations = db.relationship('ComponentBrand', back_populates='component', cascade='all, delete-orphan')

    # Pictures that belong to the main component (not variant-specific)
    pictures = db.relationship('Picture', 
                              foreign_keys='Picture.component_id',
                              backref='parent_component', 
                              lazy=True, 
                              cascade='all, delete-orphan')

    __table_args__ = (
        # Updated unique constraint to handle null supplier_id
        db.UniqueConstraint('product_number', 'supplier_id', name='_product_supplier_uc'),
        {'schema': 'component_app'}
    )

    def __repr__(self):
        return f'<Component {self.product_number}>'
    
    # Property to get brands easily
    @property
    def brands(self):
        """Get list of brands associated with this component"""
        return [assoc.brand for assoc in self.brand_associations]

    # Helper methods for properties
    def get_property(self, key, default=None):
        """Get a property value from the JSON properties field"""
        if self.properties and key in self.properties:
            prop = self.properties[key]
            if isinstance(prop, dict) and 'value' in prop:
                return prop['value']
            return prop
        return default
    
    def set_property(self, key, value, prop_type='text'):
        """Set a property in the JSON properties field with proper structure"""
        if self.properties is None:
            self.properties = {}
        
        now = datetime.utcnow().isoformat() + 'Z'
        
        # If property exists, keep created_at, update updated_at
        created_at = now
        if key in self.properties and isinstance(self.properties[key], dict):
            created_at = self.properties[key].get('created_at', now)
        
        self.properties[key] = {
            'value': value,
            'type': prop_type,
            'created_at': created_at,
            'updated_at': now
        }
        
        # Mark as modified for SQLAlchemy
        flag_modified(self, 'properties')
    
    # Brand management methods
    def add_brand(self, brand):
        """Add a brand to this component"""
        # Check if association already exists
        existing = ComponentBrand.query.filter_by(
            component_id=self.id,
            brand_id=brand.id
        ).first()

        if not existing:
            association = ComponentBrand(component_id=self.id, brand_id=brand.id)
            db.session.add(association)
            return association
        return existing

    def remove_brand(self, brand):
        """Remove a brand from this component"""
        association = ComponentBrand.query.filter_by(
            component_id=self.id,
            brand_id=brand.id
        ).first()

        if association:
            db.session.delete(association)
            return True
        return False

    def get_brand_names(self):
        """Get list of brand names for this component"""
        return [brand.name for brand in self.brands]

    def has_brand(self, brand_name):
        """Check if component has a specific brand"""
        return any(brand.name == brand_name for brand in self.brands)

    # Variant management methods
    def create_variant(self, color_id, variant_name=None, description=None):
        """Create a new color variant of this component"""
        # Check if variant already exists for this color
        existing = ComponentVariant.query.filter_by(
            component_id=self.id, 
            color_id=color_id
        ).first()
        
        if existing:
            raise ValueError(f"Variant already exists for this color")
        
        # Get color name for default variant name
        if not variant_name:
            color = Color.query.get(color_id)
            variant_name = color.name if color else f"Color {color_id}"
        
        variant = ComponentVariant(
            component_id=self.id,
            color_id=color_id,
            variant_name=variant_name,
            description=description
        )
        
        return variant
    
    def get_variant_by_color(self, color_id):
        """Get variant by color ID"""
        return ComponentVariant.query.filter_by(
            component_id=self.id,
            color_id=color_id
        ).first()
    
    def get_available_colors(self):
        """Get list of available colors for this component"""
        return [variant.color for variant in self.variants if variant.is_active]
    
    # Status management methods
    def update_proto_status(self, status, comment=None):
        """Update proto status"""
        if status not in ['pending', 'ok', 'not_ok']:
            raise ValueError("Status must be 'pending', 'ok', or 'not_ok'")
        
        self.proto_status = status
        self.proto_comment = comment
        self.proto_date = datetime.utcnow()
    
    def update_sms_status(self, status, comment=None):
        """Update SMS status"""
        if status not in ['pending', 'ok', 'not_ok']:
            raise ValueError("Status must be 'pending', 'ok', or 'not_ok'")
        
        self.sms_status = status
        self.sms_comment = comment
        self.sms_date = datetime.utcnow()
    
    def update_pps_status(self, status, comment=None):
        """Update PPS status"""
        if status not in ['pending', 'ok', 'not_ok']:
            raise ValueError("Status must be 'pending', 'ok', or 'not_ok'")
        
        self.pps_status = status
        self.pps_comment = comment
        self.pps_date = datetime.utcnow()
    
    def get_overall_status(self):
        """Get overall approval status"""
        if self.pps_status == 'ok':
            return 'approved'
        elif self.pps_status == 'not_ok' or self.sms_status == 'not_ok' or self.proto_status == 'not_ok':
            return 'rejected'
        elif self.proto_status == 'ok' and self.sms_status == 'ok' and self.pps_status == 'pending':
            return 'pending_pps'
        elif self.proto_status == 'ok' and self.sms_status == 'pending':
            return 'pending_sms'
        elif self.proto_status == 'pending':
            return 'pending_proto'
        else:
            return 'in_progress'
    
    def get_status_badge_class(self):
        """Get CSS class for status badge"""
        status = self.get_overall_status()
        status_classes = {
            'approved': 'status-approved',
            'rejected': 'status-rejected',
            'pending_pps': 'status-pending',
            'pending_sms': 'status-pending',
            'pending_proto': 'status-pending',
            'in_progress': 'status-pending'
        }
        return status_classes.get(status, 'status-pending')
    
    def get_status_display(self):
        """Get human-readable status display"""
        status = self.get_overall_status()
        status_display = {
            'approved': 'Approved',
            'rejected': 'Rejected',
            'pending_pps': 'Pending PPS',
            'pending_sms': 'Pending SMS', 
            'pending_proto': 'Pending Proto',
            'in_progress': 'In Progress'
        }
        return status_display.get(status, 'Unknown')
    
    # Helper methods for common properties
    def get_material(self):
        """Get material property"""
        return self.get_property('material')
    
    def set_material(self, material_name):
        """Set material property"""
        self.set_property('material', material_name, 'text')
    
    def get_color_property(self):
        """Get color property (for components that have colors)"""
        return self.get_property('color')
    
    def set_color_property(self, color_name):
        """Set color property"""
        self.set_property('color', color_name, 'text')
    
    def get_gender(self):
        """Get gender property"""
        return self.get_property('gender')
    
    def set_gender(self, gender_list):
        """Set gender property (can be array)"""
        self.set_property('gender', gender_list, 'array')
    
    def get_brand_property(self):
        """Get brand property from JSON properties (legacy support)"""
        return self.get_property('brand')
    
    def set_brand_property(self, brand_name):
        """Set brand property in JSON (legacy support)"""
        self.set_property('brand', brand_name, 'text')
    
    def get_style(self):
        """Get style property"""
        return self.get_property('style')
    
    def set_style(self, style_list):
        """Set style property (can be array)"""
        self.set_property('style', style_list, 'array')


class ComponentVariant(Base):
    __tablename__ = 'component_variant'
    
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey('component_app.component.id'), nullable=False)
    color_id = db.Column(db.Integer, db.ForeignKey('component_app.color.id'), nullable=False)
    variant_name = db.Column(db.String(100))  # e.g., "Silver", "Deep Black"
    description = db.Column(db.Text)  # variant-specific description
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Pictures that belong to this specific variant
    variant_pictures = db.relationship('Picture', 
                                     foreign_keys='Picture.variant_id',
                                     backref='variant', 
                                     lazy=True, 
                                     cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('component_id', 'color_id', name='_component_color_uc'),
        {'schema': 'component_app'}
    )

    def __repr__(self):
        return f'<ComponentVariant {self.component.product_number}-{self.color.name}>'
    
    def get_display_name(self):
        """Get display name for the variant"""
        return self.variant_name or self.color.name
    
    def get_full_product_number(self):
        """Get full product number including variant"""
        return f"{self.component.product_number}-{self.color.name.upper()}"
    
    def get_inherited_status(self):
        """Get status inherited from parent component"""
        return {
            'proto': {
                'status': self.component.proto_status,
                'comment': self.component.proto_comment,
                'date': self.component.proto_date
            },
            'sms': {
                'status': self.component.sms_status,
                'comment': self.component.sms_comment,
                'date': self.component.sms_date
            },
            'pps': {
                'status': self.component.pps_status,
                'comment': self.component.pps_comment,
                'date': self.component.pps_date
            }
        }


class Picture(Base):
    __tablename__ = 'picture'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Picture can belong to either component OR variant (not both)
    component_id = db.Column(db.Integer, db.ForeignKey('component_app.component.id'), nullable=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('component_app.component_variant.id'), nullable=True)
    
    picture_name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    picture_order = db.Column(db.Integer, nullable=False)
    
    # Additional metadata
    alt_text = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        # Ensure picture belongs to either component OR variant
        db.CheckConstraint(
            '(component_id IS NOT NULL AND variant_id IS NULL) OR (component_id IS NULL AND variant_id IS NOT NULL)',
            name='picture_belongs_to_component_or_variant'
        ),
        # Unique picture order per component/variant
        db.UniqueConstraint('component_id', 'picture_order', name='_component_picture_order_uc'),
        db.UniqueConstraint('variant_id', 'picture_order', name='_variant_picture_order_uc'),
        {'schema': 'component_app'}
    )

    def __repr__(self):
        if self.component_id:
            return f'<Picture {self.picture_name} (Component)>'
        else:
            return f'<Picture {self.picture_name} (Variant)>'
    
    def get_owner(self):
        """Get the component or variant this picture belongs to"""
        if self.component_id:
            return self.parent_component
        else:
            return self.variant

# Helper functions for working with ComponentBrand relationships
def add_brand_to_component(component_id, brand_id):
    """Add a brand to a component"""
    try:
        # Check if association already exists
        existing = ComponentBrand.query.filter_by(
            component_id=component_id,
            brand_id=brand_id
        ).first()

        if not existing:
            association = ComponentBrand(
                component_id=component_id,
                brand_id=brand_id
            )
            db.session.add(association)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        raise e

def remove_brand_from_component(component_id, brand_id):
    """Remove a brand from a component"""
    try:
        association = ComponentBrand.query.filter_by(
            component_id=component_id,
            brand_id=brand_id
        ).first()

        if association:
            db.session.delete(association)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        raise e

def get_components_by_brand(brand_id):
    """Get all components for a specific brand"""
    return db.session.query(Component).join(ComponentBrand).filter(
        ComponentBrand.brand_id == brand_id
    ).all()

def get_brands_for_component(component_id):
    """Get all brands for a specific component"""
    return db.session.query(Brand).join(ComponentBrand).filter(
        ComponentBrand.component_id == component_id
    ).all()