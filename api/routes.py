"""
API Routes for EDI CODECO Generator.
Defines the Flask blueprint with the POST endpoint for CODECO file generation.
"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from api.schemas import CodecoGenerateRequest, CodecoGenerateResponse, ErrorResponse
from services.xml_generator import generate_xml, generate_xml_filename
from services.edi_converter import convert_xml_to_edi
from services.file_utils import write_file_async
from services.sftp_client import upload_edi_file
from config import config

logger = logging.getLogger(__name__)

# Create Flask blueprint
codeco_bp = Blueprint('codeco', __name__, url_prefix='/api/v1/codeco')


@codeco_bp.route('/generate', methods=['POST'])
def generate_codeco():
    """
    Generate CODECO XML and EDI files from JSON request.

    This endpoint accepts a JSON payload with container and transaction details,
    validates the input, generates both XML and EDI files, and uploads the EDI
    file to the configured SFTP server.

    Request body: CodecoGenerateRequest (JSON)
    Response: CodecoGenerateResponse (JSON) on success or ErrorResponse on failure

    Returns:
        JSON response with status, filenames, and SFTP upload status.
        HTTP 200 on success, HTTP 400/500 on error.
    """

    try:
        # Extract JSON payload
        try:
            payload = request.get_json()
        except Exception as e:
            logger.warning(f"Failed to parse JSON: {str(e)}")
            return jsonify({
                "status": "error",
                "stage": "validation",
                "message": "Request body must be valid JSON"
            }), 400

        if not payload:
            return jsonify({
                "status": "error",
                "stage": "validation",
                "message": "Request body must be valid JSON"
            }), 400

        # Validate request using Pydantic schema
        try:
            request_data = CodecoGenerateRequest(**payload)
        except ValidationError as e:
            # Extract validation error details
            error_details = "; ".join([
                f"{err['loc'][0]}: {err['msg']}"
                for err in e.errors()
            ])
            logger.warning(f"Validation failed: {error_details}")
            return jsonify({
                "status": "error",
                "stage": "validation",
                "message": f"Invalid request: {error_details}"
            }), 400

        # Convert request to dictionary for XML generation
        request_dict = request_data.model_dump()

        # Auto-generate date/time fields from current UTC time
        current_datetime = datetime.now(timezone.utc)
        request_dict['created_date'] = current_datetime.strftime('%Y%m%d')
        request_dict['created_time'] = current_datetime.strftime('%H%M%S')
        request_dict['changed_date'] = current_datetime.strftime('%Y%m%d')
        request_dict['changed_time'] = current_datetime.strftime('%H%M%S')

        # ==================== XML GENERATION ====================
        logger.info("Starting XML generation")
        try:
            xml_content = generate_xml(request_dict)
            logger.info("XML generated successfully")
        except Exception as e:
            logger.error(f"XML generation failed: {str(e)}")
            return jsonify({
                "status": "error",
                "stage": "xml_generation",
                "message": f"Failed to generate XML: {str(e)}"
            }), 500

        # ==================== EDI CONVERSION ====================
        logger.info("Starting EDI conversion")
        try:
            edi_content = convert_xml_to_edi(xml_content)
            logger.info("EDI conversion successful")
        except Exception as e:
            logger.error(f"EDI conversion failed: {str(e)}")
            return jsonify({
                "status": "error",
                "stage": "edi_conversion",
                "message": f"Failed to convert XML to EDI: {str(e)}"
            }), 500

        # ==================== FILE GENERATION ====================
        # Use the same timestamp that was used for date/time generation
        xml_filename = generate_xml_filename(
            request_dict['client'],
            request_dict['created_by'],
            current_datetime
        )
        edi_filename = xml_filename.replace('.xml', '.txt')

        xml_file_path = str(Path(config.OUTPUT_DIR) / xml_filename)
        edi_file_path = str(Path(config.OUTPUT_DIR) / edi_filename)

        logger.info(f"Writing files to {config.OUTPUT_DIR}")

        # Run async file writes
        try:
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Write both files asynchronously
            loop.run_until_complete(asyncio.gather(
                write_file_async(xml_file_path, xml_content),
                write_file_async(edi_file_path, edi_content)
            ))

            logger.info(f"Files written successfully: {xml_filename}, {edi_filename}")

        except Exception as e:
            logger.error(f"File write failed: {str(e)}")
            return jsonify({
                "status": "error",
                "stage": "file_write",
                "message": f"Failed to write files: {str(e)}"
            }), 500

        # ==================== SFTP UPLOAD ====================
        logger.info(f"Starting SFTP upload of {edi_filename}")
        uploaded_to_sftp = False

        if config.SFTP_HOST and config.SFTP_USER and config.SFTP_PASSWORD:
            try:
                # Run async SFTP upload
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                uploaded_to_sftp = loop.run_until_complete(
                    upload_edi_file(
                        edi_file_path,
                        config.SFTP_HOST,
                        config.SFTP_PORT,
                        config.SFTP_USER,
                        config.SFTP_PASSWORD,
                        config.SFTP_REMOTE_DIR,
                        config.SFTP_MAX_RETRIES,
                        config.SFTP_RETRY_DELAY
                    )
                )

                if uploaded_to_sftp:
                    logger.info(f"SFTP upload successful: {edi_filename}")
                else:
                    logger.warning("SFTP upload returned False")

            except Exception as e:
                logger.error(f"SFTP upload failed: {str(e)}")
                return jsonify({
                    "status": "error",
                    "stage": "sftp_upload",
                    "message": f"Failed to upload EDI to SFTP: {str(e)}"
                }), 500
        else:
            logger.warning("SFTP credentials not configured, skipping upload")

        # ==================== SUCCESS RESPONSE ====================
        response = CodecoGenerateResponse(
            status="success",
            message="Files generated and EDI uploaded to SFTP" if uploaded_to_sftp
                    else "Files generated (SFTP credentials not configured)",
            xml_file=xml_filename,
            edi_file=edi_filename,
            uploaded_to_sftp=uploaded_to_sftp
        )

        logger.info(f"Request completed successfully: {xml_filename}")
        return jsonify(response.model_dump()), 200

    except Exception as e:
        logger.error(f"Unexpected error in /generate endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "stage": "unknown",
            "message": f"Unexpected error: {str(e)}"
        }), 500


@codeco_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify API is running.

    Returns:
        JSON response with status and timestamp.
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200
