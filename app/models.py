# app/models.py - Complete ProductData class with caching

from app import db
from sqlalchemy import text
from math import ceil
from flask import current_app
from functools import wraps
import time
import json
import hashlib
from datetime import datetime, timedelta

# Enhanced in-memory cache with TTL and size limits
class AdvancedCache:
    def __init__(self, max_size=1000, default_ttl=300):
        self.cache = {}
        self.timestamps = {}
        self.access_times = {}
        self.max_size = max_size
        self.default_ttl = default_ttl

    def _generate_key(self, func_name, args, kwargs):
        """Generate cache key from function name and arguments"""
        # Create deterministic key from sorted parameters
        key_data = f"{func_name}:{str(sorted(args))}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_expired(self, key, ttl):
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        return time.time() - self.timestamps[key] > ttl

    def _evict_oldest(self):
        """Remove oldest accessed items if cache is full"""
        if len(self.cache) >= self.max_size:
            # Remove 20% of oldest items
            to_remove = sorted(self.access_times.items(), key=lambda x: x[1])[:self.max_size // 5]
            for key, _ in to_remove:
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
                self.access_times.pop(key, None)

    def get(self, key, ttl=None):
        """Get item from cache"""
        ttl = ttl or self.default_ttl
        if key in self.cache and not self._is_expired(key, ttl):
            self.access_times[key] = time.time()
            return self.cache[key]
        return None

    def set(self, key, value, ttl=None):
        """Set item in cache"""
        self._evict_oldest()
        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.access_times[key] = time.time()

    def clear_pattern(self, pattern):
        """Clear cache entries matching pattern"""
        keys_to_remove = [key for key in self.cache.keys() if pattern in key]
        for key in keys_to_remove:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
            self.access_times.pop(key, None)

    def get_stats(self):
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_ratio': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1),
            'entries': len(self.cache)
        }

# Global enhanced cache instance
enhanced_cache = AdvancedCache(max_size=500, default_ttl=600)  # 10 minutes default

