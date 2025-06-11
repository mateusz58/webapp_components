"""
This file contains utility functions that support the main application.
These functions handle data processing, calculations, and file exports.
"""

import csv
import io
from flask import make_response

# ==============================================================================
# CSV EXPORT FUNCTIONALITY
# ==============================================================================

def export_to_csv(data, filename="shopify_products_export.csv"):
    """
    Convert product data to CSV format and create a downloadable response.
    
    This function takes a list of product dictionaries and converts them
    to a CSV file that the user can download.
    
    Args:
        data (list): List of dictionaries containing product data
        filename (str): Name for the downloaded file
        
    Returns:
        Flask Response object with CSV data, or None if no data
        
    Example usage:
        products = ProductData.get_filtered_data(filters)
        return export_to_csv(products, "my_products.csv")
    """

    # CHECK IF DATA EXISTS
    if not data:
        return None

    # CREATE IN-MEMORY STRING BUFFER
    # io.StringIO() creates a string buffer that we can write to like a file
    # This avoids creating temporary files on disk
    output = io.StringIO()

    # CREATE CSV WRITER
    # csv.DictWriter automatically handles the conversion from dictionaries to CSV
    # fieldnames comes from the keys of the first dictionary
    writer = csv.DictWriter(output, fieldnames=data[0].keys())

    # WRITE CSV CONTENT
    writer.writeheader()    # Write column headers
    writer.writerows(data)  # Write all data rows

    # CREATE FLASK RESPONSE
    # make_response() creates a Flask Response object with the CSV content
    response = make_response(output.getvalue())

    # SET RESPONSE HEADERS
    # These headers tell the browser to download the file instead of displaying it
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv"

    return response

# ==============================================================================
# DATA HEALTH CALCULATIONS
# ==============================================================================

def calculate_percentages(summary):
    """
    Calculate percentage values for data health summary statistics.
    
    Takes count values and adds corresponding percentage fields.
    This makes it easy to display both counts and percentages in templates.
    
    Args:
        summary (dict): Dictionary with count values
        
    Returns:
        dict: Original dictionary with added percentage fields
        
    Example:
        Input:  {'total_variants': 1000, 'missing_sku': 50}
        Output: {'total_variants': 1000, 'missing_sku': 50, 'missing_sku_pct': 5.0}
    """

    # CHECK IF WE HAVE DATA
    if summary.get('total_variants', 0) == 0:
        return summary

    total = summary['total_variants']

    # DEFINE FIELDS TO CALCULATE PERCENTAGES FOR
    percentage_fields = [
        'missing_sku',
        'missing_barcode',
        'missing_images',
        'missing_title_tag',
        'missing_description_tag',
        'zero_inventory',
        'unavailable_variants',
        'draft_products'
    ]

    # CALCULATE PERCENTAGES
    for field in percentage_fields:
        if field in summary:
            # Calculate percentage and round to 2 decimal places
            percentage = (summary[field] / total) * 100
            summary[f'{field}_pct'] = round(percentage, 2)

    return summary

# ==============================================================================
# METAFIELD ANALYSIS
# ==============================================================================

def get_metafield_completeness(data):
    """
    Analyze metafield completeness across all products.
    
    This function examines all metafield columns and calculates
    how many products have non-empty values for each metafield.
    
    Args:
        data (list): List of product dictionaries
        
    Returns:
        dict: Dictionary with completeness statistics for each metafield
        
    Example output:
        {
            'Metafield: custom.deals': {
                'count': 450,
                'percentage': 45.0
            },
            'Metafield: gender': {
                'count': 800,
                'percentage': 80.0
            }
        }
    """

    # CHECK IF WE HAVE DATA
    if not data:
        return {}

    # FIND ALL METAFIELD COLUMNS
    # Filter keys that start with 'Metafield:' to get only metafield columns
    metafields = [key for key in data[0].keys() if key.startswith('Metafield:')]

    total_records = len(data)
    completeness = {}

    # ANALYZE EACH METAFIELD
    for field in metafields:
        # COUNT NON-EMPTY VALUES
        # A value is considered "complete" if it exists and is not empty/whitespace
        non_empty = sum(
            1 for record in data
            if record.get(field) and str(record[field]).strip()
        )

        # CALCULATE STATISTICS
        completeness[field] = {
            'count': non_empty,
            'percentage': round((non_empty / total_records) * 100, 2) if total_records > 0 else 0
        }

    return completeness

