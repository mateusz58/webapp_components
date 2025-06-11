# app/routes.py - Fixed with proper pagination handling
import time
from datetime import datetime

import time
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, flash
from sqlalchemy import text

from app import db
from app.models import ProductData, enhanced_cache
from app.utils import export_to_csv, calculate_percentages, get_metafield_completeness, calculate_comprehensive_quality_score, format_metafield_name
import json
from threading import Thread
import asyncio

import hashlib
from threading import Thread
from datetime import datetime

import time
import json
import hashlib
from threading import Thread
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, flash
from app.models import ProductData, enhanced_cache
from app.utils import (
    export_to_csv,
    calculate_percentages,
    get_metafield_completeness,
    calculate_comprehensive_quality_score,
    format_metafield_name
)


main = Blueprint('main', __name__)

@main.route('/')
def index():
    """
    Main dashboard page with shop statistics and caching.
    """
    try:
        # Get basic shop list (fast query)
        shops = ProductData.get_all_shops()

        # Get detailed shop statistics (cached)
        shop_stats = ProductData.get_shop_statistics()

        # Get overall health summary (cached)
        health_summary = ProductData.get_shop_health_summary()

        # Merge shop data with statistics
        enhanced_shops = []
        for shop in shops:
            shop_data = shop.copy()

            # Add statistics if available
            if shop['id'] in shop_stats:
                stats = shop_stats[shop['id']]
                shop_data.update({
                    'product_count': stats['product_count'],
                    'variant_count': stats['variant_count'],
                    'active_variants': stats['active_variants'],
                    'zero_inventory': stats['zero_inventory'],
                    'missing_sku': stats['missing_sku'],
                    'health_score': stats['health_score']
                })
            else:
                # Default values if no stats available
                shop_data.update({
                    'product_count': 0,
                    'variant_count': 0,
                    'active_variants': 0,
                    'zero_inventory': 0,
                    'missing_sku': 0,
                    'health_score': 0
                })

            enhanced_shops.append(shop_data)

        return render_template('index.html',
                               shops=enhanced_shops,
                               health_summary=health_summary)

    except Exception as e:
        # Fallback to basic shop list if statistics fail
        current_app.logger.error(f"Error loading shop statistics: {str(e)}")
        shops = ProductData.get_all_shops()

        # Add empty stats
        for shop in shops:
            shop.update({
                'product_count': 0,
                'variant_count': 0,
                'active_variants': 0,
                'zero_inventory': 0,
                'missing_sku': 0,
                'health_score': 0
            })

        return render_template('index.html',
                               shops=shops,
                               health_summary={})


