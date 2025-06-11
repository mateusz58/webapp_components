# tests/test_models.py
"""
Test database models and query functions.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.models import ProductData

class TestProductData:
    """Test ProductData model methods."""

    @patch('app.models.db.session.execute')
    def test_get_all_shops(self, mock_execute):
        """Test getting all shops."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [
            (1, 'shop1'),
            (2, 'shop2'),
            (3, 'shop3')
        ]
        mock_execute.return_value = mock_result

        shops = ProductData.get_all_shops()

        assert len(shops) == 3
        assert shops[0] == {'id': 1, 'name': 'shop1'}
        assert shops[1] == {'id': 2, 'name': 'shop2'}
        assert shops[2] == {'id': 3, 'name': 'shop3'}

    @patch('app.models.db.session.execute')
    def test_get_vendors_no_filter(self, mock_execute):
        """Test getting vendors without shop filter."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [
            ('Vendor A',),
            ('Vendor B',),
            ('Vendor C',)
        ]
        mock_execute.return_value = mock_result

        vendors = ProductData.get_vendors()

        assert len(vendors) == 3
        assert 'Vendor A' in vendors
        assert 'Vendor B' in vendors
        assert 'Vendor C' in vendors

    @patch('app.models.db.session.execute')
    def test_get_vendors_with_filter(self, mock_execute):
        """Test getting vendors with shop filter."""
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [('Vendor A',), ('Vendor B',)]
        mock_execute.return_value = mock_result

        vendors = ProductData.get_vendors([1, 2])

        # Verify the query was called with parameters
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args

        # Check that parameters were passed
        assert call_args[0][1] == {'shop_id_0': 1, 'shop_id_1': 2}
        assert len(vendors) == 2

    @patch('app.models.db.session.execute')
    def test_get_filtered_data_basic(self, mock_execute):
        """Test getting filtered data with basic filters."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.keys.return_value = ['product_id', 'title', 'status']
        mock_result.__iter__.return_value = [
            (123, 'Test Product', 'active'),
            (124, 'Test Product 2', 'draft')
        ]
        mock_execute.return_value = mock_result

        filters = {'status': 'active', 'limit': 100}
        products = ProductData.get_filtered_data(filters)

        assert len(products) == 2
        assert products[0]['product_id'] == 123
        assert products[0]['title'] == 'Test Product'

    @patch('app.models.db.session.execute')
    def test_get_filtered_data_with_shop_filter(self, mock_execute):
        """Test filtered data with shop ID filter."""
        mock_result = MagicMock()
        mock_result.keys.return_value = ['product_id', 'shop_technical_id']
        mock_result.__iter__.return_value = [(123, 1), (124, 2)]
        mock_execute.return_value = mock_result

        filters = {'shop_ids': [1, 2]}
        products = ProductData.get_filtered_data(filters)

        # Verify parameters were correctly built
        call_args = mock_execute.call_args
        params = call_args[0][1]
        assert 'shop_id_0' in params
        assert 'shop_id_1' in params
        assert params['shop_id_0'] == 1
        assert params['shop_id_1'] == 2

    @patch('app.models.db.session.execute')
    def test_get_data_health_summary(self, mock_execute):
        """Test data health summary calculation."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.keys.return_value = [
            'total_variants', 'missing_sku', 'missing_barcode',
            'missing_images', 'zero_inventory'
        ]
        mock_result.fetchone.return_value = (1000, 50, 100, 25, 150)
        mock_execute.return_value = mock_result

        summary = ProductData.get_data_health_summary()

        assert summary['total_variants'] == 1000
        assert summary['missing_sku'] == 50
        assert summary['missing_barcode'] == 100
        assert summary['missing_images'] == 25
        assert summary['zero_inventory'] == 150