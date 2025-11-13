"""
EDI CODECO Converter Service.
Converts XML data into EDIFACT CODECO format following UN/EDIFACT standard structure.

CODECO IMPLEMENTATION NOTES:
===========================
CODECO (Container Station Report Message) is an EDIFACT message type used to report
container movements and status changes at container terminals/stations.

Standard EDIFACT Segment Structure:
- UNB: Service String Advice (message envelope opening)
- UNH: Message Header
- BGM: Beginning of Message (document type, number, message function)
- DTM: Date/Time/Period (message creation date/time)
- NAD: Name and Address (parties involved: sender, receiver, etc.)
- COD: Container Details
- LOC: Location
- MEA: Measurements
- UNT: Message Trailer
- UNZ: Service String Advice (message envelope closing)

To extend this converter:
1. Add new segment building functions following the pattern of existing segments
2. Update map_xml_to_codeco() to call new segment builders
3. Document segment mapping in segment builder docstrings
4. Ensure proper segment termination with ' and use composite separators + and :
"""

from lxml import etree
from datetime import datetime
from typing import Dict, Any, List


def build_unb_segment(sender: str, receiver: str, timestamp: datetime) -> str:
    """
    Build UNB (Service String Advice) segment - message envelope opening.

    Format: UNB+UNOC:3+<sender>+<receiver>+<date>+<interchange_control_ref>

    Args:
        sender: Sender identification (typically yard/company code).
        receiver: Receiver identification (typically SFTP server or trading partner).
        timestamp: Message creation timestamp for interchange control reference.

    Returns:
        str: Formatted UNB segment terminated with '.
    """
    # Use timestamp as interchange control reference (uniqueness)
    interchange_control_ref = timestamp.strftime('%Y%m%d%H%M%S')

    unb = f"UNB+UNOC:3+{sender}+{receiver}+{timestamp.strftime('%y%m%d')}+{timestamp.strftime('%H%M')}+{interchange_control_ref}'"
    return unb


def build_unh_segment(message_ref_num: str) -> str:
    """
    Build UNH (Message Header) segment.

    Format: UNH+<message_ref_num>+CODECO:D:96A:UN:EANCOM

    Args:
        message_ref_num: Message reference number (typically sequential).

    Returns:
        str: Formatted UNH segment terminated with '.
    """
    unh = f"UNH+{message_ref_num}+CODECO:D:96A:UN:EANCOM'"
    return unh


def build_bgm_segment(container_number: str, status: str) -> str:
    """
    Build BGM (Beginning of Message) segment - document type and number.

    Format: BGM+<document_type>+<document_number>+<message_function>

    In CODECO context:
    - Document type: '393' for container movement report
    - Message function: '9' for original message

    Args:
        container_number: Container identifier for document number.
        status: Status code indicating container state.

    Returns:
        str: Formatted BGM segment terminated with '.
    """
    # Document type 393 = Container movement report
    bgm = f"BGM+393+{container_number}+9'"
    return bgm


def build_dtm_segment(created_date: str, created_time: str) -> str:
    """
    Build DTM (Date/Time/Period) segment - message creation date and time.

    Format: DTM+<qualifier>:<date>:<format_qualifier>

    Args:
        created_date: Date in YYYYMMDD format.
        created_time: Time in HHMMSS format.

    Returns:
        str: Formatted DTM segment terminated with '.
    """
    # Combine date and time in YYYYMMDDHHMMSS format
    datetime_str = f"{created_date}{created_time}"

    # Qualifier 137 = Document/message date/time
    # Format qualifier 204 = YYYYMMDDHHMMSS
    dtm = f"DTM+137:{datetime_str}:204'"
    return dtm


def build_nad_segment(party_role: str, party_id: str, party_name: str = None) -> str:
    """
    Build NAD (Name and Address) segment for involved parties.

    Format: NAD+<party_role>+<party_id>++<party_name>

    Party role codes:
    - FR: Freight forwarder/transporter
    - TO: Consignee/terminal operator
    - SH: Shipper
    - CN: Consignee

    Args:
        party_role: Role qualifier (e.g., 'FR' for transporter).
        party_id: Party identification code.
        party_name: Optional party name/description.

    Returns:
        str: Formatted NAD segment terminated with '.
    """
    if party_name:
        nad = f"NAD+{party_role}+{party_id}++{party_name}'"
    else:
        nad = f"NAD+{party_role}+{party_id}'"
    return nad


