"""
Request validation schemas for the EDI Generator API.
Uses Pydantic for validation and serialization of incoming requests.
"""

from pydantic import BaseModel, Field, ConfigDict


class CodecoGenerateRequest(BaseModel):
    """
    Schema for the CODECO file generation request.
    Validates all required fields and enforces field types and constraints.

    Note: created_date, created_time, changed_date, and changed_time are automatically
    generated from the current UTC date/time on the server side.
    """

    yardId: str = Field(..., min_length=1, description="Yard ID")
    client: str = Field(..., min_length=1, description="Client code")
    weighbridge_id: str = Field(..., min_length=1, description="Weighbridge ID")
    weighbridge_id_sno: str = Field(..., min_length=1, description="Weighbridge serial number")
    transporter: str = Field(..., min_length=1, description="Transporter name")
    container_number: str = Field(..., min_length=1, description="Container number")
    container_size: str = Field(..., min_length=1, description="Container size")
    status: str = Field(..., min_length=1, max_length=2, description="Status code")
    vehicle_number: str = Field(..., min_length=1, description="Vehicle number")
    created_by: str = Field(..., min_length=1, description="User who created the record")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "yardId": "419101",
                "client": "0001052069",
                "weighbridge_id": "244191001345",
                "weighbridge_id_sno": "00001",
                "transporter": "PROPRE MOYEN",
                "container_number": "PCIU9507070",
                "container_size": "40",
                "status": "01",
                "vehicle_number": "028-AA-01",
                "created_by": "HCIHABIBS"
            }
        }
    )


class CodecoGenerateResponse(BaseModel):
    """Success response schema for CODECO generation."""

    status: str
    message: str
    xml_file: str
    edi_file: str
    uploaded_to_sftp: bool


class ErrorResponse(BaseModel):
    """Error response schema."""

    status: str
    stage: str
    message: str