# Add API endpoint for refreshing cache
@main.route('/api/refresh-shop-stats', methods=['POST'])
def refresh_shop_stats():
    """API endpoint to refresh shop statistics cache"""
    try:
        ProductData.clear_shop_cache()

        # Warm up the cache with fresh data
        ProductData.get_shop_statistics()
        ProductData.get_shop_health_summary()

        return jsonify({
            'success': True,
            'message': 'Shop statistics cache refreshed successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# @main.route('/api/cache-status')
# def cache_status():
#     """Get cache status information"""
#     current_time = time.time()
#
#     cache_info = {}
#     for key, timestamp in _cache_timestamps.items():
#         age = current_time - timestamp
#         cache_info[key] = {
#             'age_seconds': round(age, 2),
#             'age_minutes': round(age / 60, 2),
#             'size_bytes': len(str(_cache.get(key, '')))
#         }
#
#     return jsonify({
#         'total_entries': len(_cache),
#         'entries': cache_info
#     })

@main.route('/products')
def products():
    """
    Enhanced products listing page with caching and responsive pagination.
    """
    start_time = time.time()

    # EXTRACT PAGINATION PARAMETERS
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Ensure reasonable limits
    per_page = min(max(10, per_page), 200)
    page = max(1, page)

    shop_ids = request.args.getlist('shop_ids[]', type=int)
    if not shop_ids:
        single_shop_id = request.args.get('shop_ids', type=int)
        if single_shop_id:
            shop_ids = [single_shop_id]

    # EXTRACT FILTER PARAMETERS
    filters = {
        # Pagination
        'page': page,
        'per_page': per_page,

        # Basic filters
        'shop_ids': request.args.getlist('shop_ids[]', type=int),
        'status': request.args.get('status'),
        'vendors': request.args.getlist('vendors[]'),
        'product_types': request.args.getlist('product_types[]'),
        'search_term': request.args.get('search_term')
    }

    # INVENTORY FILTERS
    if request.args.get('inventory_tracked_only'):
        filters['inventory_tracked_only'] = True
    if request.args.get('zero_inventory'):
        filters['zero_inventory'] = True
    if request.args.get('low_stock_threshold'):
        filters['low_stock_threshold'] = request.args.get('low_stock_threshold', type=int)
    if request.args.get('available_for_sale_only'):
        filters['available_for_sale_only'] = True
    if request.args.get('non_shopify_inventory_management'):
        filters['non_shopify_inventory_management'] = True

    # MISSING DATA FILTERS
    if request.args.get('missing_sku'):
        filters['missing_sku'] = True
    if request.args.get('missing_barcode'):
        filters['missing_barcode'] = True
    if request.args.get('missing_images'):
        filters['missing_images'] = True
    if request.args.get('missing_title_tag'):
        filters['missing_title_tag'] = True
    if request.args.get('missing_description_tag'):
        filters['missing_description_tag'] = True

    # DATE FILTERS
    if request.args.get('created_after'):
        filters['created_after'] = request.args.get('created_after')
    if request.args.get('created_before'):
        filters['created_before'] = request.args.get('created_before')
    if request.args.get('updated_after'):
        filters['updated_after'] = request.args.get('updated_after')
    if request.args.get('updated_before'):
        filters['updated_before'] = request.args.get('updated_before')

    # Sorting
    if request.args.get('sort_by'):
        filters['sort_by'] = request.args.get('sort_by')

    # Legacy date filters (keep existing)
    if request.args.get('created_days_ago'):
        filters['created_days_ago'] = request.args.get('created_days_ago', type=int)
    if request.args.get('updated_days_ago'):
        filters['updated_days_ago'] = request.args.get('updated_days_ago', type=int)

    # CLEAN UP FILTERS
    filters = {k: v for k, v in filters.items() if v is not None and v != '' and v != []}

    try:
        # GET PAGINATED DATA (now with caching)
        result = ProductData.get_filtered_data(filters)
        products = result['data']
        pagination = result['pagination']

        # GET DATA FOR FILTER DROPDOWNS (cached)
        shops = ProductData.get_all_shops()
        all_vendors = ProductData.get_vendors()
        all_types = ProductData.get_product_types()

        load_time = time.time() - start_time
        current_app.logger.info(f"Products page loaded in {load_time:.2f}s")

        # RENDER TEMPLATE WITH PAGINATION DATA
        return render_template('products.html',
                               products=products,
                               pagination=pagination,
                               shops=shops,
                               vendors=all_vendors,
                               product_types=all_types,
                               filters=request.args,
                               total_results=pagination['total'],
                               load_time=load_time)

    except Exception as e:
        current_app.logger.error(f"Error in products route: {str(e)}")
        flash(f"Error loading products: {str(e)}", 'error')

        # Fallback with empty data
        return render_template('products.html',
                               products=[],
                               pagination={'page': 1, 'per_page': 50, 'total': 0, 'pages': 0},
                               shops=[],
                               vendors=[],
                               product_types=[],
                               filters=request.args,
                               total_results=0,
                               load_time=0)
@main.route('/export')
def export_products():
    """Enhanced export with better performance and caching"""
    start_time = time.time()

    # Get all current filters but remove pagination for export
    filters = {
        'shop_ids': request.args.getlist('shop_ids[]', type=int),
        'status': request.args.get('status'),
        'vendors': request.args.getlist('vendors[]'),
        'product_types': request.args.getlist('product_types[]'),
        'search_term': request.args.get('search_term'),
        'per_page': 5000  # Higher limit for export, but still reasonable
    }

    # Apply same filter logic as products route
    if request.args.get('inventory_tracked_only'):
        filters['inventory_tracked_only'] = True
    if request.args.get('zero_inventory'):
        filters['zero_inventory'] = True
    if request.args.get('low_stock_threshold'):
        filters['low_stock_threshold'] = request.args.get('low_stock_threshold', type=int)
    if request.args.get('available_for_sale_only'):
        filters['available_for_sale_only'] = True
    if request.args.get('missing_sku'):
        filters['missing_sku'] = True
    if request.args.get('missing_barcode'):
        filters['missing_barcode'] = True
    if request.args.get('missing_images'):
        filters['missing_images'] = True
    if request.args.get('missing_title_tag'):
        filters['missing_title_tag'] = True
    if request.args.get('missing_description_tag'):
        filters['missing_description_tag'] = True
    if request.args.get('created_days_ago'):
        filters['created_days_ago'] = request.args.get('created_days_ago', type=int)
    if request.args.get('updated_days_ago'):
        filters['updated_days_ago'] = request.args.get('updated_days_ago', type=int)

    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v is not None and v != '' and v != []}

    try:
        # GET DATA (cached for performance)
        result = ProductData.get_filtered_data(filters)
        products = result['data']

        if not products:
            flash('No products found matching your criteria', 'warning')
            return redirect(url_for('main.products'))

        # CREATE FILENAME WITH FILTER INFO
        filename_parts = ["products_export"]
        if filters.get('search_term'):
            filename_parts.append(f"search_{filters['search_term'][:20]}")
        if filters.get('shop_ids'):
            filename_parts.append(f"{len(filters['shop_ids'])}shops")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = "_".join(filename_parts) + f"_{timestamp}.csv"

        export_time = time.time() - start_time
        current_app.logger.info(f"Export prepared in {export_time:.2f}s for {len(products)} products")

        return export_to_csv(products, filename)

    except Exception as e:
        current_app.logger.error(f"Error in export: {str(e)}")
        flash(f"Export failed: {str(e)}", 'error')
        return redirect(url_for('main.products'))

@main.route('/api/products/search-suggestions')
def api_product_search_suggestions():
    """API endpoint for search suggestions"""
    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify({'suggestions': []})

    try:
        # Get cached suggestions or generate new ones
        cache_key = f"search_suggestions_{hashlib.md5(query.encode()).hexdigest()}"
        cached_suggestions = enhanced_cache.get(cache_key, ttl=300)  # 5 min cache

        if cached_suggestions is not None:
            return jsonify({'suggestions': cached_suggestions})

        # Generate suggestions based on actual data
        suggestions_query = text("""
            SELECT DISTINCT 
                CASE 
                    WHEN variant_sku ILIKE :query THEN 'SKU: ' || variant_sku
                    WHEN variant_barcode ILIKE :query THEN 'Barcode: ' || variant_barcode
                    WHEN title ILIKE :query THEN 'Product: ' || title
                    WHEN vendor ILIKE :query THEN 'Vendor: ' || vendor
                    ELSE 'Search: ' || :raw_query
                END as suggestion
            FROM catalogue.all_shops_product_data_extended
            WHERE variant_sku ILIKE :query 
               OR variant_barcode ILIKE :query 
               OR title ILIKE :query 
               OR vendor ILIKE :query
            LIMIT 5
        """)

        result = db.session.execute(suggestions_query, {
            'query': f'%{query}%',
            'raw_query': query
        })

        suggestions = [row[0] for row in result]

        # Cache the suggestions
        enhanced_cache.set(cache_key, suggestions, ttl=300)

        return jsonify({'suggestions': suggestions})

    except Exception as e:
        current_app.logger.error(f"Error generating search suggestions: {str(e)}")
        return jsonify({'suggestions': []})

@main.route('/api/products/quick-stats')
def api_products_quick_stats():
    """API endpoint for quick product statistics"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        # Use cached basic metrics
        basic_stats = ProductData.get_basic_metrics_fast(shop_ids if shop_ids else None)
        core_stats = ProductData.get_core_quality_metrics(shop_ids if shop_ids else None)

        combined_stats = {**basic_stats, **core_stats}

        return jsonify({
            'success': True,
            'data': combined_stats
        })

    except Exception as e:
        current_app.logger.error(f"Error in quick stats API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/cache/clear-products', methods=['POST'])
def api_clear_products_cache():
    """API endpoint to clear products-specific cache"""
    try:
        ProductData.clear_products_cache()

        return jsonify({
            'success': True,
            'message': 'Products cache cleared successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/cache/warm-products', methods=['POST'])
def api_warm_products_cache():
    """API endpoint to warm products cache"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        def warm_products_cache():
            # Warm common queries
            ProductData.get_all_shops()
            ProductData.get_vendors(shop_ids if shop_ids else None)
            ProductData.get_product_types(shop_ids if shop_ids else None)

            # Warm common filter combinations
            common_filters = [
                {'page': 1, 'per_page': 50},
                {'page': 1, 'per_page': 100},
                {'missing_sku': True, 'page': 1, 'per_page': 50},
                {'zero_inventory': True, 'page': 1, 'per_page': 50},
            ]

            if shop_ids:
                for filters in common_filters:
                    filters['shop_ids'] = shop_ids
                    try:
                        ProductData.get_filtered_data(filters)
                    except:
                        pass  # Continue warming other filters

        # Start warming in background
        Thread(target=warm_products_cache).start()

        return jsonify({
            'success': True,
            'message': 'Products cache warming started'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/products/performance')
def api_products_performance():
    """API endpoint for products page performance metrics"""
    try:
        # Test query performance
        start_time = time.time()

        # Test basic shop loading
        shops = ProductData.get_all_shops()
        shop_load_time = time.time() - start_time

        # Test simple product query
        start_time = time.time()
        simple_filters = {'page': 1, 'per_page': 25}
        result = ProductData.get_filtered_data(simple_filters)
        query_time = time.time() - start_time

        # Cache statistics
        cache_stats = enhanced_cache.get_stats()

        return jsonify({
            'success': True,
            'performance': {
                'shop_load_time': round(shop_load_time, 3),
                'simple_query_time': round(query_time, 3),
                'total_products_cached': len(result['data']),
                'cache_hit_ratio': cache_stats.get('hit_ratio', 0),
                'cache_size': cache_stats.get('size', 0)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/analytics')
def analytics():
    """
    Optimized analytics dashboard with progressive loading.
    Loads basic metrics immediately, then progressively loads detailed data.
    """
    shop_ids = request.args.getlist('shop_ids[]', type=int)
    show_by_shop = request.args.get('by_shop', False, type=bool)

    # Start timing for performance monitoring
    start_time = time.time()

    # Initialize with fast-loading basic data only
    basic_metrics = {}
    shops = []
    error_messages = []

    try:
        # Get basic metrics immediately (cached, very fast)
        basic_metrics = ProductData.get_basic_metrics_fast(shop_ids if shop_ids else None)
        current_app.logger.info(f"Basic metrics loaded in {time.time() - start_time:.2f}s")
    except Exception as e:
        current_app.logger.error(f"Error getting basic metrics: {str(e)}")
        error_messages.append("Unable to load basic metrics")
        basic_metrics = {}

    try:
        # Get shops for filter (should be fast)
        shops = ProductData.get_all_shops()
    except Exception as e:
        current_app.logger.error(f"Error getting shops: {str(e)}")
        shops = []
        error_messages.append("Unable to load shop list")

    # Determine if we have sufficient data to show analytics
    has_data = bool(basic_metrics.get('total_variants', 0) > 0)

    # Add error messages to flash if any occurred
    for error in error_messages:
        flash(error, 'warning')

    # Trigger background cache warming for this shop combination
    if has_data:
        Thread(target=ProductData.warm_analytics_cache, args=(shop_ids if shop_ids else None,)).start()

    # Log performance
    total_time = time.time() - start_time
    current_app.logger.info(f"Analytics page loaded in {total_time:.2f}s")

    return render_template('analytics.html',
                           basic_metrics=basic_metrics,
                           shops=shops,
                           selected_shops=shop_ids,
                           show_by_shop=show_by_shop,
                           has_data=has_data,
                           error_messages=error_messages,
                           loading_mode=True)  # Flag to indicate progressive loading

@main.route('/api/analytics/core-metrics')
def api_core_metrics():
    """API endpoint for loading core quality metrics (SKU, barcode, images)"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        start_time = time.time()
        core_metrics = ProductData.get_core_quality_metrics(shop_ids if shop_ids else None)

        current_app.logger.info(f"Core metrics API loaded in {time.time() - start_time:.2f}s")

        return jsonify({
            'success': True,
            'data': core_metrics,
            'load_time': round(time.time() - start_time, 2)
        })

    except Exception as e:
        current_app.logger.error(f"Error in core metrics API: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Core metrics failed: {str(e)}'
        }), 500

@main.route('/api/analytics/product-metrics')
def api_product_metrics():
    """API endpoint for loading product-level metrics (metafields, SEO)"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        start_time = time.time()
        product_metrics = ProductData.get_product_level_metrics(shop_ids if shop_ids else None)

        current_app.logger.info(f"Product metrics API loaded in {time.time() - start_time:.2f}s")

        return jsonify({
            'success': True,
            'data': product_metrics,
            'load_time': round(time.time() - start_time, 2)
        })

    except Exception as e:
        current_app.logger.error(f"Error in product metrics API: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Product metrics failed: {str(e)}'
        }), 500

@main.route('/api/analytics/metafield-analysis')
def api_metafield_analysis():
    """API endpoint for loading comprehensive metafield analysis"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        start_time = time.time()
        metafield_completeness = ProductData.get_comprehensive_metafield_analysis(shop_ids if shop_ids else None)

        # Format metafield names for better display
        formatted_metafields = {}
        for field_name, data in metafield_completeness.items():
            formatted_name = format_metafield_name(field_name)
            formatted_metafields[field_name] = {
                **data,
                'formatted_name': formatted_name
            }

        current_app.logger.info(f"Metafield analysis API loaded in {time.time() - start_time:.2f}s")

        return jsonify({
            'success': True,
            'data': formatted_metafields,
            'load_time': round(time.time() - start_time, 2)
        })

    except Exception as e:
        current_app.logger.error(f"Error in metafield analysis API: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Metafield analysis failed: {str(e)}'
        }), 500

@main.route('/api/analytics/quality-score')
def api_quality_score():
    """API endpoint for calculating comprehensive quality score"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        start_time = time.time()

        # Get enhanced metrics (combines cached components)
        enhanced_metrics = ProductData.get_enhanced_quality_metrics(shop_ids if shop_ids else None)

        # Get metafield analysis
        metafield_completeness = ProductData.get_comprehensive_metafield_analysis(shop_ids if shop_ids else None)

        # Calculate quality score
        quality_analysis = calculate_comprehensive_quality_score(enhanced_metrics, metafield_completeness)

        current_app.logger.info(f"Quality score API loaded in {time.time() - start_time:.2f}s")

        return jsonify({
            'success': True,
            'data': {
                'enhanced_metrics': enhanced_metrics,
                'quality_analysis': quality_analysis
            },
            'load_time': round(time.time() - start_time, 2)
        })

    except Exception as e:
        current_app.logger.error(f"Error in quality score API: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Quality score calculation failed: {str(e)}'
        }), 500

@main.route('/api/cache/warm', methods=['POST'])
def api_warm_cache():
    """API endpoint to warm up analytics cache"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        start_time = time.time()

        # Start cache warming in background
        def warm_cache_background():
            return ProductData.warm_analytics_cache(shop_ids if shop_ids else None)

        # For immediate response, start warming and return
        Thread(target=warm_cache_background).start()

        return jsonify({
            'success': True,
            'message': 'Cache warming started in background',
            'estimated_time': '30-60 seconds'
        })

    except Exception as e:
        current_app.logger.error(f"Error starting cache warm: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/cache/clear', methods=['POST'])
def api_clear_cache():
    """API endpoint to clear analytics cache"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        ProductData.clear_analytics_cache(shop_ids if shop_ids else None)

        return jsonify({
            'success': True,
            'message': 'Analytics cache cleared successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/cache/status')
def api_cache_status():
    """Get cache status and performance metrics"""
    try:
        cache_status = ProductData.get_cache_status()
        return jsonify({
            'success': True,
            'data': cache_status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add this new route for shop comparison
@main.route('/analytics/shops')
def analytics_by_shops():
    """Analytics dashboard showing metafield completeness by individual shops"""
    return redirect(url_for('main.analytics', by_shop=True))

# Update the API endpoint for better error handling
@main.route('/api/quality-analysis')
def api_quality_analysis():
    """Optimized API endpoint for fetching complete quality analysis data"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        start_time = time.time()

        # Use the optimized enhanced metrics method
        enhanced_metrics = ProductData.get_enhanced_quality_metrics(shop_ids if shop_ids else None)

        if not enhanced_metrics:
            return jsonify({
                'success': False,
                'error': 'No data found for selected shops'
            }), 404

        # Get metafield analysis (cached)
        metafield_completeness = ProductData.get_comprehensive_metafield_analysis(shop_ids if shop_ids else None)

        # Calculate quality score
        quality_analysis = calculate_comprehensive_quality_score(enhanced_metrics, metafield_completeness)

        load_time = time.time() - start_time
        current_app.logger.info(f"Complete quality analysis loaded in {load_time:.2f}s")

        return jsonify({
            'success': True,
            'data': {
                'enhanced_metrics': enhanced_metrics,
                'metafield_completeness': metafield_completeness,
                'quality_analysis': quality_analysis
            },
            'load_time': round(load_time, 2)
        })

    except Exception as e:
        current_app.logger.error(f"Error in optimized quality analysis API: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500

@main.route('/api/background/warm-all-shops', methods=['POST'])
def api_warm_all_shops():
    """Background endpoint to warm cache for all shop combinations"""
    try:
        def warm_all_shops():
            # Get all shops
            shops = ProductData.get_all_shops()

            # Warm cache for all shops combined
            ProductData.warm_analytics_cache()

            # Warm cache for individual shops
            for shop in shops:
                ProductData.warm_analytics_cache([shop['id']])
                time.sleep(1)  # Small delay to prevent overwhelming the database

        Thread(target=warm_all_shops).start()

        return jsonify({
            'success': True,
            'message': 'Background cache warming started for all shops'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/performance/metrics')
def api_performance_metrics():
    """Get performance metrics for analytics queries"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    performance_data = {}

    # Test basic metrics performance
    start_time = time.time()
    try:
        ProductData.get_basic_metrics_fast(shop_ids if shop_ids else None)
        performance_data['basic_metrics_time'] = round(time.time() - start_time, 3)
    except:
        performance_data['basic_metrics_time'] = 'error'

    # Test core metrics performance
    start_time = time.time()
    try:
        ProductData.get_core_quality_metrics(shop_ids if shop_ids else None)
        performance_data['core_metrics_time'] = round(time.time() - start_time, 3)
    except:
        performance_data['core_metrics_time'] = 'error'

    # Test metafield analysis performance
    start_time = time.time()
    try:
        ProductData.get_comprehensive_metafield_analysis(shop_ids if shop_ids else None)
        performance_data['metafield_analysis_time'] = round(time.time() - start_time, 3)
    except:
        performance_data['metafield_analysis_time'] = 'error'

    # Add cache statistics
    performance_data['cache_stats'] = enhanced_cache.get_stats()

    return jsonify({
        'success': True,
        'data': performance_data,
        'timestamp': time.time()
    })

# Add debugging endpoint to test metafield queries
@main.route('/api/debug/metafields')
def debug_metafields():
    """Debug endpoint to test metafield queries"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        # Test basic query first
        where_clause = ""
        params = {}

        if shop_ids:
            placeholders = ','.join([':shop_id_%d' % i for i in range(len(shop_ids))])
            where_clause = f"WHERE shop_technical_id IN ({placeholders})"
            for i, shop_id in enumerate(shop_ids):
                params[f'shop_id_{i}'] = shop_id

        # Test count query
        count_query = f"""
            SELECT 
                COUNT(*) as total_variants,
                COUNT(DISTINCT handle) as total_products,
                COUNT(DISTINCT shop_technical_id) as total_shops
            FROM catalogue.all_shops_product_data_extended
            {where_clause}
        """

        result = db.session.execute(text(count_query), params)
        debug_info = dict(zip(result.keys(), result.fetchone()))

        # Test one metafield
        test_metafield = '"Metafield: gender"'
        metafield_query = f"""
            SELECT COUNT(DISTINCT handle) as completed_products
            FROM catalogue.all_shops_product_data_extended
            {where_clause}
            {"AND" if where_clause else "WHERE"} {test_metafield} IS NOT NULL 
            AND TRIM(CAST({test_metafield} AS TEXT)) != ''
        """

        metafield_result = db.session.execute(text(metafield_query), params)
        debug_info['gender_completed'] = metafield_result.scalar()

        return jsonify({
            'success': True,
            'debug_info': debug_info,
            'query_params': params
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'query_params': params
        }), 500

# Add this endpoint for exporting enhanced analytics
@main.route('/api/export-quality-report')
def export_quality_report():
    """Export comprehensive quality report"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    try:
        # Get all the data
        enhanced_metrics = ProductData.get_enhanced_quality_metrics(shop_ids if shop_ids else None)
        metafield_completeness = ProductData.get_comprehensive_metafield_analysis(shop_ids if shop_ids else None)
        quality_analysis = calculate_comprehensive_quality_score(enhanced_metrics, metafield_completeness)

        # Prepare report data
        report_data = []

        # Add summary row
        total_variants = enhanced_metrics.get('total_variants', 0)
        report_data.append({
            'metric_category': 'Summary',
            'metric_name': 'Total Variants',
            'value': total_variants,
            'percentage': 100.0,
            'status': 'info'
        })

        # Add quality factors
        for factor_name, factor_data in quality_analysis.get('breakdown', {}).items():
            for component_name, component_score in factor_data.get('components', {}).items():
                report_data.append({
                    'metric_category': factor_name.replace('_', ' ').title(),
                    'metric_name': component_name.replace('_', ' ').title(),
                    'value': f"{component_score:.1f}%",
                    'percentage': component_score,
                    'status': 'good' if component_score >= 80 else 'fair' if component_score >= 60 else 'poor'
                })

        # Add metafield completeness
        for field_name, field_data in metafield_completeness.items():
            report_data.append({
                'metric_category': 'Metafield Completeness',
                'metric_name': field_data.get('formatted_name', field_name),
                'value': f"{field_data['count']:,} ({field_data['percentage']:.1f}%)",
                'percentage': field_data['percentage'],
                'status': 'good' if field_data['percentage'] >= 80 else 'fair' if field_data['percentage'] >= 50 else 'poor'
            })

        # Generate filename
        shop_suffix = f"_{len(shop_ids)}shops" if shop_ids else "_allshops"
        filename = f"quality_report{shop_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return export_to_csv(report_data, filename)

    except Exception as e:
        current_app.logger.error(f"Error exporting quality report: {str(e)}")
        return jsonify({'error': 'Failed to export quality report'}), 500

@main.route('/api/product-details/<int:product_id>')
def api_product_details(product_id):
    """Enhanced product details with caching"""
    try:
        # Try to get from cache first
        cache_key = f"product_details_{product_id}"
        cached_details = enhanced_cache.get(cache_key, ttl=600)

        if cached_details is not None:
            return jsonify(cached_details)

        filters = {'search_term': str(product_id), 'per_page': 100}
        result = ProductData.get_filtered_data(filters)
        products = result['data']

        # Filter exact matches
        product_variants = [p for p in products if p['product_id'] == product_id]

        if not product_variants:
            return jsonify({'error': 'Product not found'}), 404

        product_info = {
            'product_id': product_id,
            'title': product_variants[0]['title'],
            'handle': product_variants[0]['handle'],
            'vendor': product_variants[0]['vendor'],
            'type': product_variants[0]['type'],
            'status': product_variants[0]['status'],
            'shop': product_variants[0]['shop_technical_name'],
            'variants': product_variants,
            'variant_count': len(product_variants)
        }

        # Cache the result
        enhanced_cache.set(cache_key, product_info, ttl=600)

        return jsonify(product_info)

    except Exception as e:
        current_app.logger.error(f"Error in product details API: {str(e)}")
        return jsonify({'error': 'Failed to load product details'}), 500

@main.route('/api/search-barcode')
def api_search_barcode():
    """Enhanced barcode search API endpoint with caching"""
    barcode = request.args.get('barcode', '').strip()

    if not barcode:
        return jsonify({'error': 'Barcode parameter required'}), 400

    if len(barcode) < 3:
        return jsonify({'error': 'Barcode too short (minimum 3 characters)'}), 400

    try:
        variants = ProductData.search_variants_by_barcode(barcode)

        return jsonify({
            'barcode': barcode,
            'found': len(variants),
            'variants': variants,
            'cached': True  # This will be cached by the decorator
        })

    except Exception as e:
        current_app.logger.error(f"Error in barcode search: {str(e)}")
        return jsonify({'error': 'Barcode search failed'}), 500

@main.route('/api/variant-details/<int:variant_id>')
def api_variant_details(variant_id):
    """Enhanced variant details with caching"""
    try:
        variant = ProductData.get_variant_details(variant_id)

        if not variant:
            return jsonify({'error': 'Variant not found'}), 404

        return jsonify({**variant, 'cached': True})

    except Exception as e:
        current_app.logger.error(f"Error in variant details: {str(e)}")
        return jsonify({'error': 'Failed to load variant details'}), 500

# API endpoints for dynamic filtering
@main.route('/api/shops')
def api_shops():
    """Get all shops with caching"""
    try:
        shops = ProductData.get_all_shops()
        return jsonify(shops)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/vendors')
def api_vendors():
    """Get vendors filtered by shops with caching"""
    try:
        shop_ids = request.args.getlist('shop_ids[]', type=int)
        vendors = ProductData.get_vendors(shop_ids if shop_ids else None)
        return jsonify(vendors)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/product-types')
def api_product_types():
    """Get product types filtered by shops with caching"""
    try:
        shop_ids = request.args.getlist('shop_ids[]', type=int)
        types = ProductData.get_product_types(shop_ids if shop_ids else None)
        return jsonify(types)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/consistency-check')
def consistency_check():
    """Data consistency checking page"""
    shop_ids = request.args.getlist('shop_ids[]', type=int)

    # Get data for analysis with reasonable limit
    filters = {'per_page': 10000}
    if shop_ids:
        filters['shop_ids'] = shop_ids

    result = ProductData.get_filtered_data(filters)
    all_products = result['data']

    # Analyze consistency issues
    issues = analyze_product_consistency(all_products)
    shops = ProductData.get_all_shops()

    return render_template('consistency.html',
                           issues=issues,
                           shops=shops,
                           selected_shops=shop_ids)

def analyze_product_consistency(products):
    """Analyze product data for consistency issues"""
    issues = {
        'missing_sku_products': [],
        'missing_barcode_products': [],
        'missing_images': [],
        'inconsistent_inventory_tracking': [],
        'zero_inventory_available': [],
        'missing_seo_fields': [],
        'duplicate_skus': [],
        'size_inconsistencies': []
    }

    # Group products by product_id
    products_by_id = {}
    sku_counts = {}
    barcode_counts = {}

    for product in products:
        product_id = product['product_id']

        # Group variants by product
        if product_id not in products_by_id:
            products_by_id[product_id] = []
        products_by_id[product_id].append(product)

        # Count SKU occurrences
        sku = product.get('variant_sku')
        if sku:
            sku_counts[sku] = sku_counts.get(sku, 0) + 1

        # Count barcode occurrences
        barcode = product.get('variant_barcode')
        if barcode:
            barcode_counts[barcode] = barcode_counts.get(barcode, 0) + 1

    # Find duplicate SKUs
    for sku, count in sku_counts.items():
        if count > 1:
            duplicate_products = [p for p in products if p.get('variant_sku') == sku]
            issues['duplicate_skus'].append({
                'sku': sku,
                'count': count,
                'products': duplicate_products[:5]
            })

    # Find duplicate barcodes
    duplicate_barcodes = []
    for barcode, count in barcode_counts.items():
        if count > 1:
            duplicate_products = [p for p in products if p.get('variant_barcode') == barcode]
            duplicate_barcodes.append({
                'barcode': barcode,
                'count': count,
                'products': duplicate_products[:5]
            })

    issues['duplicate_barcodes'] = duplicate_barcodes

    # Analyze each product group
    for product_id, variants in products_by_id.items():
        first_variant = variants[0]

        # Check for missing SKUs
        missing_sku_variants = [v for v in variants if not v.get('variant_sku')]
        if missing_sku_variants:
            issues['missing_sku_products'].append({
                'product': first_variant,
                'missing_count': len(missing_sku_variants)
            })

        # Check for missing barcodes
        missing_barcode_variants = [v for v in variants if not v.get('variant_barcode')]
        if missing_barcode_variants:
            issues['missing_barcode_products'].append({
                'product': first_variant,
                'missing_count': len(missing_barcode_variants)
            })

        # Check for missing images
        if not first_variant.get('image_src') and not any(v.get('variant_image') for v in variants):
            issues['missing_images'].append(first_variant)

        # Check inventory tracking consistency
        tracking_methods = set(v.get('variant_inventory_management') for v in variants if v.get('variant_inventory_management'))
        if len(tracking_methods) > 1:
            issues['inconsistent_inventory_tracking'].append({
                'product': first_variant,
                'tracking_methods': list(tracking_methods)
            })

        # Check for zero inventory but available
        zero_inventory_available = [v for v in variants
                                    if v.get('variant_inventory_quantity', 0) == 0
                                    and v.get('variant_available_for_sale')]
        if zero_inventory_available:
            issues['zero_inventory_available'].append({
                'product': first_variant,
                'affected_variants': len(zero_inventory_available)
            })

        # Check SEO fields
        if (not first_variant.get('Metafield: title_tag') or
                not first_variant.get('Metafield: description_tag')):
            issues['missing_seo_fields'].append(first_variant)

    # Limit results to prevent UI overload
    for key in issues:
        if isinstance(issues[key], list) and len(issues[key]) > 50:
            issues[key] = issues[key][:50]

    return issues