def smart_cached(ttl=600, cache_key_func=None):
    """Advanced caching decorator with shop-aware keys"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = enhanced_cache._generate_key(f.__name__, args, kwargs)

            # Try to get from cache
            cached_result = enhanced_cache.get(cache_key, ttl)
            if cached_result is not None:
                current_app.logger.debug(f"Cache HIT for {f.__name__}: {cache_key[:16]}")
                return cached_result

            # Execute function and cache result
            current_app.logger.debug(f"Cache MISS for {f.__name__}: {cache_key[:16]}")
            result = f(*args, **kwargs)
            enhanced_cache.set(cache_key, result, ttl)

            return result
        return decorated_function
    return decorator

def shop_cache_key(func_name, shop_ids=None):
    """Generate cache key for shop-specific data"""
    if shop_ids:
        shop_key = '_'.join(map(str, sorted(shop_ids)))
    else:
        shop_key = 'all_shops'
    return f"{func_name}_{shop_key}"

class ProductData:
    """Complete ProductData class with optimized caching and all methods"""

    @staticmethod
    def get_filtered_data(filters):
        """
        Get filtered product data with proper pagination support and caching.

        Args:
            filters (dict): Dictionary of filter criteria including:
                - page: Page number (starts from 1)
                - per_page: Results per page
                - search_term: Search across multiple fields including variant_barcode

        Returns:
            dict: {
                'data': List of product dictionaries,
                'pagination': {
                    'page': current page,
                    'per_page': results per page,
                    'total': total records,
                    'pages': total pages,
                    'has_prev': boolean,
                    'has_next': boolean,
                    'prev_page': previous page number,
                    'next_page': next page number
                }
            }
        """

        # PAGINATION PARAMETERS
        page = filters.get('page', 1)
        per_page = filters.get('per_page', 50)

        # Ensure minimum values
        page = max(1, int(page))
        per_page = min(max(10, int(per_page)), 200)  # Limit max per_page to 200

        # Create cache key for this specific query
        filter_key = json.dumps(filters, sort_keys=True, default=str)
        cache_key = f"filtered_data_{hashlib.md5(filter_key.encode()).hexdigest()}"

        # Try to get from cache (shorter TTL for dynamic queries)
        cached_result = enhanced_cache.get(cache_key, ttl=180)  # 3 minutes cache
        if cached_result is not None:
            current_app.logger.debug(f"Cache hit for filtered data query")
            return cached_result

        # BASE QUERY
        base_query = """
            SELECT 
                ordinal_number,
                shop_technical_name,
                shop_technical_id,
                id as product_id,
                handle,
                title,
                body_html,
                vendor,
                type,
                tags,
                created_at,
                updated_at,
                status,
                image_type,
                image_src,
                variant_id,
                size,
                color,
                material,
                variant_sku,
                variant_barcode,
                variant_image,
                variant_weight,
                variant_inventory_policy,
                variant_available_for_sale,
                variant_inventory_quantity,
                variant_fulfillment_service,
                variant_inventory_management,
                variant_created_at,
                variant_updated_at,
                "Metafield: custom.deals",
                "Metafield: custom.categories",
                "Metafield: Google Product Category",
                "Metafield: collar",
                "Metafield: multipack",
                "Metafield: lining",
                "Metafield: gender",
                "Metafield: trousers_rise",
                "Metafield: pattern",
                "Metafield: occasion_2",
                "Metafield: keyword",
                "Metafield: description_tag",
                "Metafield: google_product_category",
                "Metafield: occasion",
                "Metafield: type_of_heel",
                "Metafield: shoe_tip",
                "Metafield: fit",
                "Metafield: article_code1",
                "Metafield: title_tag",
                "Metafield: dimensions",
                "Metafield: fastener",
                "Metafield: condition",
                "Metafield: sleeve_type",
                "Metafield: age_group",
                "Metafield: pattern_2",
                "Metafield: occasion_3",
                "Metafield: length",
                "Metafield: special_fit"
            FROM catalogue.all_shops_product_data_extended
        """

        # COUNT QUERY for pagination
        count_query = "SELECT COUNT(*) FROM catalogue.all_shops_product_data_extended"

        # DYNAMIC WHERE CLAUSE BUILDING
        where_conditions = []
        params = {}

        # SHOP FILTER
        if filters.get('shop_ids'):
            shop_ids = filters['shop_ids']
            placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
            where_conditions.append(f"shop_technical_id IN ({placeholders})")
            for i, shop_id in enumerate(shop_ids):
                params[f'shop_id_{i}'] = shop_id

        # STATUS FILTER
        if filters.get('status'):
            where_conditions.append("UPPER(status) = UPPER(:status)")
            params['status'] = filters['status']

        # VENDOR FILTER
        if filters.get('vendors'):
            vendors = filters['vendors']
            placeholders = ','.join([':vendor_%d' % i for i in range(len(vendors))])
            where_conditions.append(f"vendor IN ({placeholders})")
            for i, vendor in enumerate(vendors):
                params[f'vendor_{i}'] = vendor

        # PRODUCT TYPE FILTER
        if filters.get('product_types'):
            types = filters['product_types']
            placeholders = ','.join([':type_%d' % i for i in range(len(types))])
            where_conditions.append(f"type IN ({placeholders})")
            for i, ptype in enumerate(types):
                params[f'type_{i}'] = ptype

        # INVENTORY FILTERS
        if filters.get('inventory_tracked_only'):
            where_conditions.append("variant_inventory_management IS NOT NULL")

        if filters.get('zero_inventory'):
            where_conditions.append("variant_inventory_quantity = 0")

        if filters.get('low_stock_threshold'):
            where_conditions.append("variant_inventory_quantity <= :low_stock")
            params['low_stock'] = int(filters['low_stock_threshold'])

        if filters.get('available_for_sale_only'):
            where_conditions.append("variant_available_for_sale = true")

        if filters.get('non_shopify_inventory_management'):
            where_conditions.append("variant_inventory_management != 'SHOPIFY'")

        # MISSING DATA FILTERS
        if filters.get('missing_sku'):
            where_conditions.append("(variant_sku IS NULL OR variant_sku = '')")

        if filters.get('missing_barcode'):
            where_conditions.append("(variant_barcode IS NULL OR variant_barcode = '')")

        if filters.get('missing_images'):
            where_conditions.append("(image_src IS NULL OR image_src = '') AND (variant_image IS NULL OR variant_image = '')")

        if filters.get('missing_title_tag'):
            where_conditions.append('("Metafield: title_tag" IS NULL OR "Metafield: title_tag" = \'\')')

        if filters.get('missing_description_tag'):
            where_conditions.append('("Metafield: description_tag" IS NULL OR "Metafield: description_tag" = \'\')')

        # DATE FILTERS
        if filters.get('created_days_ago'):
            where_conditions.append("created_at >= CURRENT_DATE - INTERVAL ':days days'")
            params['days'] = int(filters['created_days_ago'])

        if filters.get('updated_days_ago'):
            where_conditions.append("updated_at >= CURRENT_DATE - INTERVAL ':days_updated days'")
            params['days_updated'] = int(filters['updated_days_ago'])

        # DATE FILTERS - Enhanced with more options
        if filters.get('created_after'):
            where_conditions.append("created_at >= :created_after")
            params['created_after'] = filters['created_after']

        if filters.get('created_before'):
            where_conditions.append("created_at <= :created_before")
            params['created_before'] = filters['created_before']

        if filters.get('updated_after'):
            where_conditions.append("updated_at >= :updated_after")
            params['updated_after'] = filters['updated_after']

        if filters.get('updated_before'):
            where_conditions.append("updated_at <= :updated_before")
            params['updated_before'] = filters['updated_before']

        # Legacy date filters (keep for backward compatibility)
        if filters.get('created_days_ago'):
            where_conditions.append("created_at >= CURRENT_DATE - INTERVAL ':days days'")
            params['days'] = int(filters['created_days_ago'])

        if filters.get('updated_days_ago'):
            where_conditions.append("updated_at >= CURRENT_DATE - INTERVAL ':days_updated days'")
            params['days_updated'] = int(filters['updated_days_ago'])

        # IMPROVED SEARCH FILTER - Now includes variant_barcode
        if filters.get('search_term'):
            search_conditions = [
                "title ILIKE :search",
                "handle ILIKE :search",
                "variant_sku ILIKE :search",
                "variant_barcode ILIKE :search",
                "vendor ILIKE :search",
                "type ILIKE :search",
                "id::text = :search_exact"  # Exact ID match
            ]
            where_conditions.append(f"({' OR '.join(search_conditions)})")
            params['search'] = f"%{filters['search_term']}%"
            params['search_exact'] = filters['search_term']

        # BUILD FINAL QUERIES
        where_clause = ""
        if where_conditions:
            where_clause = " WHERE " + " AND ".join(where_conditions)

        try:
            # GET TOTAL COUNT FIRST
            count_sql = count_query + where_clause
            count_result = db.session.execute(text(count_sql), params)
            total_records = count_result.scalar()

            # CALCULATE PAGINATION INFO
            total_pages = ceil(total_records / per_page) if total_records > 0 else 1
            page = min(page, total_pages)  # Don't exceed max pages

            offset = (page - 1) * per_page

            # BUILD DATA QUERY WITH PAGINATION
            data_query = base_query + where_clause

            sort_by = filters.get('sort_by', 'default')
            if sort_by == 'created_desc':
                data_query += " ORDER BY created_at DESC, title"
            elif sort_by == 'created_asc':
                data_query += " ORDER BY created_at ASC, title"
            elif sort_by == 'updated_desc':
                data_query += " ORDER BY updated_at DESC, title"
            elif sort_by == 'updated_asc':
                data_query += " ORDER BY updated_at ASC, title"
            else:
                data_query += " ORDER BY shop_technical_name, title, variant_id"

            data_query += f" LIMIT {per_page} OFFSET {offset}"

            # EXECUTE DATA QUERY
            result = db.session.execute(text(data_query), params)
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result]

            # BUILD PAGINATION INFO
            pagination = {
                'page': page,
                'per_page': per_page,
                'total': total_records,
                'pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages,
                'prev_page': page - 1 if page > 1 else None,
                'next_page': page + 1 if page < total_pages else None,
                'offset': offset,
                'showing_from': offset + 1 if total_records > 0 else 0,
                'showing_to': min(offset + per_page, total_records)
            }

            result_data = {
                'data': data,
                'pagination': pagination
            }

            # Cache the result
            enhanced_cache.set(cache_key, result_data, ttl=180)

            return result_data

        except Exception as e:
            current_app.logger.error(f"Error in get_filtered_data: {str(e)}")
            return {'data': [], 'pagination': {'page': 1, 'per_page': per_page, 'total': 0, 'pages': 0}}

    @staticmethod
    @smart_cached(ttl=300)
    def search_variants_by_barcode(barcode):
        """
        Quick search specifically for variant barcode.

        Args:
            barcode (str): Variant barcode to search for

        Returns:
            list: Matching variants
        """
        try:
            query = text("""
                SELECT variant_id, variant_sku, variant_barcode, title, handle, shop_technical_name
                FROM catalogue.all_shops_product_data_extended
                WHERE variant_barcode ILIKE :barcode
                ORDER BY shop_technical_name, title
                LIMIT 50
            """)

            result = db.session.execute(query, {'barcode': f'%{barcode}%'})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            current_app.logger.error(f"Error in search_variants_by_barcode: {str(e)}")
            return []

    @staticmethod
    @smart_cached(ttl=600)
    def get_variant_details(variant_id):
        """
        Get detailed information for a specific variant.

        Args:
            variant_id (int): Variant ID to get details for

        Returns:
            dict: Variant details or None if not found
        """
        try:
            query = text("""
                SELECT *
                FROM catalogue.all_shops_product_data_extended
                WHERE variant_id = :variant_id
            """)

            result = db.session.execute(query, {'variant_id': variant_id})
            row = result.fetchone()

            if row:
                columns = result.keys()
                return dict(zip(columns, row))
            return None
        except Exception as e:
            current_app.logger.error(f"Error in get_variant_details: {str(e)}")
            return None

    @staticmethod
    @smart_cached(ttl=1800, cache_key_func=lambda: "all_shops")
    def get_all_shops():
        """Get a list of all available shops"""
        try:
            query = text("""
                SELECT DISTINCT shop_technical_id, shop_technical_name 
                FROM catalogue.all_shops_product_data_extended 
                ORDER BY shop_technical_name
            """)
            result = db.session.execute(query)
            return [{'id': row[0], 'name': row[1]} for row in result]
        except Exception as e:
            current_app.logger.error(f"Error in get_all_shops: {str(e)}")
            return []

    @staticmethod
    @smart_cached(ttl=900)
    def get_vendors(shop_ids=None):
        """Get list of vendors, optionally filtered by shops"""
        try:
            where_clause = ""
            params = {}
            if shop_ids:
                placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
                where_clause = f"WHERE shop_technical_id IN ({placeholders})"
                for i, shop_id in enumerate(shop_ids):
                    params[f'shop_id_{i}'] = shop_id

            query = text(f"""
                SELECT DISTINCT vendor 
                FROM catalogue.all_shops_product_data_extended 
                {where_clause}
                ORDER BY vendor
            """)

            result = db.session.execute(query, params)
            return [row[0] for row in result if row[0]]
        except Exception as e:
            current_app.logger.error(f"Error in get_vendors: {str(e)}")
            return []

    @staticmethod
    @smart_cached(ttl=900)
    def get_product_types(shop_ids=None):
        """Get list of product types, optionally filtered by shops"""
        try:
            where_clause = ""
            params = {}
            if shop_ids:
                placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
                where_clause = f"WHERE shop_technical_id IN ({placeholders})"
                for i, shop_id in enumerate(shop_ids):
                    params[f'shop_id_{i}'] = shop_id

            query = text(f"""
                SELECT DISTINCT type 
                FROM catalogue.all_shops_product_data_extended 
                {where_clause}
                ORDER BY type
            """)

            result = db.session.execute(query, params)
            return [row[0] for row in result if row[0]]
        except Exception as e:
            current_app.logger.error(f"Error in get_product_types: {str(e)}")
            return []

    @staticmethod
    @smart_cached(ttl=600)
    def get_data_health_summary(shop_ids=None):
        """Get summary statistics about data health"""
        try:
            where_clause = ""
            params = {}

            if shop_ids:
                placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
                where_clause = f"WHERE shop_technical_id IN ({placeholders})"
                for i, shop_id in enumerate(shop_ids):
                    params[f'shop_id_{i}'] = shop_id

            query = text(f"""
                SELECT 
                    COUNT(*) as total_variants,
                    COUNT(CASE WHEN variant_sku IS NULL OR variant_sku = '' THEN 1 END) as missing_sku,
                    COUNT(CASE WHEN variant_barcode IS NULL OR variant_barcode = '' THEN 1 END) as missing_barcode,
                    COUNT(CASE WHEN (image_src IS NULL OR image_src = '') AND (variant_image IS NULL OR variant_image = '') THEN 1 END) as missing_images,
                    COUNT(CASE WHEN "Metafield: title_tag" IS NULL OR "Metafield: title_tag" = '' THEN 1 END) as missing_title_tag,
                    COUNT(CASE WHEN "Metafield: description_tag" IS NULL OR "Metafield: description_tag" = '' THEN 1 END) as missing_description_tag,
                    COUNT(CASE WHEN variant_inventory_quantity = 0 THEN 1 END) as zero_inventory,
                    COUNT(CASE WHEN variant_available_for_sale = false THEN 1 END) as unavailable_variants,
                    COUNT(CASE WHEN UPPER(status) = 'DRAFT' THEN 1 END) as draft_products
                FROM catalogue.all_shops_product_data_extended
                {where_clause}
            """)

            result = db.session.execute(query, params)
            row = result.fetchone()
            return dict(zip(result.keys(), row)) if row else {}
        except Exception as e:
            current_app.logger.error(f"Error in get_data_health_summary: {str(e)}")
            return {}

    # NEW ANALYTICS CACHING METHODS

    @staticmethod
    @smart_cached(ttl=900, cache_key_func=lambda shop_ids=None: shop_cache_key('basic_metrics', shop_ids))
    def get_basic_metrics_fast(shop_ids=None):
        """Get basic metrics quickly - optimized for speed."""
        where_clause = ""
        params = {}

        if shop_ids:
            placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
            where_clause = f"WHERE shop_technical_id IN ({placeholders})"
            for i, shop_id in enumerate(shop_ids):
                params[f'shop_id_{i}'] = shop_id

        try:
            query = text(f"""
                SELECT 
                    COUNT(*) as total_variants,
                    COUNT(DISTINCT handle) as total_products,
                    COUNT(DISTINCT shop_technical_id) as total_shops
                FROM catalogue.all_shops_product_data_extended
                {where_clause}
            """)

            result = db.session.execute(query, params)
            row = result.fetchone()

            if row:
                return dict(zip(result.keys(), row))
            return {}

        except Exception as e:
            current_app.logger.error(f"Error in basic metrics: {str(e)}")
            return {}

    @staticmethod
    @smart_cached(ttl=1200, cache_key_func=lambda shop_ids=None: shop_cache_key('core_quality', shop_ids))
    def get_core_quality_metrics(shop_ids=None):
        """Get core quality metrics (SKU, barcode, images) - medium priority loading."""
        where_clause = ""
        params = {}

        if shop_ids:
            placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
            where_clause = f"WHERE shop_technical_id IN ({placeholders})"
            for i, shop_id in enumerate(shop_ids):
                params[f'shop_id_{i}'] = shop_id

        try:
            query = text(f"""
                SELECT 
                    COUNT(CASE WHEN variant_sku IS NULL OR variant_sku = '' THEN 1 END) as missing_sku,
                    COUNT(CASE WHEN variant_barcode IS NULL OR variant_barcode = '' THEN 1 END) as missing_barcode,
                    COUNT(CASE WHEN (image_src IS NULL OR image_src = '') AND (variant_image IS NULL OR variant_image = '') THEN 1 END) as missing_images,
                    COUNT(CASE WHEN variant_inventory_quantity = 0 THEN 1 END) as zero_inventory,
                    COUNT(CASE WHEN UPPER(status) = 'ACTIVE' THEN 1 END) as active_products,
                    COUNT(CASE WHEN UPPER(status) = 'DRAFT' THEN 1 END) as draft_products
                FROM catalogue.all_shops_product_data_extended
                {where_clause}
            """)

            result = db.session.execute(query, params)
            row = result.fetchone()

            if row:
                return dict(zip(result.keys(), row))
            return {}

        except Exception as e:
            current_app.logger.error(f"Error in core quality metrics: {str(e)}")
            return {}

    @staticmethod
    @smart_cached(ttl=1800, cache_key_func=lambda shop_ids=None: shop_cache_key('product_level_metrics', shop_ids))
    def get_product_level_metrics(shop_ids=None):
        """Get product-level metrics (metafields, SEO) - slower loading, longer cache."""
        where_clause = ""
        params = {}

        if shop_ids:
            placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
            where_clause = f"WHERE shop_technical_id IN ({placeholders})"
            for i, shop_id in enumerate(shop_ids):
                params[f'shop_id_{i}'] = shop_id

        try:
            query = text(f"""
                WITH product_summary AS (
                    SELECT DISTINCT 
                        handle,
                        "Metafield: title_tag",
                        "Metafield: description_tag",
                        "Metafield: custom.categories",
                        "Metafield: gender",
                        "Metafield: pattern"
                    FROM catalogue.all_shops_product_data_extended
                    {where_clause}
                )
                SELECT 
                    COUNT(CASE WHEN "Metafield: title_tag" IS NULL OR "Metafield: title_tag" = '' THEN 1 END) as missing_title_tag_products,
                    COUNT(CASE WHEN "Metafield: description_tag" IS NULL OR "Metafield: description_tag" = '' THEN 1 END) as missing_description_tag_products,
                    COUNT(CASE WHEN "Metafield: custom.categories" IS NULL OR "Metafield: custom.categories" = '' THEN 1 END) as missing_categories_products,
                    COUNT(CASE WHEN "Metafield: gender" IS NULL OR "Metafield: gender" = '' THEN 1 END) as missing_gender_products,
                    COUNT(CASE WHEN 
                        ("Metafield: gender" IS NOT NULL AND "Metafield: gender" != '') AND
                        ("Metafield: custom.categories" IS NOT NULL AND "Metafield: custom.categories" != '') AND
                        ("Metafield: pattern" IS NOT NULL AND "Metafield: pattern" != '')
                        THEN 1 END) as rich_content_products
                FROM product_summary
            """)

            result = db.session.execute(query, params)
            row = result.fetchone()

            if row:
                return dict(zip(result.keys(), row))
            return {}

        except Exception as e:
            current_app.logger.error(f"Error in product level metrics: {str(e)}")
            return {}

    @staticmethod
    def get_enhanced_quality_metrics(shop_ids=None):
        """Combined enhanced quality metrics - now uses cached components for speed."""
        try:
            # Get components from cache or compute them
            basic_metrics = ProductData.get_basic_metrics_fast(shop_ids)
            core_metrics = ProductData.get_core_quality_metrics(shop_ids)
            product_metrics = ProductData.get_product_level_metrics(shop_ids)

            # Combine all metrics
            enhanced_metrics = {**basic_metrics, **core_metrics, **product_metrics}

            # Add additional computed fields if needed
            if enhanced_metrics.get('total_variants', 0) > 0:
                enhanced_metrics['missing_weight'] = 0
                enhanced_metrics['missing_vendor'] = 0
                enhanced_metrics['missing_type'] = 0
                enhanced_metrics['null_inventory'] = 0
                enhanced_metrics['unavailable_variants'] = 0

            return enhanced_metrics
        except Exception as e:
            current_app.logger.error(f"Error combining enhanced metrics: {str(e)}")
            return {}

    @staticmethod
    @smart_cached(ttl=3600, cache_key_func=lambda shop_ids=None: shop_cache_key('metafield_analysis', shop_ids))
    def get_comprehensive_metafield_analysis(shop_ids=None):
        """Optimized metafield analysis with individual caching per metafield."""
        where_clause = ""
        params = {}

        if shop_ids:
            placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
            where_clause = f"WHERE shop_technical_id IN ({placeholders})"
            for i, shop_id in enumerate(shop_ids):
                params[f'shop_id_{i}'] = shop_id

        # Get total products count first (cached separately)
        total_products = ProductData._get_total_products_count(shop_ids)

        if total_products == 0:
            return {}

        # All metafields from your original query
        all_metafields = [
            '"Metafield: custom.deals"',
            '"Metafield: custom.categories"',
            '"Metafield: Google Product Category"',
            '"Metafield: collar"',
            '"Metafield: multipack"',
            '"Metafield: lining"',
            '"Metafield: gender"',
            '"Metafield: trousers_rise"',
            '"Metafield: pattern"',
            '"Metafield: occasion_2"',
            '"Metafield: keyword"',
            '"Metafield: description_tag"',
            '"Metafield: google_product_category"',
            '"Metafield: occasion"',
            '"Metafield: type_of_heel"',
            '"Metafield: shoe_tip"',
            '"Metafield: fit"',
            '"Metafield: article_code1"',
            '"Metafield: title_tag"',
            '"Metafield: dimensions"',
            '"Metafield: fastener"',
            '"Metafield: condition"',
            '"Metafield: sleeve_type"',
            '"Metafield: age_group"',
            '"Metafield: pattern_2"',
            '"Metafield: occasion_3"',
            '"Metafield: length"',
            '"Metafield: special_fit"'
        ]

        metafield_completeness = {}

        for col in all_metafields:
            try:
                completed_count = ProductData._get_metafield_completion_count(col, where_clause, params)

                # Calculate percentage
                percentage = round((completed_count / total_products) * 100, 2) if total_products > 0 else 0

                # Clean field name for display
                field_key = col.replace('"', '')
                display_name = field_key.replace('Metafield: ', '')

                metafield_completeness[field_key] = {
                    'count': completed_count,
                    'percentage': percentage,
                    'display_name': display_name,
                    'total_products': total_products,
                    'priority': get_metafield_priority(display_name)
                }

            except Exception as e:
                current_app.logger.error(f"Error analyzing metafield {col}: {str(e)}")
                continue

        return metafield_completeness

    @staticmethod
    @smart_cached(ttl=1800, cache_key_func=lambda shop_ids=None: shop_cache_key('total_products', shop_ids))
    def _get_total_products_count(shop_ids=None):
        """Cache total products count separately for reuse"""
        where_clause = ""
        params = {}

        if shop_ids:
            placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
            where_clause = f"WHERE shop_technical_id IN ({placeholders})"
            for i, shop_id in enumerate(shop_ids):
                params[f'shop_id_{i}'] = shop_id

        try:
            count_query = f"""
                SELECT COUNT(DISTINCT handle) as total_products
                FROM catalogue.all_shops_product_data_extended
                {where_clause}
            """

            result = db.session.execute(text(count_query), params)
            return result.scalar() or 0
        except Exception as e:
            current_app.logger.error(f"Error getting total products count: {str(e)}")
            return 0

    @staticmethod
    def _get_metafield_completion_count(metafield_col, where_clause, params):
        """Get completion count for a single metafield with caching"""
        cache_key = f"metafield_{metafield_col}_{hash(str(params))}"

        cached_result = enhanced_cache.get(cache_key, ttl=1800)
        if cached_result is not None:
            return cached_result

        try:
            metafield_query = f"""
                SELECT COUNT(DISTINCT handle) as completed_products
                FROM catalogue.all_shops_product_data_extended
                {where_clause}
                {"AND" if where_clause else "WHERE"} {metafield_col} IS NOT NULL 
                AND TRIM(CAST({metafield_col} AS TEXT)) != ''
            """

            result = db.session.execute(text(metafield_query), params)
            count = result.scalar() or 0

            enhanced_cache.set(cache_key, count, ttl=1800)
            return count
        except Exception as e:
            current_app.logger.error(f"Error getting metafield completion count for {metafield_col}: {str(e)}")
            return 0

    @staticmethod
    @smart_cached(ttl=600, cache_key_func=lambda: "shop_statistics")
    def get_shop_statistics():
        """Get product and variant counts for each shop with caching."""
        try:
            query = text("""
                SELECT 
                    shop_technical_id,
                    shop_technical_name,
                    COUNT(DISTINCT id) as product_count,
                    COUNT(*) as variant_count,
                    COUNT(CASE WHEN UPPER(status) = 'ACTIVE' THEN 1 END) as active_variants,
                    COUNT(CASE WHEN variant_inventory_quantity = 0 THEN 1 END) as zero_inventory,
                    COUNT(CASE WHEN variant_sku IS NULL OR variant_sku = '' THEN 1 END) as missing_sku
                FROM catalogue.all_shops_product_data_extended
                GROUP BY shop_technical_id, shop_technical_name
                ORDER BY shop_technical_name
            """)

            result = db.session.execute(query)
            columns = result.keys()

            # Convert to dictionary for easy lookup
            stats = {}
            for row in result:
                row_dict = dict(zip(columns, row))
                shop_id = row_dict['shop_technical_id']
                stats[shop_id] = {
                    'id': shop_id,
                    'name': row_dict['shop_technical_name'],
                    'product_count': row_dict['product_count'],
                    'variant_count': row_dict['variant_count'],
                    'active_variants': row_dict['active_variants'],
                    'zero_inventory': row_dict['zero_inventory'],
                    'missing_sku': row_dict['missing_sku'],
                    'health_score': round(
                        (row_dict['active_variants'] / row_dict['variant_count'] * 100)
                        if row_dict['variant_count'] > 0 else 0, 1
                    )
                }

            return stats
        except Exception as e:
            current_app.logger.error(f"Error in get_shop_statistics: {str(e)}")
            return {}

    @staticmethod
    @smart_cached(ttl=300, cache_key_func=lambda: "shop_health_summary")
    def get_shop_health_summary():
        """Get overall health summary across all shops"""
        try:
            query = text("""
            SELECT 
                COUNT(DISTINCT shop_technical_id) as total_shops,
                COUNT(DISTINCT handle) as total_products,
                COUNT(DISTINCT variant_barcode) as total_variants,
                COUNT(DISTINCT CASE WHEN UPPER(status) = 'ACTIVE' THEN variant_barcode END) as active_variants,
                COUNT(DISTINCT CASE WHEN variant_inventory_quantity > 0 THEN variant_barcode END) as in_stock_variants
            FROM catalogue.all_shops_product_data_extended
            WHERE variant_barcode IS NOT NULL AND variant_barcode != ''
        """)

            result = db.session.execute(query)
            row = result.fetchone()

            if row:
                columns = result.keys()
                summary = dict(zip(columns, row))

                # Calculate percentages
                summary['active_percentage'] = round(
                    (summary['active_variants'] / summary['total_variants'] * 100)
                    if summary['total_variants'] > 0 else 0, 1
                )
                summary['stock_percentage'] = round(
                    (summary['in_stock_variants'] / summary['total_variants'] * 100)
                    if summary['total_variants'] > 0 else 0, 1
                )

                return summary

            return {}
        except Exception as e:
            current_app.logger.error(f"Error in get_shop_health_summary: {str(e)}")
            return {}

    # CACHE MANAGEMENT METHODS

    @staticmethod
    def clear_analytics_cache(shop_ids=None):
        """Clear analytics-related cache entries"""
        if shop_ids:
            shop_key = '_'.join(map(str, sorted(shop_ids)))
            enhanced_cache.clear_pattern(shop_key)
        else:
            # Clear all analytics cache
            patterns = ['basic_metrics', 'core_quality', 'product_level_metrics', 'metafield_analysis', 'total_products']
            for pattern in patterns:
                enhanced_cache.clear_pattern(pattern)

    @staticmethod
    def clear_products_cache():
        """Clear products page related cache"""
        enhanced_cache.clear_pattern('filtered_data')
        enhanced_cache.clear_pattern('all_shops')
        enhanced_cache.clear_pattern('get_vendors')
        enhanced_cache.clear_pattern('get_product_types')

    @staticmethod
    def warm_analytics_cache(shop_ids=None):
        """Pre-warm cache with analytics data"""
        try:
            current_app.logger.info(f"Warming analytics cache for shops: {shop_ids}")

            # Warm basic metrics first
            ProductData.get_basic_metrics_fast(shop_ids)

            # Warm core metrics
            ProductData.get_core_quality_metrics(shop_ids)

            # Warm product level metrics
            ProductData.get_product_level_metrics(shop_ids)

            # Warm metafield analysis (this is the slowest)
            ProductData.get_comprehensive_metafield_analysis(shop_ids)

            current_app.logger.info("Analytics cache warming completed")
            return True
        except Exception as e:
            current_app.logger.error(f"Error warming analytics cache: {str(e)}")
            return False

    @staticmethod
    def get_cache_status():
        """Get cache status and statistics"""
        return {
            'cache_stats': enhanced_cache.get_stats(),
            'cache_size': len(enhanced_cache.cache),
            'timestamp': datetime.now().isoformat()
        };

def get_metafield_priority(field_name):
    """Return priority order for metafield display (lower number = higher priority)"""
    high_priority = ['custom.categories', 'gender', 'title_tag', 'description_tag', 'Google Product Category']
    medium_priority = ['pattern', 'fit', 'material', 'color', 'occasion', 'type_of_heel', 'collar']

    field_lower = field_name.lower()

    for priority_field in high_priority:
        if priority_field.lower() in field_lower:
            return 1

    for priority_field in medium_priority:
        if priority_field.lower() in field_lower:
            return 2

    return 3  # Low priority