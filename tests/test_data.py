# tests/test_data.py
"""
Test data fixtures and sample data for testing.
"""

import pytest

class TestDataFixtures:
    """Sample data for use in tests."""

    @staticmethod
    def sample_shops():
        """Sample shop data."""
        return [
            {'id': 1, 'name': 'shop_leo'},
            {'id': 2, 'name': 'shop_faina'},
            {'id': 3, 'name': 'shop_drei'}
        ]

    @staticmethod
    def sample_products():
        """Sample product data."""
        return [
            {
                'ordinal_number': 1,
                'shop_technical_name': 'leo',
                'shop_technical_id': 1,
                'product_id': 12345,
                'handle': 'sample-product-1',
                'title': 'Sample Product 1',
                'body_html': '<p>Product description</p>',
                'vendor': 'Sample Vendor',
                'type': 'Clothing',
                'tags': 'tag1,tag2,tag3',
                'status': 'active',
                'image_src': 'https://example.com/image1.jpg',
                'variant_id': 67890,
                'size': 'M',
                'color': 'Blue',
                'material': 'Cotton',
                'variant_sku': 'SAMPLE-001-M-BLUE',
                'variant_barcode': '1234567890123',
                'variant_weight': 0.5,
                'variant_inventory_quantity': 25,
                'variant_available_for_sale': True,
                'variant_inventory_management': 'shopify',
                'Metafield: custom.deals': 'New Arrival',
                'Metafield: gender': 'Unisex',
                'Metafield: title_tag': 'Sample Product 1 - Buy Now',
                'Metafield: description_tag': 'High quality sample product'
            },
            {
                'ordinal_number': 2,
                'shop_technical_name': 'leo',
                'shop_technical_id': 1,
                'product_id': 12346,
                'handle': 'sample-product-2',
                'title': 'Sample Product 2',
                'body_html': '<p>Another product description</p>',
                'vendor': 'Another Vendor',
                'type': 'Accessories',
                'tags': 'tag2,tag4',
                'status': 'draft',
                'image_src': '',  # Missing image
                'variant_id': 67891,
                'size': 'L',
                'color': 'Red',
                'material': 'Polyester',
                'variant_sku': '',  # Missing SKU
                'variant_barcode': '1234567890124',
                'variant_weight': 0.3,
                'variant_inventory_quantity': 0,  # Zero inventory
                'variant_available_for_sale': True,  # But still available
                'variant_inventory_management': 'manual',
                'Metafield: custom.deals': '',  # Missing metafield
                'Metafield: gender': 'Female',
                'Metafield: title_tag': '',  # Missing SEO
                'Metafield: description_tag': ''
            }
        ]

    @staticmethod
    def sample_consistency_issues():
        """Sample data with consistency issues."""
        return [
            # Duplicate SKUs
            {
                'product_id': 123,
                'variant_sku': 'DUPLICATE-SKU',
                'title': 'Product A'
            },
            {
                'product_id': 124,
                'variant_sku': 'DUPLICATE-SKU',  # Same SKU
                'title': 'Product B'
            },
            # Size inconsistencies
            {
                'product_id': 125,
                'size': 'Small',
                'title': 'Product C Variant 1'
            },
            {
                'product_id': 125,
                'size': 'small',  # Inconsistent capitalization
                'title': 'Product C Variant 2'
            }
        ]