def build_cod_segment(container_number: str, container_size: str, status: str) -> str:
    """
    Build COD (Container Details) segment - container information.

    Format: COD+<container_number>+<container_size>+<status>

    Container size codes (ISO 6346):
    - '20' = 20-foot container
    - '40' = 40-foot container
    - '30' = 30-foot container

    Args:
        container_number: Unique container identification number.
        container_size: Container size code.
        status: Current container status code.

    Returns:
        str: Formatted COD segment terminated with '.
    """
    cod = f"COD+{container_number}+{container_size}+{status}'"
    return cod


def build_loc_segment(location_type: str, location_code: str) -> str:
    """
    Build LOC (Location) segment for container location details.

    Format: LOC+<location_type>+<location_code>

    Location type codes:
    - '5' = Place of delivery
    - '87' = Place of acceptance/loading
    - '88' = Place of discharge/unloading

    Args:
        location_type: Location qualifier code.
        location_code: Specific location identifier.

    Returns:
        str: Formatted LOC segment terminated with '.
    """
    loc = f"LOC+{location_type}+{location_code}'"
    return loc


def build_mea_segment(measurement_type: str, measurement_value: str, unit: str) -> str:
    """
    Build MEA (Measurements) segment for container measurements.

    Format: MEA+<measurement_type>+<unit>+<value>

    Measurement type codes:
    - '7' = Container weight
    - '8' = Container volume

    Args:
        measurement_type: Type of measurement.
        measurement_value: Numerical measurement value.
        unit: Unit of measurement (e.g., 'KGM' for kilograms).

    Returns:
        str: Formatted MEA segment terminated with '.
    """
    mea = f"MEA+{measurement_type}+{unit}+{measurement_value}'"
    return mea


def build_unt_segment(segment_count: int, message_ref_num: str) -> str:
    """
    Build UNT (Message Trailer) segment.

    Format: UNT+<segment_count>+<message_ref_num>

    The segment count includes UNH and UNT segments.

    Args:
        segment_count: Total number of segments in the message (including UNH and UNT).
        message_ref_num: Reference number from the corresponding UNH segment.

    Returns:
        str: Formatted UNT segment terminated with '.
    """
    unt = f"UNT+{segment_count}+{message_ref_num}'"
    return unt


def build_unz_segment(message_count: int, interchange_control_ref: str) -> str:
    """
    Build UNZ (Service String Advice) segment - message envelope closing.

    Format: UNZ+<message_count>+<interchange_control_ref>

    Args:
        message_count: Number of messages in the interchange.
        interchange_control_ref: Control reference from the UNB segment.

    Returns:
        str: Formatted UNZ segment terminated with '.
    """
    unz = f"UNZ+{message_count}+{interchange_control_ref}'"
    return unz


