"""
Cache configuration and utilities for the component management application.
"""

import os
from flask_caching import Cache

# Cache configuration based on environment
CACHE_CONFIG = {
    'development': {
        'CACHE_TYPE': 'simple',  # In-memory cache for development
        'CACHE_DEFAULT_TIMEOUT': 300
    },
    'production': {
        'CACHE_TYPE': 'redis',   # Redis for production
        'CACHE_REDIS_HOST': os.environ.get('REDIS_HOST', 'localhost'),
        'CACHE_REDIS_PORT': int(os.environ.get('REDIS_PORT', 6379)),
        'CACHE_REDIS_DB': int(os.environ.get('REDIS_DB', 0)),
        'CACHE_REDIS_PASSWORD': os.environ.get('REDIS_PASSWORD'),
        'CACHE_DEFAULT_TIMEOUT': 600,
        'CACHE_KEY_PREFIX': 'webapp_components:'
    },
    'testing': {
        'CACHE_TYPE': 'null',    # No cache for testing
        'CACHE_DEFAULT_TIMEOUT': 0
    }
}

def init_cache(app):
    """Initialize cache with the Flask app"""
    
    # Get environment
    env = app.config.get('ENV', 'development')
    
    # Get cache config for environment
    cache_config = CACHE_CONFIG.get(env, CACHE_CONFIG['development'])
    
    # Update app config
    app.config.update(cache_config)
    
    # Initialize cache
    cache = Cache(app)
    
    # Add cache instance to app for access elsewhere
    app.cache = cache
    
    return cache

def create_cache_key(*args, **kwargs):
    """Create a consistent cache key from arguments"""
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (str, int)):
            key_parts.append(str(arg))
        elif hasattr(arg, 'id'):
            key_parts.append(f"{arg.__class__.__name__}_{arg.id}")
        else:
            key_parts.append(str(hash(str(arg))))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}_{v}")
    
    return ":".join(key_parts)

def invalidate_component_cache(cache, component_id=None):
    """Invalidate component-related cache entries"""
    patterns_to_clear = [
        'filter_options',
        'component_stats',
        'optimized_components_index',
        'optimized_suppliers'
    ]
    
    for pattern in patterns_to_clear:
        try:
            cache.delete(pattern)
        except:
            pass  # Continue if deletion fails
    
    # Clear specific component cache if ID provided
    if component_id:
        try:
            cache.delete(f'component_detail_{component_id}')
        except:
            pass

def warm_cache(cache, db):
    """Pre-populate frequently accessed cache entries"""
    from app.models import ComponentType, Supplier, Category, Brand, ComponentBrand, Component
    from sqlalchemy import func
    
    try:
        # Warm filter options cache
        component_types = db.session.query(ComponentType).join(Component).distinct().order_by(ComponentType.name).all()
        suppliers = db.session.query(Supplier).join(Component).distinct().order_by(Supplier.supplier_code).all()
        categories = db.session.query(Category).join(Component).distinct().order_by(Category.name).all()
        brands = db.session.query(Brand).join(ComponentBrand).join(Component).distinct().order_by(Brand.name).all()
        
        filter_options = {
            'component_types': component_types,
            'suppliers': suppliers,
            'categories': categories,
            'brands': brands,
            'brands_count': len(brands)
        }
        
        cache.set('filter_options', filter_options, timeout=600)
        
        # Warm dashboard stats cache
        stats = db.session.query(
            func.count(Component.id).label('total_components'),
            func.count(func.distinct(Component.supplier_id)).label('total_suppliers'),
            func.count(func.distinct(ComponentBrand.brand_id)).label('total_brands'),
            func.sum(func.case([(Component.proto_status == 'ok', 1)], else_=0)).label('approved_components')
        ).outerjoin(ComponentBrand).first()
        
        dashboard_stats = {
            'total_components': stats.total_components or 0,
            'total_suppliers': stats.total_suppliers or 0,
            'total_brands': stats.total_brands or 0,
            'approved_components': stats.approved_components or 0,
        }
        
        cache.set('component_stats', dashboard_stats, timeout=900)
        
        return True
        
    except Exception as e:
        print(f"Error warming cache: {e}")
        return False