"""
Flask API endpoints for CauseListOCR
Main application routes for document upload, extraction, and data retrieval
"""

import logging
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session

from app.models.models import (
    CauseListDocument, ExtractionRun, ExtractedRecord,
    ProcessingStatusEnum, ConfidenceLevelEnum
)
from app.models.database import get_db
from app.ocr.processor import OCRProcessor
from app.extraction.extractor import RecordExtractor
from app.output.formatter import OutputFormatter
from app.validation.validator import RecordValidator

logger = logging.getLogger(__name__)

# Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Configuration
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }), 200


@api_bp.route('/documents', methods=['POST'])
def upload_document():
    """Upload a cause list document.
    
    Returns:
        JSON with document info and document_id
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": f"File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f} MB limit"}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + filename
        
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Create database record
        db = get_db()
        doc = CauseListDocument(
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            processing_status=ProcessingStatusEnum.PENDING
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        logger.info(f"Document uploaded: {doc.id} - {filename}")
        
        return jsonify({
            "success": True,
            "document_id": doc.id,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "status": doc.processing_status.value
        }), 201
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/documents/<int:doc_id>', methods=['GET'])
def get_document(doc_id: int):
    """Get document details."""
    try:
        db = get_db()
        doc = db.query(CauseListDocument).filter(CauseListDocument.id == doc_id).first()
        
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        
        return jsonify({
            "id": doc.id,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "status": doc.processing_status.value,
            "pages": doc.pages,
            "ocr_engine": doc.ocr_engine
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/documents/<int:doc_id>/process', methods=['POST'])
def process_document(doc_id: int):
    """Process a document with OCR and extract records.
    
    Query params:
        ocr_engine: 'tesseract' or 'textract' (default: 'tesseract')
        extract_method: 'line-based' or 'table-based' (default: 'line-based')
    """
    try:
        db = get_db()
        doc = db.query(CauseListDocument).filter(CauseListDocument.id == doc_id).first()
        
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        
        if doc.processing_status == ProcessingStatusEnum.PROCESSING:
            return jsonify({"error": "Document is already being processed"}), 409
        
        # Get parameters
        ocr_engine = request.json.get('ocr_engine', 'tesseract') if request.is_json else 'tesseract'
        extract_method = request.json.get('extract_method', 'line-based') if request.is_json else 'line-based'
        
        # Update status
        doc.processing_status = ProcessingStatusEnum.PROCESSING
        doc.processing_started = datetime.utcnow()
        doc.ocr_engine = ocr_engine
        db.commit()
        
        # OCR processing
        ocr_processor = OCRProcessor(engine=ocr_engine)
        ocr_result = ocr_processor.process_file(doc.file_path)
        
        # Create extraction run
        extraction_run = ExtractionRun(
            document_id=doc.id,
            extraction_method=extract_method,
            average_confidence=0.0
        )
        db.add(extraction_run)
        db.commit()
        db.refresh(extraction_run)
        
        # Extract records
        extractor = RecordExtractor(method=extract_method)
        records = extractor.extract(ocr_result, extraction_run.id)
        
        # Validate records
        validator = RecordValidator()
        for record in records:
            issues = validator.validate(record)
            record.validation_issues = str(issues)
            record.validation_passed = len(issues) == 0
            record.needs_review = len(issues) > 0
        
        db.add_all(records)
        
        # Update extraction run stats
        extraction_run.total_records_extracted = len(records)
        extraction_run.records_requiring_review = sum(1 for r in records if r.needs_review)
        extraction_run.duplicates_found = sum(1 for r in records if r.is_duplicate)
        extraction_run.average_confidence = sum(r.overall_confidence for r in records) / len(records) if records else 0
        
        # Update document status
        doc.processing_status = ProcessingStatusEnum.COMPLETED
        doc.processing_completed = datetime.utcnow()
        doc.pages = ocr_result.get('total_pages', 0)
        
        db.commit()
        
        logger.info(f"Document {doc_id} processed: {len(records)} records extracted")
        
        return jsonify({
            "success": True,
            "document_id": doc.id,
            "extraction_run_id": extraction_run.id,
            "total_records": extraction_run.total_records_extracted,
            "records_requiring_review": extraction_run.records_requiring_review,
            "duplicates_found": extraction_run.duplicates_found,
            "average_confidence": round(extraction_run.average_confidence, 4)
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        db = get_db()
        doc = db.query(CauseListDocument).filter(CauseListDocument.id == doc_id).first()
        if doc:
            doc.processing_status = ProcessingStatusEnum.FAILED
            db.commit()
        return jsonify({"error": str(e)}), 500


@api_bp.route('/records', methods=['GET'])
def list_records():
    """List extracted records with filtering.
    
    Query params:
        case_number: Filter by case number
        confidence_level: HIGH, MEDIUM, LOW, CRITICAL
        needs_review: true/false
        limit: Max records (default: 100)
        offset: Pagination offset (default: 0)
    """
    try:
        db = get_db()
        query = db.query(ExtractedRecord)
        
        # Apply filters
        if request.args.get('case_number'):
            query = query.filter(ExtractedRecord.case_number.ilike(f"%{request.args.get('case_number')}%"))
        
        if request.args.get('confidence_level'):
            try:
                conf_level = ConfidenceLevelEnum[request.args.get('confidence_level')]
                query = query.filter(ExtractedRecord.confidence_level == conf_level)
            except KeyError:
                return jsonify({"error": "Invalid confidence level"}), 400
        
        if request.args.get('needs_review') == 'true':
            query = query.filter(ExtractedRecord.needs_review == True)
        elif request.args.get('needs_review') == 'false':
            query = query.filter(ExtractedRecord.needs_review == False)
        
        # Pagination
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        total = query.count()
        records = query.limit(limit).offset(offset).all()
        
        return jsonify({
            "total": total,
            "limit": limit,
            "offset": offset,
            "records": [
                {
                    "id": r.id,
                    "case_number": r.case_number,
                    "hearing_date": r.hearing_date,
                    "party_name": r.party_name,
                    "advocate": r.advocate,
                    "overall_confidence": round(r.overall_confidence, 4),
                    "confidence_level": r.confidence_level.value,
                    "needs_review": r.needs_review
                }
                for r in records
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing records: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/records/<int:record_id>', methods=['GET'])
def get_record(record_id: int):
    """Get detailed record information."""
    try:
        db = get_db()
        record = db.query(ExtractedRecord).filter(ExtractedRecord.id == record_id).first()
        
        if not record:
            return jsonify({"error": "Record not found"}), 404
        
        return jsonify({
            "id": record.id,
            "case_number": record.case_number,
            "hearing_date": record.hearing_date,
            "party_name": record.party_name,
            "advocate": record.advocate,
            "case_number_confidence": round(record.case_number_confidence, 4),
            "date_confidence": round(record.date_confidence, 4),
            "party_name_confidence": round(record.party_name_confidence, 4),
            "advocate_confidence": round(record.advocate_confidence, 4),
            "overall_confidence": round(record.overall_confidence, 4),
            "confidence_level": record.confidence_level.value,
            "needs_review": record.needs_review,
            "is_duplicate": record.is_duplicate,
            "validation_passed": record.validation_passed,
            "validation_issues": record.validation_issues,
            "page_number": record.page_number,
            "line_number": record.line_number
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving record: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/export', methods=['POST'])
def export_records():
    """Export records in specified format.
    
    Request JSON:
        format: 'csv', 'json', 'excel', or 'html'
        filters: dict of filters to apply
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        export_format = request.json.get('format', 'csv').lower()
        if export_format not in ['csv', 'json', 'excel', 'html']:
            return jsonify({"error": "Invalid format. Must be: csv, json, excel, html"}), 400
        
        # Get records
        db = get_db()
        query = db.query(ExtractedRecord)
        
        # Apply filters if provided
        filters = request.json.get('filters', {})
        if filters.get('needs_review'):
            query = query.filter(ExtractedRecord.needs_review == True)
        if filters.get('confidence_level'):
            try:
                conf_level = ConfidenceLevelEnum[filters['confidence_level']]
                query = query.filter(ExtractedRecord.confidence_level == conf_level)
            except KeyError:
                return jsonify({"error": "Invalid confidence level"}), 400
        
        records = query.all()
        records_dict = [
            {
                "case_number": r.case_number,
                "hearing_date": r.hearing_date,
                "party_name": r.party_name,
                "advocate": r.advocate,
                "overall_confidence": r.overall_confidence,
                "confidence_level": r.confidence_level.value,
                "needs_review": r.needs_review
            }
            for r in records
        ]
        
        # Format and export
        formatter = OutputFormatter()
        
        if export_format == 'json':
            output = formatter.to_json(records_dict)
            return output, 200, {'Content-Type': 'application/json'}
        
        elif export_format == 'csv':
            output = formatter.to_csv(records_dict)
            return output, 200, {'Content-Type': 'text/csv'}
        
        elif export_format == 'html':
            output = formatter.to_html(records_dict)
            return output, 200, {'Content-Type': 'text/html'}
        
        elif export_format == 'excel':
            output = formatter.to_excel(records_dict)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'causelist_{datetime.utcnow().strftime("%Y%m%d")}.xlsx'
            )
    
    except Exception as e:
        logger.error(f"Error exporting records: {str(e)}")
        return jsonify({"error": str(e)}), 500
