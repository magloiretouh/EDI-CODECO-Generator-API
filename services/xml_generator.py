"""
XML Generator Service for EDI CODECO files.
Converts validated request data into a properly formatted XML structure matching the SAP CODECO model.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from lxml import etree


def generate_xml(request_data: Dict[str, Any]) -> str:
    """
    Generate an XML string from validated request data.

    This function creates an XML document that matches the SAP_CODECO_REPORT_MT schema.
    Static fields are hardcoded as per the requirements, while dynamic fields are populated
    from the request_data dictionary.

    Args:
        request_data: Dictionary containing validated CODECO request fields.
                     Expected keys:
                     - yardId, client, weighbridge_id, weighbridge_id_sno
                     - transporter, container_number, container_size, status
                     - vehicle_number, created_date, created_time, changed_date
                     - changed_time, created_by

    Returns:
        str: Formatted XML string with proper indentation and declaration.

    Raises:
        KeyError: If any required field is missing from request_data.
        ValueError: If field values are invalid or empty.
    """

    # Define XML namespaces as per SAP CODECO model
    nsmap = {
        'n0': 'urn:olam.com:IVC:EDIFACT:ONE',
        'prx': 'urn:sap.com:proxy:GRP:/1SAI/TASC3DF160D1FCBB8D1B039:740',
        'soap-env': 'http://schemas.xmlsoap.org/soap/envelope/'
    }

    # Create root element
    root = etree.Element(
        '{urn:olam.com:IVC:EDIFACT:ONE}SAP_CODECO_REPORT_MT',
        nsmap=nsmap
    )

    # Create Records container
    records = etree.SubElement(root, 'Records')

    # ==================== HEADER SECTION ====================
    header = etree.SubElement(records, 'Header')

    # Static: Company Code
    company_code = etree.SubElement(header, 'Company_Code')
    company_code.text = 'CIABJ31'

    # Dynamic: Plant (from yardId)
    plant = etree.SubElement(header, 'Plant')
    plant.text = request_data.get('yardId', '')

    # Dynamic: Customer (from client)
    customer = etree.SubElement(header, 'Customer')
    customer.text = request_data.get('client', '')

    # ==================== ITEM SECTION ====================
    item = etree.SubElement(records, 'Item')

    # Dynamic: Weighbridge ID
    weighbridge_id = etree.SubElement(item, 'Weighbridge_ID')
    weighbridge_id.text = request_data.get('weighbridge_id', '')

    # Dynamic: Weighbridge ID SNO
    weighbridge_id_sno = etree.SubElement(item, 'Weighbridge_ID_SNO')
    weighbridge_id_sno.text = request_data.get('weighbridge_id_sno', '')

    # Dynamic: Transporter
    transporter = etree.SubElement(item, 'Transporter')
    transporter.text = request_data.get('transporter', '')

    # Dynamic: Container Number
    container_number = etree.SubElement(item, 'Container_Number')
    container_number.text = request_data.get('container_number', '')

    # Dynamic: Container Size
    container_size = etree.SubElement(item, 'Container_Size')
    container_size.text = request_data.get('container_size', '')

    # Static: Design
    design = etree.SubElement(item, 'Design')
    design.text = '003'

    # Static: Type
    item_type = etree.SubElement(item, 'Type')
    item_type.text = '02'

    # Static: Color
    color = etree.SubElement(item, 'Color')
    color.text = '#312682'

    # Static: Clean Type
    clean_type = etree.SubElement(item, 'Clean_Type')
    clean_type.text = '001'

    # Dynamic: Status
    status = etree.SubElement(item, 'Status')
    status.text = request_data.get('status', '')

    # Static: Device Number
    device_number = etree.SubElement(item, 'Device_Number')
    device_number.text = 'TD2019031200'

    # Dynamic: Vehicle Number
    vehicle_number = etree.SubElement(item, 'Vehicle_Number')
    vehicle_number.text = request_data.get('vehicle_number', '')

    # Dynamic: Created Date
    created_date = etree.SubElement(item, 'Created_Date')
    created_date.text = request_data.get('created_date', '')

    # Dynamic: Created Time
    created_time = etree.SubElement(item, 'Created_Time')
    created_time.text = request_data.get('created_time', '')

    # Dynamic: Created By
    created_by = etree.SubElement(item, 'Created_By')
    created_by.text = request_data.get('created_by', '')

    # Dynamic: Changed Date
    changed_date = etree.SubElement(item, 'Changed_Date')
    changed_date.text = request_data.get('changed_date', '')

    # Dynamic: Changed Time
    changed_time = etree.SubElement(item, 'Changed_Time')
    changed_time.text = request_data.get('changed_time', '')

    # Dynamic: Changed By (uses same value as Created_By)
    changed_by = etree.SubElement(item, 'Changed_By')
    changed_by.text = request_data.get('created_by', '')

    # Static: Number of Entries
    num_of_entries = etree.SubElement(item, 'Num_Of_Entries')
    num_of_entries.text = '1'

    # Convert to pretty-printed XML string with declaration
    xml_string = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='UTF-8'
    ).decode('utf-8')

    return xml_string


def generate_xml_filename(client: str, created_by: str, timestamp: datetime = None) -> str:
    """
    Generate XML filename following the pattern: CODECO_<customer>_<YYYYMMDDHHMMSS>_<created_by>.xml

    Args:
        client: Client/customer code from request.
        created_by: User who created the record.
        timestamp: Optional datetime object. If not provided, current UTC time is used.

    Returns:
        str: Formatted filename string.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    # Format timestamp as YYYYMMDDHHMMSS
    datetime_str = timestamp.strftime('%Y%m%d%H%M%S')

    return f'CODECO_{client}_{datetime_str}_{created_by}.xml'