# ==============================================================================
# DATA VALIDATION UTILITIES
# ==============================================================================

def validate_product_data(product):
    """
    Validate a single product record for common issues.
    
    This function checks a product dictionary for various data quality issues.
    
    Args:
        product (dict): Product dictionary to validate
        
    Returns:
        list: List of validation issues found
    """
    issues = []

    # CHECK REQUIRED FIELDS
    required_fields = ['product_id', 'title', 'variant_id']
    for field in required_fields:
        if not product.get(field):
            issues.append(f"Missing required field: {field}")

    # CHECK SKU FORMAT
    sku = product.get('variant_sku')
    if sku and len(sku) < 3:
        issues.append("SKU too short (less than 3 characters)")

    # CHECK INVENTORY LOGIC
    qty = product.get('variant_inventory_quantity', 0)
    available = product.get('variant_available_for_sale', False)

    if qty == 0 and available:
        issues.append("Zero inventory but marked as available for sale")

    # CHECK IMAGE URLs
    image_url = product.get('image_src')
    if image_url and not (image_url.startswith('http://') or image_url.startswith('https://')):
        issues.append("Invalid image URL format")

    # CHECK PRICE LOGIC (if price fields exist)
    price = product.get('price')
    compare_price = product.get('compare_at_price')

    if price and compare_price:
        try:
            if float(compare_price) <= float(price):
                issues.append("Compare price should be higher than regular price")
        except (ValueError, TypeError):
            issues.append("Invalid price format")

    return issues

def clean_product_data(products):
    """
    Clean and standardize product data.
    
    This function applies various cleaning operations to improve data quality.
    
    Args:
        products (list): List of product dictionaries
        
    Returns:
        list: Cleaned product data
    """
    cleaned_products = []

    for product in products:
        # CREATE A COPY TO AVOID MODIFYING ORIGINAL
        cleaned_product = product.copy()

        # CLEAN TEXT FIELDS
        text_fields = ['title', 'vendor', 'type', 'variant_sku']
        for field in text_fields:
            if cleaned_product.get(field):
                # Strip whitespace and normalize spacing
                cleaned_product[field] = ' '.join(cleaned_product[field].split())

        # STANDARDIZE BOOLEAN FIELDS
        boolean_fields = ['variant_available_for_sale']
        for field in boolean_fields:
            if field in cleaned_product:
                # Convert various representations to proper boolean
                value = cleaned_product[field]
                if isinstance(value, str):
                    cleaned_product[field] = value.lower() in ['true', '1', 'yes', 'on']
                else:
                    cleaned_product[field] = bool(value)

        # CLEAN NUMERIC FIELDS
        numeric_fields = ['variant_inventory_quantity', 'variant_weight']
        for field in numeric_fields:
            if field in cleaned_product and cleaned_product[field] is not None:
                try:
                    cleaned_product[field] = float(cleaned_product[field])
                except (ValueError, TypeError):
                    cleaned_product[field] = 0

        # STANDARDIZE SIZE VARIATIONS
        if cleaned_product.get('size'):
            size = cleaned_product['size'].upper().strip()
            # Standardize common size variations
            size_mappings = {
                'EXTRA SMALL': 'XS',
                'SMALL': 'S',
                'MEDIUM': 'M',
                'LARGE': 'L',
                'EXTRA LARGE': 'XL'
            }
            cleaned_product['size'] = size_mappings.get(size, size)

        cleaned_products.append(cleaned_product)

    return cleaned_products

# ==============================================================================
# REPORTING UTILITIES
# ==============================================================================

