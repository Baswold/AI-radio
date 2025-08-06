from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import db, Media
from upload_handler import UploadHandler
import os

upload_bp = Blueprint('upload', __name__)
handler = UploadHandler()

@upload_bp.route('/', methods=['POST'])
@login_required
def upload_file():
    """Handle file uploads with validation and processing."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    try:
        # Process the upload
        result = handler.process_upload(file)
        
        # Create database entry
        media = Media(
            filename=result['upload_id'],
            original_name=result['original_name'],
            status=result['status'],
            size=result['size']
        )
        db.session.add(media)
        db.session.commit()
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500
