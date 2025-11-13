"""
Unit tests for API endpoints.
Tests Flask route handlers and request/response validation.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app import create_app
from config import TestingConfig


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = create_app()
    app.config.from_object(TestingConfig)
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test that health check returns HTTP 200."""
        response = client.get('/api/v1/codeco/health')
        assert response.status_code == 200

    def test_health_check_response_format(self, client):
        """Test health check response format."""
        response = client.get('/api/v1/codeco/health')
        data = json.loads(response.data)

        assert data['status'] == 'healthy'
        assert 'timestamp' in data


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_returns_200(self, client):
        """Test that root endpoint returns HTTP 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_root_response_format(self, client):
        """Test root endpoint response format."""
        response = client.get('/')
        data = json.loads(response.data)

        assert data['name'] == 'EDI CODECO Generator API'
        assert 'version' in data
        assert 'status' in data


class TestCodecoGenerateEndpoint:
    """Test CODECO generation endpoint."""

    @pytest.fixture
    def valid_request_data(self):
        """Fixture providing valid request data."""
        return {
            "yardId": "419101",
            "client": "0001052069",
            "weighbridge_id": "244191001345",
            "weighbridge_id_sno": "00001",
            "transporter": "PROPRE MOYEN",
            "container_number": "PCIU9507070",
            "container_size": "40",
            "status": "01",
            "vehicle_number": "028-AA-01",
            "created_date": "20240425",
            "created_time": "040011",
            "changed_date": "20240425",
            "changed_time": "040011",
            "created_by": "HCIHABIBS"
        }

    def test_generate_returns_200_with_valid_request(self, client, valid_request_data):
        """Test that valid request returns HTTP 200."""
        with patch('services.sftp_client.SFTPClient.upload_file'):
            response = client.post(
                '/api/v1/codeco/generate',
                json=valid_request_data,
                content_type='application/json'
            )
            assert response.status_code == 200

    def test_generate_response_format_on_success(self, client, valid_request_data):
        """Test response format on successful generation."""
        with patch('services.sftp_client.SFTPClient.upload_file'):
            response = client.post(
                '/api/v1/codeco/generate',
                json=valid_request_data,
                content_type='application/json'
            )
            data = json.loads(response.data)

            assert data['status'] == 'success'
            assert 'message' in data
            assert 'xml_file' in data
            assert 'edi_file' in data
            assert 'uploaded_to_sftp' in data

    def test_generate_filename_format(self, client, valid_request_data):
        """Test that generated filenames follow correct format."""
        with patch('services.sftp_client.SFTPClient.upload_file'):
            response = client.post(
                '/api/v1/codeco/generate',
                json=valid_request_data,
                content_type='application/json'
            )
            data = json.loads(response.data)

            # Check XML filename format: CODECO_<customer>_<YYYYMMDDHHMMSS>_<created_by>.xml
            assert data['xml_file'].startswith('CODECO_')
            assert data['xml_file'].endswith('.xml')
            assert '0001052069' in data['xml_file']  # customer code
            assert 'HCIHABIBS' in data['xml_file']   # created_by

            # Check EDI filename format
            assert data['edi_file'].startswith('CODECO_')
            assert data['edi_file'].endswith('.txt')

    def test_generate_returns_400_with_missing_field(self, client):
        """Test that request with missing field returns HTTP 400."""
        invalid_data = {
            "yardId": "419101",
            # Missing required fields
        }
        response = client.post(
            '/api/v1/codeco/generate',
            json=invalid_data,
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_generate_error_response_format_on_invalid_request(self, client):
        """Test error response format for invalid request."""
        invalid_data = {"yardId": "419101"}
        response = client.post(
            '/api/v1/codeco/generate',
            json=invalid_data,
            content_type='application/json'
        )
        data = json.loads(response.data)

        assert data['status'] == 'error'
        assert data['stage'] == 'validation'
        assert 'message' in data

    def test_generate_returns_400_with_empty_required_field(self, client, valid_request_data):
        """Test that empty required field returns HTTP 400."""
        invalid_data = valid_request_data.copy()
        invalid_data['container_number'] = ''

        response = client.post(
            '/api/v1/codeco/generate',
            json=invalid_data,
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_generate_returns_400_with_no_json_body(self, client):
        """Test that missing JSON body returns HTTP 400."""
        response = client.post(
            '/api/v1/codeco/generate',
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_generate_xml_file_created(self, client, valid_request_data):
        """Test that XML file is created in output directory."""
        with patch('services.sftp_client.SFTPClient.upload_file'):
            response = client.post(
                '/api/v1/codeco/generate',
                json=valid_request_data,
                content_type='application/json'
            )
            data = json.loads(response.data)

            xml_file = data['xml_file']
            assert xml_file.endswith('.xml')
            assert 'CODECO_' in xml_file

    def test_generate_edi_file_created(self, client, valid_request_data):
        """Test that EDI file is created in output directory."""
        with patch('services.sftp_client.SFTPClient.upload_file'):
            response = client.post(
                '/api/v1/codeco/generate',
                json=valid_request_data,
                content_type='application/json'
            )
            data = json.loads(response.data)

            edi_file = data['edi_file']
            assert edi_file.endswith('.txt')
            assert 'CODECO_' in edi_file


class TestErrorHandling:
    """Test error handling in Flask app."""

    def test_404_not_found(self, client):
        """Test 404 error response."""
        response = client.get('/nonexistent/endpoint')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'

    def test_405_method_not_allowed(self, client):
        """Test 405 error response."""
        response = client.get('/api/v1/codeco/generate')
        assert response.status_code == 405
        data = json.loads(response.data)
        assert data['status'] == 'error'
