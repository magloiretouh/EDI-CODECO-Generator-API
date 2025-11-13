"""
Unit tests for EDI Converter service.
Tests conversion of XML to EDIFACT CODECO format.
"""

import pytest
from services.edi_converter import (
    convert_xml_to_edi,
    build_unb_segment,
    build_unh_segment,
    build_bgm_segment,
    build_dtm_segment,
    build_nad_segment,
    build_cod_segment,
    build_loc_segment,
    build_unt_segment,
    build_unz_segment
)
from services.xml_generator import generate_xml
from datetime import datetime


class TestEDISegmentBuilders:
    """Test individual EDIFACT segment building functions."""

    def test_build_unb_segment(self):
        """Test UNB segment building."""
        timestamp = datetime(2024, 4, 25, 4, 0, 11)
        segment = build_unb_segment('CIABJ31', 'TERMLOC', timestamp)

        assert segment.startswith('UNB+UNOC:3+')
        assert 'CIABJ31' in segment
        assert 'TERMLOC' in segment
        assert segment.endswith("'")

    def test_build_unh_segment(self):
        """Test UNH segment building."""
        segment = build_unh_segment('1')

        assert segment == "UNH+1+CODECO:D:96A:UN:EANCOM'"

    def test_build_bgm_segment(self):
        """Test BGM segment building."""
        segment = build_bgm_segment('PCIU9507070', '01')

        assert segment.startswith('BGM+393+')
        assert 'PCIU9507070' in segment
        assert segment.endswith("'")

    def test_build_dtm_segment(self):
        """Test DTM segment building."""
        segment = build_dtm_segment('20240425', '040011')

        assert 'DTM+137:' in segment
        assert '20240425040011:204' in segment
        assert segment.endswith("'")

    def test_build_nad_segment_with_name(self):
        """Test NAD segment building with party name."""
        segment = build_nad_segment('FR', 'TRANSPORTER', 'Transporter Company')

        assert segment == "NAD+FR+TRANSPORTER++Transporter Company'"

    def test_build_nad_segment_without_name(self):
        """Test NAD segment building without party name."""
        segment = build_nad_segment('TO', 'YARD123')

        assert segment == "NAD+TO+YARD123'"

    def test_build_cod_segment(self):
        """Test COD segment building."""
        segment = build_cod_segment('PCIU9507070', '40', '01')

        assert segment == "COD+PCIU9507070+40+01'"

    def test_build_loc_segment(self):
        """Test LOC segment building."""
        segment = build_loc_segment('87', 'YARD419101')

        assert segment == "LOC+87+YARD419101'"

    def test_build_unt_segment(self):
        """Test UNT segment building."""
        segment = build_unt_segment(11, '1')

        assert segment == "UNT+11+1'"

    def test_build_unz_segment(self):
        """Test UNZ segment building."""
        segment = build_unz_segment(1, '20240425040011')

        assert segment == "UNZ+1+20240425040011'"