def generate_summary_report(products):
    """
    Generate a comprehensive summary report of product data.
    
    Args:
        products (list): List of product dictionaries
        
    Returns:
        dict: Summary statistics and insights
    """
    if not products:
        return {'total_products': 0}

    # BASIC COUNTS
    total_products = len(set(p['product_id'] for p in products))
    total_variants = len(products)

    # SHOP DISTRIBUTION
    shop_counts = {}
    for product in products:
        shop = product.get('shop_technical_name', 'Unknown')
        shop_counts[shop] = shop_counts.get(shop, 0) + 1

    # VENDOR DISTRIBUTION
    vendor_counts = {}
    for product in products:
        vendor = product.get('vendor', 'Unknown')
        vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1

    # STATUS DISTRIBUTION
    status_counts = {}
    for product in products:
        status = product.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1

    # INVENTORY ANALYSIS
    total_inventory = sum(p.get('variant_inventory_quantity', 0) for p in products)
    zero_inventory_count = sum(1 for p in products if p.get('variant_inventory_quantity', 0) == 0)

    # AVAILABILITY ANALYSIS
    available_count = sum(1 for p in products if p.get('variant_available_for_sale', False))

    # BUILD REPORT
    report = {
        'total_products': total_products,
        'total_variants': total_variants,
        'total_inventory': total_inventory,
        'average_inventory_per_variant': round(total_inventory / total_variants, 2) if total_variants > 0 else 0,
        'zero_inventory_variants': zero_inventory_count,
        'zero_inventory_percentage': round((zero_inventory_count / total_variants) * 100, 2) if total_variants > 0 else 0,
        'available_variants': available_count,
        'availability_percentage': round((available_count / total_variants) * 100, 2) if total_variants > 0 else 0,
        'shop_distribution': dict(sorted(shop_counts.items(), key=lambda x: x[1], reverse=True)),
        'vendor_distribution': dict(sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True)[:10]),  # Top 10
        'status_distribution': status_counts
    }

    return report

# ==============================================================================
# FILTERING UTILITIES
# ==============================================================================

def build_filter_summary(filters):
    """
    Create a human-readable summary of applied filters.
    
    This helps users understand what filters are currently active.
    
    Args:
        filters (dict): Dictionary of filter parameters
        
    Returns:
        list: List of human-readable filter descriptions
    """
    summary = []

    # SHOP FILTERS
    if filters.get('shop_ids'):
        shop_count = len(filters['shop_ids'])
        summary.append(f"Filtered to {shop_count} shop(s)")

    # STATUS FILTER
    if filters.get('status'):
        summary.append(f"Status: {filters['status'].title()}")

    # VENDOR FILTER
    if filters.get('vendors'):
        vendor_count = len(filters['vendors'])
        if vendor_count == 1:
            summary.append(f"Vendor: {filters['vendors'][0]}")
        else:
            summary.append(f"{vendor_count} vendors selected")

    # INVENTORY FILTERS
    if filters.get('zero_inventory'):
        summary.append("Zero inventory only")

    if filters.get('low_stock_threshold'):
        summary.append(f"Low stock (≤{filters['low_stock_threshold']})")

    if filters.get('available_for_sale_only'):
        summary.append("Available for sale only")

    # MISSING DATA FILTERS
    missing_filters = []
    if filters.get('missing_sku'):
        missing_filters.append("SKU")
    if filters.get('missing_barcode'):
        missing_filters.append("barcode")
    if filters.get('missing_images'):
        missing_filters.append("images")
    if filters.get('missing_title_tag'):
        missing_filters.append("title tag")

    if missing_filters:
        summary.append(f"Missing: {', '.join(missing_filters)}")

    # DATE FILTERS
    if filters.get('created_days_ago'):
        summary.append(f"Created in last {filters['created_days_ago']} days")

    if filters.get('updated_days_ago'):
        summary.append(f"Updated in last {filters['updated_days_ago']} days")

    # SEARCH FILTER
    if filters.get('search_term'):
        summary.append(f"Search: '{filters['search_term']}'")

    return summary

# ==============================================================================
# ERROR HANDLING UTILITIES
# ==============================================================================

def safe_get_value(dictionary, key, default=None, value_type=str):
    """
    Safely extract and convert values from dictionaries.
    
    This prevents errors when dealing with missing or invalid data.
    
    Args:
        dictionary (dict): Source dictionary
        key (str): Key to extract
        default: Default value if key doesn't exist or conversion fails
        value_type (type): Type to convert the value to
        
    Returns:
        Converted value or default
    """
    try:
        value = dictionary.get(key, default)
        if value is None:
            return default
        return value_type(value)
    except (ValueError, TypeError):
        return default

def log_data_issue(issue_type, details, product_id=None):
    """
    Log data quality issues for monitoring and debugging.
    
    In a production environment, you might want to log these to a file
    or send them to a monitoring service.
    
    Args:
        issue_type (str): Type of issue (e.g., 'missing_sku', 'invalid_price')
        details (str): Detailed description of the issue
        product_id (int, optional): Product ID if applicable
    """
    # In development, just print to console
    # In production, you'd log to a file or monitoring service
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {issue_type}: {details}"
    if product_id:
        log_entry += f" (Product ID: {product_id})"

    print(f"DATA ISSUE: {log_entry}")

