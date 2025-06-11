# tests/test_integration.py
"""
Integration tests for complete user workflows.
"""

import pytest
from unittest.mock import patch

class TestIntegration:
    """Test complete user workflows."""

    @patch('app.models.ProductData.get_all_shops')
    @patch('app.models.ProductData.get_filtered_data')
    @patch('app.models.ProductData.get_vendors')
    @patch('app.models.ProductData.get_product_types')
    def test_complete_product_search_workflow(self, mock_types, mock_vendors,
                                              mock_data, mock_shops, client):
        """Test complete product search workflow."""
        # Setup mock data
        mock_shops.return_value = [{'id': 1, 'name': 'test_shop'}]
        mock_vendors.return_value = ['Test Vendor']
        mock_types.return_value = ['Test Type']
        mock_data.return_value = [
            {
                'product_id': 123,
                'title': 'Test Product',
                'variant_sku': 'TEST-001',
                'status': 'active'
            }
        ]

        # Step 1: User visits dashboard
        response = client.get('/')
        assert response.status_code == 200

        # Step 2: User goes to products page
        response = client.get('/products')
        assert response.status_code == 200

        # Step 3: User applies filters
        response = client.get('/products?status=active&shop_ids[]=1')
        assert response.status_code == 200

        # Step 4: User exports results
        with patch('app.routes.export_to_csv') as mock_export:
            mock_export.return_value = 'csv_response'
            response = client.get('/export?status=active&shop_ids[]=1')
            assert response.status_code == 200

    @patch('app.models.ProductData.get_data_health_summary')
    @patch('app.models.ProductData.get_filtered_data')
    @patch('app.models.ProductData.get_all_shops')
    def test_analytics_workflow(self, mock_shops, mock_data, mock_summary, client):
        """Test analytics dashboard workflow."""
        # Setup mock data
        mock_shops.return_value = [{'id': 1, 'name': 'test_shop'}]
        mock_summary.return_value = {
            'total_variants': 1000,
            'missing_sku': 50,
            'missing_barcode': 100
        }
        mock_data.return_value = [
            {'Metafield: custom.deals': 'Sale', 'Metafield: gender': 'Male'}
        ]

        # User visits analytics page
        response = client.get('/analytics')
        assert response.status_code == 200

        # User filters analytics by shop
        response = client.get('/analytics?shop_ids[]=1')
        assert response.status_code == 200

        # Verify shop filter was applied
        mock_summary.assert_called_with([1])