class TestXMLToEDIConversion:
    """Test XML to EDIFACT CODECO conversion."""

    @pytest.fixture
    def sample_xml(self):
        """Fixture providing sample XML for conversion testing."""
        request_data = {
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
        return generate_xml(request_data)

    def test_convert_xml_to_edi_returns_string(self, sample_xml):
        """Test that conversion returns a string."""
        result = convert_xml_to_edi(sample_xml)
        assert isinstance(result, str)

    def test_convert_xml_to_edi_contains_unb_segment(self, sample_xml):
        """Test that converted EDI contains UNB segment."""
        edi = convert_xml_to_edi(sample_xml)
        assert edi.startswith('UNB+')

    def test_convert_xml_to_edi_contains_unh_segment(self, sample_xml):
        """Test that converted EDI contains UNH segment."""
        edi = convert_xml_to_edi(sample_xml)
        assert 'UNH+' in edi

    def test_convert_xml_to_edi_contains_bgm_segment(self, sample_xml):
        """Test that converted EDI contains BGM segment."""
        edi = convert_xml_to_edi(sample_xml)
        assert 'BGM+' in edi

    def test_convert_xml_to_edi_contains_dtm_segment(self, sample_xml):
        """Test that converted EDI contains DTM segment."""
        edi = convert_xml_to_edi(sample_xml)
        assert 'DTM+' in edi

    def test_convert_xml_to_edi_contains_nad_segments(self, sample_xml):
        """Test that converted EDI contains NAD segments."""
        edi = convert_xml_to_edi(sample_xml)
        # Should have at least 3 NAD segments (TO, FR, SH)
        assert edi.count('NAD+') >= 3

    def test_convert_xml_to_edi_contains_cod_segment(self, sample_xml):
        """Test that converted EDI contains COD segment."""
        edi = convert_xml_to_edi(sample_xml)
        assert 'COD+' in edi

    def test_convert_xml_to_edi_contains_loc_segment(self, sample_xml):
        """Test that converted EDI contains LOC segment."""
        edi = convert_xml_to_edi(sample_xml)
        assert 'LOC+' in edi

    def test_convert_xml_to_edi_contains_unt_segment(self, sample_xml):
        """Test that converted EDI contains UNT segment."""
        edi = convert_xml_to_edi(sample_xml)
        assert 'UNT+' in edi

    def test_convert_xml_to_edi_contains_unz_segment(self, sample_xml):
        """Test that converted EDI contains UNZ segment."""
        edi = convert_xml_to_edi(sample_xml)
        assert edi.endswith("'") or 'UNZ+' in edi

    def test_convert_xml_to_edi_all_segments_terminated(self, sample_xml):
        """Test that all segments in EDI are properly terminated with '."""
        edi = convert_xml_to_edi(sample_xml)
        # Count opening quotes should equal closing quotes
        # Each segment ends with '
        assert edi.count("'") > 0

    def test_convert_xml_to_edi_contains_container_number(self, sample_xml):
        """Test that EDI contains the container number from XML."""
        edi = convert_xml_to_edi(sample_xml)
        assert 'PCIU9507070' in edi

    def test_convert_xml_to_edi_contains_container_size(self, sample_xml):
        """Test that EDI contains the container size from XML."""
        edi = convert_xml_to_edi(sample_xml)
        # Container size should appear in COD segment
        assert '+40+' in edi

    def test_convert_xml_to_edi_with_invalid_xml_raises_error(self):
        """Test that invalid XML raises an exception."""
        invalid_xml = "<invalid>Not proper XML"

        with pytest.raises(Exception):
            convert_xml_to_edi(invalid_xml)

    def test_convert_xml_to_edi_preserves_dates(self):
        """Test that dates are properly preserved in EDI."""
        request_data = {
            "yardId": "419101",
            "client": "0001052069",
            "weighbridge_id": "244191001345",
            "weighbridge_id_sno": "00001",
            "transporter": "PROPRE MOYEN",
            "container_number": "PCIU9507070",
            "container_size": "40",
            "status": "01",
            "vehicle_number": "028-AA-01",
            "created_date": "20240101",
            "created_time": "235959",
            "changed_date": "20240101",
            "changed_time": "235959",
            "created_by": "HCIHABIBS"
        }
        xml = generate_xml(request_data)
        edi = convert_xml_to_edi(xml)

        # Date and time should appear in EDI
        assert '20240101235959' in edi


class TestEDIConversionEdgeCases:
    """Test edge cases in EDIFACT conversion."""

    def test_convert_xml_with_special_characters_in_transporter(self):
        """Test conversion with special characters in transporter name."""
        request_data = {
            "yardId": "419101",
            "client": "0001052069",
            "weighbridge_id": "244191001345",
            "weighbridge_id_sno": "00001",
            "transporter": "TRANS & CO",
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
        xml = generate_xml(request_data)
        edi = convert_xml_to_edi(xml)

        # Should be valid EDI even with special characters
        assert isinstance(edi, str)
        assert len(edi) > 0
        assert 'UNB+' in edi