# Add these functions to your utils.py file

def calculate_comprehensive_quality_score(enhanced_metrics, metafield_completeness):
    """
    Calculate a comprehensive data quality score based on multiple weighted factors.
    Updated to handle product-level metafield analysis correctly.

    Args:
        enhanced_metrics (dict): Enhanced quality metrics from the database
        metafield_completeness (dict): Metafield completeness data (at product level)

    Returns:
        dict: Quality score breakdown with overall score and individual component scores
    """
    if not enhanced_metrics or enhanced_metrics.get('total_variants', 0) == 0:
        return {
            'overall_score': 0,
            'breakdown': {},
            'recommendations': ['No data available for quality analysis']
        }

    total_variants = enhanced_metrics['total_variants']
    total_products = enhanced_metrics.get('total_products', total_variants)

    # Define quality factors with weights (should sum to 1.0)
    factors = {
        'core_data_completeness': {
            'weight': 0.30,
            'components': {
                'sku_completeness': calculate_completeness_score(enhanced_metrics.get('missing_sku', 0), total_variants),
                'barcode_completeness': calculate_completeness_score(enhanced_metrics.get('missing_barcode', 0), total_variants),
                'image_completeness': calculate_completeness_score(enhanced_metrics.get('missing_images', 0), total_variants)
            }
        },
        'seo_metadata_health': {
            'weight': 0.20,
            'components': {
                # Note: using product-level counts for metafields
                'title_tag_completeness': calculate_completeness_score(enhanced_metrics.get('missing_title_tag_products', 0), total_products),
                'description_tag_completeness': calculate_completeness_score(enhanced_metrics.get('missing_description_tag_products', 0), total_products)
            }
        },
        'categorization_richness': {
            'weight': 0.20,
            'components': {
                # Note: using product-level counts for metafields
                'category_completeness': calculate_completeness_score(enhanced_metrics.get('missing_categories_products', 0), total_products),
                'gender_completeness': calculate_completeness_score(enhanced_metrics.get('missing_gender_products', 0), total_products),
                'metafield_richness': calculate_metafield_richness_score(metafield_completeness)
            }
        },
        'inventory_health': {
            'weight': 0.15,
            'components': {
                'stock_availability': calculate_completeness_score(enhanced_metrics.get('zero_inventory', 0), total_variants),
                'inventory_tracking': calculate_completeness_score(enhanced_metrics.get('null_inventory', 0), total_variants)
            }
        },
        'product_status_health': {
            'weight': 0.10,
            'components': {
                'active_product_ratio': calculate_active_ratio_score(enhanced_metrics.get('active_products', 0), total_variants),
                'draft_product_impact': calculate_completeness_score(enhanced_metrics.get('draft_products', 0), total_variants)
            }
        },
        'additional_data_quality': {
            'weight': 0.05,
            'components': {
                'vendor_completeness': calculate_completeness_score(enhanced_metrics.get('missing_vendor', 0), total_variants),
                'type_completeness': calculate_completeness_score(enhanced_metrics.get('missing_type', 0), total_variants),
                'weight_completeness': calculate_completeness_score(enhanced_metrics.get('missing_weight', 0), total_variants)
            }
        }
    }

    # Calculate factor scores
    for factor_name, factor_data in factors.items():
        components = factor_data['components']
        if components:
            factor_data['score'] = sum(components.values()) / len(components)
        else:
            factor_data['score'] = 0

    # Calculate weighted overall score
    overall_score = sum(factor_data['score'] * factor_data['weight'] for factor_data in factors.values())
    overall_score = max(0, min(100, round(overall_score, 1)))

    # Generate recommendations based on scores
    recommendations = generate_quality_recommendations(factors, enhanced_metrics, total_variants, total_products)

    # Calculate quality grade
    quality_grade = get_quality_grade(overall_score)

    return {
        'overall_score': overall_score,
        'quality_grade': quality_grade,
        'breakdown': factors,
        'recommendations': recommendations,
        'metrics_summary': {
            'total_variants': total_variants,
            'total_products': total_products,
            'rich_content_products': enhanced_metrics.get('rich_content_products', 0),
            'rich_content_percentage': round((enhanced_metrics.get('rich_content_products', 0) / total_products) * 100, 2) if total_products > 0 else 0
        }
    }

