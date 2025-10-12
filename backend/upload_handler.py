from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Upload
import hashlib
import os
import subprocess
import json
from datetime import datetime

upload_bp = Blueprint('upload', __name__)

class MediaProcessor:
    ALLOWED_AUDIO = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac'}
    ALLOWED_VIDEO = {'mp4', 'webm', 'avi', 'mov', 'mkv'}
    ALLOWED_MIME = {'audio/mpeg', 'audio/wav', 'video/mp4'}
    MAX_DURATION = 3600  # 1 hour max

    def __init__(self, upload_dir=None):
        self.upload_dir = upload_dir or current_app.config.get('UPLOAD_FOLDER')

    def validate_file(self, file):
        """Validate basic file type and perform malware scan stub."""
        import magic

        # Check MIME type
        mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)
        if mime not in self.ALLOWED_MIME:
            raise ValueError(f'Invalid file type: {mime}')

        # TODO: Integrate with a malware scanner such as ClamAV
        # Currently this is a stub and does not perform any scanning.
        
    def get_file_extension(self, filename):
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def is_allowed_file(self, filename, media_type):
        ext = self.get_file_extension(filename)
        if media_type == 'audio':
            return ext in self.ALLOWED_AUDIO
        elif media_type == 'video':
            return ext in self.ALLOWED_VIDEO
        return False
    
    def get_file_hash(self, file):
        hasher = hashlib.sha256()
        chunk_size = 4096
        for chunk in iter(lambda: file.read(chunk_size), b""):
            hasher.update(chunk)
        file.seek(0)  # Reset file pointer
        return hasher.hexdigest()
    
    def get_media_info(self, filepath):
        """Use ffprobe to get media information"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', filepath
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFprobe failed: {result.stderr}")
            
            info = json.loads(result.stdout)
            format_info = info.get('format', {})
            duration = float(format_info.get('duration', 0))
            
            # Get video/audio stream info
            streams = info.get('streams', [])
            video_streams = [s for s in streams if s.get('codec_type') == 'video']
            audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
            
            return {
                'duration': duration,
                'has_video': len(video_streams) > 0,
                'has_audio': len(audio_streams) > 0,
                'format': format_info.get('format_name', ''),
                'size': int(format_info.get('size', 0))
            }
        except Exception as e:
            print(f"Error getting media info: {e}")
            return None
    
    def process_audio(self, input_path, output_path):
        """Convert and normalize audio"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-codec:a', 'libmp3lame',
                '-b:a', '192k',
                '-ar', '44100',
                '-ac', '2',
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
                
            return True
        except Exception as e:
            print(f"Error processing audio: {e}")
            return False
    
    def process_video(self, input_path, output_path, thumbnail_path):
        """Convert video and generate thumbnail"""
        try:
            # Convert video
            video_cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'fast',
                '-crf', '23',
                '-maxrate', '2M',
                '-bufsize', '4M',
                '-vf', 'scale=-2:720',  # Scale to 720p height, maintain aspect ratio
                '-y', output_path
            ]
            
            result = subprocess.run(video_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Video conversion failed: {result.stderr}")
            
            # Generate thumbnail
            thumb_cmd = [
                'ffmpeg', '-i', output_path,
                '-ss', '5',  # 5 seconds in
                '-vframes', '1',
                '-vf', 'scale=320:240',
                '-y', thumbnail_path
            ]
            
            subprocess.run(thumb_cmd, capture_output=True, text=True)
            
            return True
        except Exception as e:
            print(f"Error processing video: {e}")
            return False
    
    def process_upload(self, file, metadata):
        """Main processing function"""
        try:
            # Validate file format
            if not self.is_allowed_file(file.filename, metadata['media_type']):
                raise ValueError("Invalid file format")

            # Basic validation and malware scan stub
            self.validate_file(file)

            # Generate file hash for duplicate detection
            file_hash = self.get_file_hash(file)
            
            # Check for duplicates
            existing = Upload.query.filter_by(file_hash=file_hash).first()
            if existing:
                raise ValueError("File already exists")
            
            # Create secure filename
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{timestamp}_{current_user.id}_{filename}"
            
            # Save original file
            pending_dir = os.path.join(self.upload_dir, 'pending')
            os.makedirs(pending_dir, exist_ok=True)
            temp_path = os.path.join(pending_dir, base_name)
            file.save(temp_path)
            
            # Get media info
            media_info = self.get_media_info(temp_path)
            if not media_info:
                os.remove(temp_path)
                raise ValueError("Could not read media file")
            
            # Validate duration
            if media_info['duration'] > self.MAX_DURATION:
                os.remove(temp_path)
                raise ValueError(f"File too long (max {self.MAX_DURATION/60:.0f} minutes)")
            
            # Process based on media type
            processed_path = None
            thumbnail_path = None
            
            if metadata['media_type'] == 'audio':
                audio_dir = os.path.join(current_app.config['MEDIA_FOLDER'], 'audio')
                os.makedirs(audio_dir, exist_ok=True)
                processed_path = os.path.join(audio_dir, f"{base_name}.mp3")
                
                if not self.process_audio(temp_path, processed_path):
                    os.remove(temp_path)
                    raise ValueError("Audio processing failed")
            
            elif metadata['media_type'] == 'video':
                video_dir = os.path.join(current_app.config['MEDIA_FOLDER'], 'video')
                os.makedirs(video_dir, exist_ok=True)
                processed_path = os.path.join(video_dir, f"{base_name}.mp4")
                thumbnail_path = os.path.join(video_dir, f"{base_name}_thumb.jpg")
                
                if not self.process_video(temp_path, processed_path, thumbnail_path):
                    os.remove(temp_path)
                    raise ValueError("Video processing failed")
            
            # Clean up temp file
            os.remove(temp_path)
            
            return {
                'filepath': processed_path,
                'thumbnail_path': thumbnail_path,
                'duration': int(media_info['duration']),
                'file_hash': file_hash,
                'original_size': media_info['size']
            }
            
        except Exception as e:
            # Clean up on error
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

@upload_bp.route('/', methods=['POST'])
@login_required
def upload_file():
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get metadata
        metadata = {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
            'media_type': request.form.get('media_type', '').strip(),
            'category': request.form.get('category', '').strip(),
            'tags': request.form.get('tags', '').split(',') if request.form.get('tags') else []
        }
        
        # Validation
        if not metadata['title']:
            return jsonify({'error': 'Title is required'}), 400
        
        if metadata['media_type'] not in ['audio', 'video']:
            return jsonify({'error': 'Media type must be audio or video'}), 400
        
        if len(metadata['title']) > 200:
            return jsonify({'error': 'Title too long (max 200 characters)'}), 400
        
        # Process upload
        processor = MediaProcessor()
        result = processor.process_upload(file, metadata)
        
        # Create database record
        upload = Upload(
            user_id=current_user.id,
            title=metadata['title'],
            description=metadata['description'],
            media_type=metadata['media_type'],
            category=metadata['category'],
            filename=result['filepath'],
            thumbnail_path=result.get('thumbnail_path'),
            duration=result['duration'],
            file_hash=result['file_hash'],
            tags=metadata['tags'],
            status='pending'  # Requires approval
        )
        
        db.session.add(upload)
        db.session.commit()
        
        # Queue AI intro generation (will be handled by Celery later)
        # For now, just return success
        
        return jsonify({
            'message': 'Upload successful',
            'upload_id': upload.id,
            'status': 'pending_approval'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@upload_bp.route('/my-uploads', methods=['GET'])
@login_required
def get_user_uploads():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        uploads = Upload.query.filter_by(user_id=current_user.id)\
                         .order_by(Upload.uploaded_at.desc())\
                         .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'uploads': [{
                'id': upload.id,
                'title': upload.title,
                'description': upload.description,
                'media_type': upload.media_type,
                'category': upload.category,
                'duration': upload.duration,
                'status': upload.status,
                'uploaded_at': upload.uploaded_at.isoformat(),
                'played_count': upload.played_count,
                'tags': upload.tags
            } for upload in uploads.items],
            'pagination': {
                'page': uploads.page,
                'pages': uploads.pages,
                'per_page': uploads.per_page,
                'total': uploads.total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch uploads'}), 500