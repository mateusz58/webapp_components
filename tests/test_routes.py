# tests/test_routes.py
"""
Test Flask routes and API endpoints.
"""

import pytest
import json
from unittest.mock import patch

class TestRoutes:
    """Test Flask routes."""

    def test_index_route(self, client):
        """Test main dashboard route."""
        with patch('app.routes.ProductData.get_all_shops') as mock_shops:
            mock_shops.return_value = [{'id': 1, 'name': 'test_shop'}]

            response = client.get('/')
            assert response.status_code == 200
            assert b'Shopify Product Analytics Dashboard' in response.data

    def test_products_route(self, client):
        """Test products listing route."""
        with patch('app.routes.ProductData.get_filtered_data') as mock_data, \
                patch('app.routes.ProductData.get_all_shops') as mock_shops, \
                patch('app.routes.ProductData.get_vendors') as mock_vendors, \
                patch('app.routes.ProductData.get_product_types') as mock_types:

            mock_data.return_value = [{'product_id': 123, 'title': 'Test Product'}]
            mock_shops.return_value = [{'id': 1, 'name': 'test_shop'}]
            mock_vendors.return_value = ['Test Vendor']
            mock_types.return_value = ['Test Type']

            response = client.get('/products')
            assert response.status_code == 200
            assert b'Product Data' in response.data

    def test_products_route_with_filters(self, client):
        """Test products route with filter parameters."""
        with patch('app.routes.ProductData.get_filtered_data') as mock_data, \
                patch('app.routes.ProductData.get_all_shops') as mock_shops, \
                patch('app.routes.ProductData.get_vendors') as mock_vendors, \
                patch('app.routes.ProductData.get_product_types') as mock_types:

            mock_data.return_value = []
            mock_shops.return_value = []
            mock_vendors.return_value = []
            mock_types.return_value = []

            response = client.get('/products?status=active&missing_sku=1&shop_ids[]=1')
            assert response.status_code == 200

            # Verify filters were passed to the model
            call_args = mock_data.call_args[0][0]
            assert 'status' in call_args
            assert 'missing_sku' in call_args
            assert 'shop_ids' in call_args

    def test_analytics_route(self, client):
        """Test analytics dashboard route."""
        with patch('app.routes.ProductData.get_data_health_summary') as mock_summary, \
                patch('app.routes.ProductData.get_filtered_data') as mock_data, \
                patch('app.routes.ProductData.get_all_shops') as mock_shops, \
                patch('app.routes.get_metafield_completeness') as mock_completeness:

            mock_summary.return_value = {'total_variants': 1000, 'missing_sku': 50}
            mock_data.return_value = []
            mock_shops.return_value = []
            mock_completeness.return_value = {}

            response = client.get('/analytics')
            assert response.status_code == 200
            assert b'Data Health Analytics' in response.data

    def test_api_shops(self, client):
        """Test shops API endpoint."""
        with patch('app.routes.ProductData.get_all_shops') as mock_shops:
            mock_shops.return_value = [
                {'id': 1, 'name': 'shop1'},
                {'id': 2, 'name': 'shop2'}
            ]

            response = client.get('/api/shops')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert len(data) == 2
            assert data[0]['id'] == 1
            assert data[0]['name'] == 'shop1'

    def test_api_vendors(self, client):
        """Test vendors API endpoint."""
        with patch('app.routes.ProductData.get_vendors') as mock_vendors:
            mock_vendors.return_value = ['Vendor A', 'Vendor B']

            response = client.get('/api/vendors')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert len(data) == 2
            assert 'Vendor A' in data
            assert 'Vendor B' in data

    def test_api_vendors_with_shop_filter(self, client):
        """Test vendors API with shop filter."""
        with patch('app.routes.ProductData.get_vendors') as mock_vendors:
            mock_vendors.return_value = ['Vendor A']

            response = client.get('/api/vendors?shop_ids[]=1&shop_ids[]=2')
            assert response.status_code == 200

            # Verify the shop filter was passed to the model
            mock_vendors.assert_called_with([1, 2])

    def test_export_route(self, client):
        """Test CSV export route."""
        with patch('app.routes.ProductData.get_filtered_data') as mock_data, \
                patch('app.routes.export_to_csv') as mock_export:

            mock_data.return_value = [{'id': 1, 'title': 'Test Product'}]
            mock_export.return_value = 'mocked_csv_response'

            response = client.get('/export')
            assert response.status_code == 200

            # Verify export function was called
            mock_export.assert_called_once()

    def test_consistency_check_route(self, client):
        """Test consistency checking route."""
        with patch('app.routes.ProductData.get_filtered_data') as mock_data, \
                patch('app.routes.ProductData.get_all_shops') as mock_shops, \
                patch('app.routes.analyze_product_consistency') as mock_analyze:

            mock_data.return_value = []
            mock_shops.return_value = []
            mock_analyze.return_value = {'duplicate_skus': []}

            response = client.get('/consistency-check')
            assert response.status_code == 200
            assert b'Data Consistency Check' in response.data

    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404