def calculate_completeness_score(missing_count, total_count):
    """Calculate completeness score as percentage (higher is better)"""
    if total_count == 0:
        return 0
    completion_rate = max(0, (total_count - missing_count) / total_count)
    return round(completion_rate * 100, 2)

def calculate_active_ratio_score(active_count, total_count):
    """Calculate active product ratio score"""
    if total_count == 0:
        return 0
    active_ratio = active_count / total_count
    return round(active_ratio * 100, 2)

def calculate_metafield_richness_score(metafield_completeness):
    """Calculate score based on important metafield completion rates"""
    if not metafield_completeness:
        return 0

    # Define important metafields for e-commerce
    important_fields = [
        'custom.categories', 'gender', 'pattern', 'fit',
        'material', 'occasion', 'color', 'size'
    ]

    relevant_completions = []
    for field_name, data in metafield_completeness.items():
        field_lower = field_name.lower()
        if any(important in field_lower for important in important_fields):
            relevant_completions.append(data['percentage'])

    if relevant_completions:
        return round(sum(relevant_completions) / len(relevant_completions), 2)

    # Fallback: average of all metafields
    all_percentages = [data['percentage'] for data in metafield_completeness.values()]
    if all_percentages:
        return round(sum(all_percentages) / len(all_percentages), 2)

    return 0

def generate_quality_recommendations(factors, enhanced_metrics, total_variants, total_products):
    """Generate actionable recommendations based on quality analysis"""
    recommendations = []

    # Core data issues (variant level)
    core_data = factors.get('core_data_completeness', {})
    if core_data.get('score', 0) < 80:
        missing_sku = enhanced_metrics.get('missing_sku', 0)
        missing_barcode = enhanced_metrics.get('missing_barcode', 0)
        missing_images = enhanced_metrics.get('missing_images', 0)

        if missing_sku > 0:
            recommendations.append(f"🔧 Fix {missing_sku:,} missing SKUs ({missing_sku/total_variants*100:.1f}% of variants)")
        if missing_barcode > 0:
            recommendations.append(f"🏷️ Add barcodes to {missing_barcode:,} variants ({missing_barcode/total_variants*100:.1f}% of variants)")
        if missing_images > 0:
            recommendations.append(f"📸 Upload images for {missing_images:,} variants ({missing_images/total_variants*100:.1f}% of variants)")

    # SEO issues (product level)
    seo_health = factors.get('seo_metadata_health', {})
    if seo_health.get('score', 0) < 70:
        missing_title = enhanced_metrics.get('missing_title_tag_products', 0)
        missing_desc = enhanced_metrics.get('missing_description_tag_products', 0)

        if missing_title > 0:
            recommendations.append(f"📝 Add SEO title tags to {missing_title:,} products ({missing_title/total_products*100:.1f}% of products)")
        if missing_desc > 0:
            recommendations.append(f"📄 Add SEO descriptions to {missing_desc:,} products ({missing_desc/total_products*100:.1f}% of products)")

    # Categorization issues (product level)
    categorization = factors.get('categorization_richness', {})
    if categorization.get('score', 0) < 60:
        missing_categories = enhanced_metrics.get('missing_categories_products', 0)
        missing_gender = enhanced_metrics.get('missing_gender_products', 0)

        if missing_categories > 0:
            recommendations.append(f"🗂️ Categorize {missing_categories:,} uncategorized products ({missing_categories/total_products*100:.1f}% of products)")
        if missing_gender > 0:
            recommendations.append(f"👫 Set gender classification for {missing_gender:,} products ({missing_gender/total_products*100:.1f}% of products)")

    # Inventory issues (variant level)
    inventory_health = factors.get('inventory_health', {})
    if inventory_health.get('score', 0) < 75:
        zero_inventory = enhanced_metrics.get('zero_inventory', 0)
        if zero_inventory > 0:
            recommendations.append(f"📦 Review {zero_inventory:,} out-of-stock variants ({zero_inventory/total_variants*100:.1f}% of inventory)")

    # Draft products (variant level)
    draft_products = enhanced_metrics.get('draft_products', 0)
    if draft_products > 0:
        recommendations.append(f"🚀 Publish {draft_products:,} draft product variants or archive if not needed")

    # Priority recommendations based on impact
    if not recommendations:
        rich_products = enhanced_metrics.get('rich_content_products', 0)
        rich_percentage = (rich_products / total_products * 100) if total_products > 0 else 0

        if rich_percentage < 50:
            recommendations.append("⭐ Focus on enriching product data with categories, gender, and patterns for better searchability")
        else:
            recommendations.append("✅ Good data quality! Consider advanced optimizations like A/B testing product descriptions")

    return recommendations[:5]  # Limit to top 5 recommendations

