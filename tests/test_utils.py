# tests/test_utils.py
"""
Test utility functions.
"""

import pytest
from io import StringIO
from app.utils import (
    export_to_csv, calculate_percentages, get_metafield_completeness,
    validate_product_data, clean_product_data
)

class TestUtilityFunctions:
    """Test utility functions."""

    def test_export_to_csv_with_data(self):
        """Test CSV export with data."""
        test_data = [
            {'id': 1, 'name': 'Product 1', 'price': 10.99},
            {'id': 2, 'name': 'Product 2', 'price': 15.99}
        ]

        response = export_to_csv(test_data, 'test.csv')

        assert response is not None
        assert 'text/csv' in response.headers['Content-type']
        assert 'attachment; filename=test.csv' in response.headers['Content-Disposition']

        # Check CSV content
        csv_content = response.get_data(as_text=True)
        assert 'id,name,price' in csv_content
        assert 'Product 1' in csv_content
        assert 'Product 2' in csv_content

    def test_export_to_csv_no_data(self):
        """Test CSV export with no data."""
        response = export_to_csv([])
        assert response is None

        response = export_to_csv(None)
        assert response is None

    def test_calculate_percentages(self):
        """Test percentage calculations."""
        summary = {
            'total_variants': 1000,
            'missing_sku': 50,
            'missing_barcode': 100,
            'zero_inventory': 200
        }

        result = calculate_percentages(summary)

        assert result['missing_sku_pct'] == 5.0
        assert result['missing_barcode_pct'] == 10.0
        assert result['zero_inventory_pct'] == 20.0
        assert result['total_variants'] == 1000  # Original value preserved

    def test_calculate_percentages_zero_total(self):
        """Test percentage calculation with zero total."""
        summary = {'total_variants': 0, 'missing_sku': 0}
        result = calculate_percentages(summary)

        # Should return original summary unchanged
        assert result == summary

    def test_get_metafield_completeness(self):
        """Test metafield completeness analysis."""
        test_data = [
            {
                'Metafield: custom.deals': 'Sale',
                'Metafield: gender': 'Male',
                'Metafield: color': ''
            },
            {
                'Metafield: custom.deals': '',
                'Metafield: gender': 'Female',
                'Metafield: color': 'Red'
            },
            {
                'Metafield: custom.deals': 'Clearance',
                'Metafield: gender': '',
                'Metafield: color': ''
            }
        ]

        completeness = get_metafield_completeness(test_data)

        # Check deals metafield: 2 out of 3 have values
        assert completeness['Metafield: custom.deals']['count'] == 2
        assert completeness['Metafield: custom.deals']['percentage'] == 66.67

        # Check gender metafield: 2 out of 3 have values
        assert completeness['Metafield: gender']['count'] == 2
        assert completeness['Metafield: gender']['percentage'] == 66.67

        # Check color metafield: 1 out of 3 has value
        assert completeness['Metafield: color']['count'] == 1
        assert completeness['Metafield: color']['percentage'] == 33.33

    def test_get_metafield_completeness_empty_data(self):
        """Test metafield completeness with empty data."""
        completeness = get_metafield_completeness([])
        assert completeness == {}

    def test_validate_product_data_valid(self):
        """Test product validation with valid data."""
        valid_product = {
            'product_id': 123,
            'title': 'Valid Product',
            'variant_id': 456,
            'variant_sku': 'VALID-SKU-001',
            'variant_inventory_quantity': 10,
            'variant_available_for_sale': True,
            'image_src': 'https://example.com/image.jpg'
        }

        issues = validate_product_data(valid_product)
        assert len(issues) == 0

    def test_validate_product_data_invalid(self):
        """Test product validation with invalid data."""
        invalid_product = {
            'product_id': None,  # Missing required field
            'title': '',  # Missing required field
            'variant_id': 456,
            'variant_sku': 'AB',  # Too short
            'variant_inventory_quantity': 0,
            'variant_available_for_sale': True,  # Zero inventory but available
            'image_src': 'invalid-url'  # Invalid URL format
        }

        issues = validate_product_data(invalid_product)
        assert len(issues) > 0
        assert any('Missing required field: product_id' in issue for issue in issues)
        assert any('SKU too short' in issue for issue in issues)
        assert any('Zero inventory but marked as available' in issue for issue in issues)
        assert any('Invalid image URL format' in issue for issue in issues)

    def test_clean_product_data(self):
        """Test product data cleaning."""
        dirty_data = [
            {
                'title': '  Product   with   extra   spaces  ',
                'vendor': '  Vendor Name  ',
                'variant_sku': ' SKU-001 ',
                'variant_available_for_sale': 'true',
                'variant_inventory_quantity': '10',
                'size': 'extra large'
            }
        ]

        cleaned = clean_product_data(dirty_data)

        assert cleaned[0]['title'] == 'Product with extra spaces'
        assert cleaned[0]['vendor'] == 'Vendor Name'
        assert cleaned[0]['variant_sku'] == 'SKU-001'
        assert cleaned[0]['variant_available_for_sale'] is True
        assert cleaned[0]['variant_inventory_quantity'] == 10.0
        assert cleaned[0]['size'] == 'XL'  # Standardized size