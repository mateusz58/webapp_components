from app import db
from app.models import Property, ComponentTypeProperty, Material, Color, Category, Brand, Supplier
from flask import current_app
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

class PropertyService:
    
    @staticmethod
    def get_all_properties():
        return Property.query.filter(Property.is_active == True).order_by(Property.property_key).all()
    
    @staticmethod
    def get_property_by_key(property_key):
        return Property.query.filter_by(property_key=property_key, is_active=True).first()
    
    @staticmethod
    def get_properties_for_component_type(component_type_id):
        return db.session.query(ComponentTypeProperty).options(
            selectinload(ComponentTypeProperty.component_type)
        ).filter_by(component_type_id=component_type_id).order_by(ComponentTypeProperty.display_order).all()
    
    @staticmethod
    def get_property_form_config(component_type_id):
        type_properties = PropertyService.get_properties_for_component_type(component_type_id)
        config = {}
        
        for type_prop in type_properties:
            widget_config = type_prop.get_widget_config()
            config[type_prop.property_name] = {
                'display_name': type_prop.display_name,
                'data_type': widget_config['type'],
                'required': widget_config['required'],
                'options': widget_config['options'],
                'placeholder': widget_config.get('placeholder', ''),
                'display_order': type_prop.display_order
            }
        
        return config
    
    @staticmethod
    def validate_property_values(component_type_id, property_values):
        validation_errors = []
        type_properties = PropertyService.get_properties_for_component_type(component_type_id)
        
        for type_prop in type_properties:
            property_name = type_prop.property_name
            value = property_values.get(property_name)
            
            if type_prop.is_required and not value:
                validation_errors.append(f"{type_prop.display_name} is required")
                continue
            
            if value:
                validation_result = PropertyService._validate_single_property(type_prop, value)
                if not validation_result['valid']:
                    validation_errors.append(validation_result['error'])
        
        return {
            'valid': len(validation_errors) == 0,
            'errors': validation_errors
        }
    
    @staticmethod
    def _validate_single_property(type_prop, value):
        property_definition = type_prop.get_property_definition()
        
        if not property_definition:
            return {'valid': True}
        
        if property_definition.data_type == 'select':
            options = property_definition.get_dynamic_options()
            valid_values = [opt['name'] for opt in options]
            if value not in valid_values:
                return {
                    'valid': False,
                    'error': f"{type_prop.display_name} must be one of: {', '.join(valid_values)}"
                }
        
        elif property_definition.data_type == 'multiselect':
            if isinstance(value, str):
                value = [v.strip() for v in value.split(',')]
            
            if isinstance(value, list):
                options = property_definition.get_dynamic_options()
                valid_values = [opt['name'] for opt in options]
                invalid_values = [v for v in value if v not in valid_values]
                if invalid_values:
                    return {
                        'valid': False,
                        'error': f"{type_prop.display_name} contains invalid values: {', '.join(invalid_values)}"
                    }
        
        return {'valid': True}
    
    @staticmethod
    def populate_property_options(property_key):
        property_definition = PropertyService.get_property_by_key(property_key)
        if not property_definition:
            return []
        
        dynamic_options = property_definition.get_dynamic_options()
        
        if dynamic_options:
            property_definition.options = dynamic_options
            db.session.commit()
            current_app.logger.info(f"Updated options for property {property_key} with {len(dynamic_options)} items")
        
        return dynamic_options
    
    @staticmethod
    def create_property(property_data):
        try:
            property_obj = Property(
                property_key=property_data['property_key'],
                display_name=property_data['display_name'],
                data_type=property_data['data_type'],
                description=property_data.get('description', ''),
                is_active=property_data.get('is_active', True),
                options=property_data.get('options', [])
            )
            
            db.session.add(property_obj)
            db.session.commit()
            
            PropertyService.populate_property_options(property_obj.property_key)
            
            return {
                'success': True,
                'property': property_obj,
                'message': f"Property {property_obj.property_key} created successfully"
            }
            
        except IntegrityError as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f"Property key already exists: {property_data['property_key']}"
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating property: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to create property: {str(e)}"
            }
    
    @staticmethod
    def update_property(property_id, property_data):
        try:
            property_obj = Property.query.get(property_id)
            if not property_obj:
                return {
                    'success': False,
                    'error': 'Property not found'
                }
            
            property_obj.display_name = property_data.get('display_name', property_obj.display_name)
            property_obj.data_type = property_data.get('data_type', property_obj.data_type)
            property_obj.description = property_data.get('description', property_obj.description)
            property_obj.is_active = property_data.get('is_active', property_obj.is_active)
            property_obj.options = property_data.get('options', property_obj.options)
            
            db.session.commit()
            
            PropertyService.populate_property_options(property_obj.property_key)
            
            return {
                'success': True,
                'property': property_obj,
                'message': f"Property {property_obj.property_key} updated successfully"
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating property: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to update property: {str(e)}"
            }
    
    @staticmethod
    def delete_property(property_id):
        try:
            property_obj = Property.query.get(property_id)
            if not property_obj:
                return {
                    'success': False,
                    'error': 'Property not found'
                }
            
            property_obj.is_active = False
            db.session.commit()
            
            return {
                'success': True,
                'message': f"Property {property_obj.property_key} deactivated successfully"
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting property: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to delete property: {str(e)}"
            }
    
    @staticmethod
    def add_property_to_component_type(component_type_id, property_data):
        try:
            type_property = ComponentTypeProperty(
                component_type_id=component_type_id,
                property_name=property_data['property_name'],
                property_type=property_data['property_type'],
                is_required=property_data.get('is_required', False),
                display_order=property_data.get('display_order', 0)
            )
            
            db.session.add(type_property)
            db.session.commit()
            
            return {
                'success': True,
                'type_property': type_property,
                'message': f"Property {property_data['property_name']} added to component type"
            }
            
        except IntegrityError as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f"Property already exists for this component type"
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding property to component type: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to add property: {str(e)}"
            }
    
    @staticmethod
    def remove_property_from_component_type(component_type_id, property_name):
        try:
            type_property = ComponentTypeProperty.query.filter_by(
                component_type_id=component_type_id,
                property_name=property_name
            ).first()
            
            if not type_property:
                return {
                    'success': False,
                    'error': 'Property not found for this component type'
                }
            
            db.session.delete(type_property)
            db.session.commit()
            
            return {
                'success': True,
                'message': f"Property {property_name} removed from component type"
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error removing property from component type: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to remove property: {str(e)}"
            }