def get_quality_grade(score):
    """Convert numeric score to letter grade"""
    if score >= 90:
        return {'letter': 'A', 'description': 'Excellent', 'color': 'success'}
    elif score >= 80:
        return {'letter': 'B', 'description': 'Good', 'color': 'info'}
    elif score >= 70:
        return {'letter': 'C', 'description': 'Fair', 'color': 'warning'}
    elif score >= 60:
        return {'letter': 'D', 'description': 'Poor', 'color': 'danger'}
    else:
        return {'letter': 'F', 'description': 'Critical', 'color': 'danger'}

def format_metafield_name(field_name):
    """Format metafield names for better display"""
    # Remove 'Metafield: ' prefix
    clean_name = field_name.replace('Metafield: ', '')

    # Handle special cases
    name_mappings = {
        'custom.deals': 'Deals & Promotions',
        'custom.categories': 'Product Categories',
        'Google Product Category': 'Google Category',
        'google_product_category': 'Google Category',
        'title_tag': 'SEO Title',
        'description_tag': 'SEO Description',
        'article_code1': 'Article Code',
        'trousers_rise': 'Trouser Rise',
        'type_of_heel': 'Heel Type',
        'shoe_tip': 'Shoe Tip Style',
        'occasion_2': 'Secondary Occasion',
        'occasion_3': 'Tertiary Occasion',
        'pattern_2': 'Secondary Pattern',
        'sleeve_type': 'Sleeve Type',
        'age_group': 'Target Age Group',
        'special_fit': 'Special Fit'
    }

    if clean_name in name_mappings:
        return name_mappings[clean_name]

    # Default formatting: title case with spaces
    return clean_name.replace('_', ' ').title()

def analyze_shop_comparison(shop_analysis):
    """
    Analyze differences between shops for comparison view.

    Args:
        shop_analysis (dict): Shop-level metafield analysis

    Returns:
        dict: Comparison insights and rankings
    """
    if not shop_analysis:
        return {}

    shop_scores = {}
    metafield_averages = {}

    # Calculate overall score for each shop
    for shop_id, shop_data in shop_analysis.items():
        metafields = shop_data.get('metafields', {})
        if metafields:
            total_completion = sum(mf.get('percentage', 0) for mf in metafields.values())
            avg_completion = total_completion / len(metafields)
            shop_scores[shop_id] = {
                'shop_name': shop_data['shop_name'],
                'avg_completion': round(avg_completion, 2),
                'total_products': shop_data.get('total_products', 0),
                'metafield_count': len(metafields)
            }

    # Calculate metafield averages across all shops
    all_metafields = set()
    for shop_data in shop_analysis.values():
        all_metafields.update(shop_data.get('metafields', {}).keys())

    for metafield in all_metafields:
        percentages = []
        for shop_data in shop_analysis.values():
            mf_data = shop_data.get('metafields', {}).get(metafield)
            if mf_data:
                percentages.append(mf_data.get('percentage', 0))

        if percentages:
            metafield_averages[metafield] = {
                'avg_percentage': round(sum(percentages) / len(percentages), 2),
                'min_percentage': min(percentages),
                'max_percentage': max(percentages),
                'shop_count': len(percentages)
            }

    # Rank shops by performance
    ranked_shops = sorted(shop_scores.items(), key=lambda x: x[1]['avg_completion'], reverse=True)

    return {
        'shop_scores': shop_scores,
        'metafield_averages': metafield_averages,
        'ranked_shops': ranked_shops,
        'best_performing_shop': ranked_shops[0] if ranked_shops else None,
        'needs_improvement': [shop for shop in ranked_shops if shop[1]['avg_completion'] < 50]
    }