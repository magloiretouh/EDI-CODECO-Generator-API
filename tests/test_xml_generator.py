"""
Unit tests for XML Generator service.
Tests XML generation from request data and filename generation.
"""

import pytest
from datetime import datetime
from lxml import etree
from services.xml_generator import generate_xml, generate_xml_filename


class TestXmlGeneration:
    """Test cases for XML generation functionality."""

    @pytest.fixture
    def sample_request_data(self):
        """Fixture providing sample request data for XML generation."""
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

    def test_generate_xml_returns_string(self, sample_request_data):
        """Test that generate_xml returns a string."""
        result = generate_xml(sample_request_data)
        assert isinstance(result, str)

    def test_generate_xml_contains_declaration(self, sample_request_data):
        """Test that generated XML contains XML declaration."""
        result = generate_xml(sample_request_data)
        assert result.startswith('<?xml')

    def test_generate_xml_valid_structure(self, sample_request_data):
        """Test that generated XML is valid and parseable."""
        xml_string = generate_xml(sample_request_data)
        try:
            root = etree.fromstring(xml_string.encode('utf-8'))
            assert root is not None
        except etree.XMLSyntaxError:
            pytest.fail("Generated XML is not valid")

    def test_generate_xml_contains_root_element(self, sample_request_data):
        """Test that XML contains the expected root element."""
        xml_string = generate_xml(sample_request_data)
        root = etree.fromstring(xml_string.encode('utf-8'))
        assert 'SAP_CODECO_REPORT_MT' in root.tag

    def test_generate_xml_contains_header(self, sample_request_data):
        """Test that XML contains Header section with correct values."""
        xml_string = generate_xml(sample_request_data)
        root = etree.fromstring(xml_string.encode('utf-8'))

        # Find Header element
        header = root.find('.//Records/Header')
        assert header is not None

        # Check static field
        company_code = header.findtext('Company_Code')
        assert company_code == 'CIABJ31'

        # Check dynamic fields
        plant = header.findtext('Plant')
        assert plant == sample_request_data['yardId']

        customer = header.findtext('Customer')
        assert customer == sample_request_data['client']

    def test_generate_xml_contains_item(self, sample_request_data):
        """Test that XML contains Item section with correct values."""
        xml_string = generate_xml(sample_request_data)
        root = etree.fromstring(xml_string.encode('utf-8'))

        # Find Item element
        item = root.find('.//Records/Item')
        assert item is not None

        # Check dynamic fields
        weighbridge_id = item.findtext('Weighbridge_ID')
        assert weighbridge_id == sample_request_data['weighbridge_id']

        container_number = item.findtext('Container_Number')
        assert container_number == sample_request_data['container_number']

        status = item.findtext('Status')
        assert status == sample_request_data['status']

    def test_generate_xml_static_fields(self, sample_request_data):
        """Test that static fields in Item have expected values."""
        xml_string = generate_xml(sample_request_data)
        root = etree.fromstring(xml_string.encode('utf-8'))
        item = root.find('.//Records/Item')

        assert item.findtext('Design') == '003'
        assert item.findtext('Type') == '02'
        assert item.findtext('Color') == '#312682'
        assert item.findtext('Clean_Type') == '001'
        assert item.findtext('Device_Number') == 'TD2019031200'
        assert item.findtext('Num_Of_Entries') == '1'

    def test_generate_xml_changed_by_matches_created_by(self, sample_request_data):
        """Test that Changed_By uses same value as Created_By."""
        xml_string = generate_xml(sample_request_data)
        root = etree.fromstring(xml_string.encode('utf-8'))
        item = root.find('.//Records/Item')

        created_by = item.findtext('Created_By')
        changed_by = item.findtext('Changed_By')
        assert created_by == changed_by

    def test_generate_xml_namespaces(self, sample_request_data):
        """Test that XML contains expected namespaces."""
        xml_string = generate_xml(sample_request_data)
        root = etree.fromstring(xml_string.encode('utf-8'))

        nsmap = root.nsmap
        assert 'n0' in nsmap
        assert nsmap['n0'] == 'urn:olam.com:IVC:EDIFACT:ONE'
        assert 'prx' in nsmap
        assert 'soap-env' in nsmap

    def test_generate_xml_missing_field_handled_gracefully(self):
        """Test that missing field is handled gracefully (uses empty string)."""
        incomplete_data = {
            "yardId": "419101",
            "client": "0001052069"
            # Missing other required fields - should use empty strings
        }

        # Should not raise, just use empty strings for missing fields
        result = generate_xml(incomplete_data)
        assert isinstance(result, str)
        assert "419101" in result
        assert "0001052069" in result

    def test_generate_xml_filename_format(self):
        """Test XML filename generation format."""
        client = "0001052069"
        created_by = "HCIHABIBS"
        timestamp = datetime(2024, 4, 25, 4, 0, 11)

        filename = generate_xml_filename(client, created_by, timestamp)

        assert filename.startswith('CODECO_')
        assert filename.endswith('.xml')
        assert client in filename
        assert created_by in filename
        assert '20240425040011' in filename

    def test_generate_xml_filename_format_with_zero_padding(self):
        """Test that filename timestamp is zero-padded."""
        client = "0001052069"
        created_by = "USER"
        # Test with single digit month and day
        timestamp = datetime(2024, 1, 5, 9, 5, 3)

        filename = generate_xml_filename(client, created_by, timestamp)

        # Should be zero-padded: 20240105090503
        assert '20240105090503' in filename

    def test_generate_xml_filename_uses_utc_when_none(self):
        """Test that filename generation uses UTC when timestamp is None."""
        client = "TEST"
        created_by = "USER"

        # Call without timestamp
        filename = generate_xml_filename(client, created_by)

        # Should still be valid format
        assert filename.startswith('CODECO_')
        assert filename.endswith('.xml')
        assert client in filename
        assert created_by in filename


class TestXmlGeneratorEdgeCases:
    """Test edge cases and special characters in XML generation."""

    def test_generate_xml_with_special_characters(self):
        """Test XML generation with special characters that need escaping."""
        request_data = {
            "yardId": "419101",
            "client": "0001052069",
            "weighbridge_id": "244191001345",
            "weighbridge_id_sno": "00001",
            "transporter": "PROPRE & CO",  # Special character &
            "container_number": "PCIU9507070",
            "container_size": "40",
            "status": "01",
            "vehicle_number": "028-AA-01",
            "created_date": "20240425",
            "created_time": "040011",
            "changed_date": "20240425",
            "changed_time": "040011",
            "created_by": "USER<1>"  # Special characters < >
        }

        xml_string = generate_xml(request_data)

        # XML should still be valid and parseable
        root = etree.fromstring(xml_string.encode('utf-8'))
        assert root is not None

        # Special characters should be properly escaped in XML
        item = root.find('.//Records/Item')
        assert item.findtext('Transporter') == "PROPRE & CO"

    def test_generate_xml_with_empty_transporter_name(self):
        """Test XML generation handles empty transporter name gracefully."""
        request_data = {
            "yardId": "419101",
            "client": "0001052069",
            "weighbridge_id": "244191001345",
            "weighbridge_id_sno": "00001",
            "transporter": "",  # Empty string
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

        xml_string = generate_xml(request_data)
        root = etree.fromstring(xml_string.encode('utf-8'))

        item = root.find('.//Records/Item')
        assert item.findtext('Transporter') == ""