def map_xml_to_codeco(xml_string: str) -> str:
    """
    Main conversion function: transforms XML into EDIFACT CODECO format.

    This function parses the XML document and extracts relevant container and
    transaction information, then builds a complete EDIFACT CODECO message
    by assembling segments in the correct order.

    Args:
        xml_string: XML content as string (output from xml_generator.generate_xml()).

    Returns:
        str: Complete EDIFACT CODECO message with all segments properly formatted.

    Raises:
        etree.XMLSyntaxError: If XML is malformed.
        KeyError: If expected XML elements are missing.
    """

    # Parse XML string
    root = etree.fromstring(xml_string.encode('utf-8'))

    # Define namespace for XPath queries
    ns = {'n0': 'urn:olam.com:IVC:EDIFACT:ONE'}

    # Extract Header information
    header = root.find('.//Records/Header', ns)
    company_code = header.findtext('Company_Code') if header is not None else 'UNKNOWN'
    plant = header.findtext('Plant') if header is not None else 'UNKNOWN'
    customer = header.findtext('Customer') if header is not None else 'UNKNOWN'

    # Extract Item information
    item = root.find('.//Records/Item', ns)
    weighbridge_id = item.findtext('Weighbridge_ID') if item is not None else ''
    transporter = item.findtext('Transporter') if item is not None else ''
    container_number = item.findtext('Container_Number') if item is not None else ''
    container_size = item.findtext('Container_Size') if item is not None else ''
    status = item.findtext('Status') if item is not None else ''
    vehicle_number = item.findtext('Vehicle_Number') if item is not None else ''
    created_date = item.findtext('Created_Date') if item is not None else ''
    created_time = item.findtext('Created_Time') if item is not None else ''
    created_by = item.findtext('Created_By') if item is not None else ''

    # Parse timestamps for EDIFACT formatting
    timestamp = datetime.strptime(f"{created_date}{created_time}", '%Y%m%d%H%M%S')

    # Build EDIFACT segments in correct order
    segments: List[str] = []

    # 1. UNB - Service String Advice (message envelope opening)
    segments.append(build_unb_segment(company_code, plant, timestamp))

    # 2. UNH - Message Header
    message_ref_num = '1'
    segments.append(build_unh_segment(message_ref_num))

    # 3. BGM - Beginning of Message
    segments.append(build_bgm_segment(container_number, status))

    # 4. DTM - Date/Time information
    segments.append(build_dtm_segment(created_date, created_time))

    # 5. NAD - Name and Address segments for parties
    segments.append(build_nad_segment('TO', plant))  # Terminal operator (yard)
    segments.append(build_nad_segment('FR', transporter, transporter))  # Freight forwarder/transporter
    segments.append(build_nad_segment('SH', customer))  # Shipper/customer

    # 6. LOC - Location segment (container location at yard)
    segments.append(build_loc_segment('87', plant))  # Place of acceptance/loading

    # 7. COD - Container details
    segments.append(build_cod_segment(container_number, container_size, status))

    # 8. UNT - Message Trailer
    # Count: UNH + BGM + DTM + NAD(3) + LOC + COD + UNT = 11 segments
    segment_count = 11
    segments.append(build_unt_segment(segment_count, message_ref_num))

    # 9. UNZ - Service String Advice (message envelope closing)
    interchange_control_ref = timestamp.strftime('%Y%m%d%H%M%S')
    segments.append(build_unz_segment(1, interchange_control_ref))

    # Join all segments to create the complete EDIFACT message
    # Note: Each segment already ends with ', so no additional separator needed
    # Add newline after each segment for readability (except transmission - can be stripped)
    codeco_message = '\n'.join(segments)

    return codeco_message


def convert_xml_to_edi(xml_string: str) -> str:
    """
    Convert XML document to EDIFACT EDI format.

    This is the main entry point for EDI conversion. It calls map_xml_to_codeco()
    to generate the EDIFACT CODECO message.

    The returned message is formatted with line breaks (newlines) after each segment
    for improved readability. This is safe because:
    - Line breaks are not part of the EDIFACT standard
    - Only the segment terminator (') matters
    - Line breaks can be programmatically stripped before transmission

    To remove line breaks for transmission: message.replace('\\n', '')

    Args:
        xml_string: XML content as string.

    Returns:
        str: EDIFACT CODECO formatted message with line breaks for readability.
             Safe for storage and display; can be stripped before transmission.

    Raises:
        Exception: Re-raises any conversion errors with context.
    """
    try:
        edi_content = map_xml_to_codeco(xml_string)
        return edi_content
    except Exception as e:
        raise Exception(f"Failed to convert XML to EDI: {str(e)}")


def strip_edi_formatting(edi_message: str) -> str:
    """
    Remove line breaks from formatted EDI message for transmission.

    EDI messages are stored with line breaks for readability, but transmission-ready
    format requires the line breaks to be removed. This function converts from
    readable format to transmission format.

    Args:
        edi_message: EDI message string with line breaks.

    Returns:
        str: EDI message without line breaks, ready for transmission.

    Example:
        >>> formatted = "UNB+UNOC:3+SENDER+RECEIVER...'\\nUNH+1+CODECO...'"
        >>> transmission = strip_edi_formatting(formatted)
        >>> # transmission = "UNB+UNOC:3+SENDER+RECEIVER...'UNH+1+CODECO...'"
    """
    return edi_message.replace('\n', '')
