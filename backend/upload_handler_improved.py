"""
Improved upload handler with comprehensive validation, security, and async processing.
This module replaces the old upload_handler.py with better practices.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Upload
from middleware import sanitize_filename, validate_file_path
import hashlib
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
import time

upload_bp = Blueprint('upload', __name__)


class MediaValidator:
    """Validates media files before processing"""

    def __init__(self, config):
        self.config = config
        self.allowed_audio = config.get('ALLOWED_AUDIO_EXTENSIONS', {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac'})
        self.allowed_video = config.get('ALLOWED_VIDEO_EXTENSIONS', {'mp4', 'webm', 'avi', 'mov', 'mkv'})
        self.allowed_mime = config.get('ALLOWED_MIME_TYPES', set())
        self.max_duration = config.get('MAX_MEDIA_DURATION', 3600)
        self.max_size = config.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)

    def validate_file_extension(self, filename, media_type):
        """Validate file extension"""
        ext = self.get_file_extension(filename)
        if not ext:
            raise ValueError('File has no extension')

        if media_type == 'audio':
            if ext not in self.allowed_audio:
                raise ValueError(f'Invalid audio format. Allowed: {", ".join(self.allowed_audio)}')
        elif media_type == 'video':
            if ext not in self.allowed_video:
                raise ValueError(f'Invalid video format. Allowed: {", ".join(self.allowed_video)}')
        else:
            raise ValueError('Media type must be audio or video')

        return ext

    def validate_mime_type(self, file):
        """Validate MIME type using python-magic"""
        try:
            import magic
            # Read first 2048 bytes for MIME detection
            file_start = file.read(2048)
            file.seek(0)

            mime = magic.from_buffer(file_start, mime=True)

            if mime not in self.allowed_mime:
                current_app.logger.warning(f'Rejected file with MIME type: {mime}')
                raise ValueError(f'Invalid file type: {mime}. This does not appear to be a valid media file.')

            return mime
        except ImportError:
            current_app.logger.warning('python-magic not available, skipping MIME validation')
            return None

    def scan_malware(self, file_path):
        """Scan file for malware using ClamAV (if enabled)"""
        if not current_app.config.get('ENABLE_MALWARE_SCAN', False):
            return True

        try:
            import pyclamd
            cd = pyclamd.ClamdNetworkSocket(
                host=current_app.config.get('CLAMAV_HOST', 'localhost'),
                port=current_app.config.get('CLAMAV_PORT', 3310)
            )

            if not cd.ping():
                current_app.logger.warning('ClamAV not available, skipping malware scan')
                return True

            result = cd.scan_file(file_path)
            if result:
                current_app.logger.error(f'Malware detected in {file_path}: {result}')
                raise ValueError('File failed malware scan')

            return True
        except ImportError:
            current_app.logger.warning('pyclamd not installed, skipping malware scan')
            return True
        except Exception as e:
            current_app.logger.error(f'Malware scan error: {e}')
            # Don't fail upload if scanner is unavailable
            return True

    @staticmethod
    def get_file_extension(filename):
        """Get file extension safely"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


class MediaProcessor:
    """Processes media files (audio/video conversion and optimization)"""

    def __init__(self, config):
        self.config = config
        self.validator = MediaValidator(config)
        self.upload_dir = Path(config.get('UPLOAD_FOLDER'))
        self.media_dir = Path(config.get('MEDIA_FOLDER'))
        self.pending_dir = Path(config.get('PENDING_DIR'))
        self.audio_dir = Path(config.get('AUDIO_DIR'))
        self.video_dir = Path(config.get('VIDEO_DIR'))
        self.thumbnail_dir = Path(config.get('THUMBNAIL_DIR'))

        # Ensure directories exist
        for directory in [self.upload_dir, self.media_dir, self.pending_dir,
                          self.audio_dir, self.video_dir, self.thumbnail_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_file_hash(self, file_path):
        """Generate SHA256 hash of file (memory efficient)"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_media_info(self, filepath):
        """Use ffprobe to get media information"""
        try:
            cmd = [
                current_app.config.get('FFPROBE_BINARY', 'ffprobe'),
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                str(filepath)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

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
                'size': int(format_info.get('size', 0)),
                'bitrate': int(format_info.get('bit_rate', 0))
            }
        except subprocess.TimeoutExpired:
            current_app.logger.error('FFprobe timeout')
            raise Exception('Media info extraction timed out')
        except Exception as e:
            current_app.logger.error(f"Error getting media info: {e}")
            return None

    def process_audio(self, input_path, output_path):
        """Convert and normalize audio"""
        try:
            start_time = time.time()

            cmd = [
                current_app.config.get('FFMPEG_BINARY', 'ffmpeg'),
                '-i', str(input_path),
                '-codec:a', 'libmp3lame',
                '-b:a', '192k',
                '-ar', '44100',
                '-ac', '2',
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                '-threads', str(current_app.config.get('FFMPEG_THREADS', 2)),
                '-y', str(output_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )

            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")

            duration = time.time() - start_time
            current_app.logger.info(f'Audio processing completed in {duration:.2f}s')

            return True
        except subprocess.TimeoutExpired:
            current_app.logger.error('FFmpeg audio processing timeout')
            raise Exception('Audio processing timed out')
        except Exception as e:
            current_app.logger.error(f"Error processing audio: {e}")
            return False

    def process_video(self, input_path, output_path, thumbnail_path):
        """Convert video and generate thumbnail"""
        try:
            start_time = time.time()

            # Convert video
            video_cmd = [
                current_app.config.get('FFMPEG_BINARY', 'ffmpeg'),
                '-i', str(input_path),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'fast',
                '-crf', '23',
                '-maxrate', '2M',
                '-bufsize', '4M',
                '-vf', 'scale=-2:720',  # Scale to 720p height, maintain aspect ratio
                '-threads', str(current_app.config.get('FFMPEG_THREADS', 2)),
                '-y', str(output_path)
            ]

            result = subprocess.run(
                video_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )

            if result.returncode != 0:
                raise Exception(f"Video conversion failed: {result.stderr}")

            # Generate thumbnail
            thumb_cmd = [
                current_app.config.get('FFMPEG_BINARY', 'ffmpeg'),
                '-i', str(output_path),
                '-ss', '5',  # 5 seconds in
                '-vframes', '1',
                '-vf', 'scale=320:240',
                '-y', str(thumbnail_path)
            ]

            subprocess.run(thumb_cmd, capture_output=True, text=True, timeout=30)

            duration = time.time() - start_time
            current_app.logger.info(f'Video processing completed in {duration:.2f}s')

            return True
        except subprocess.TimeoutExpired:
            current_app.logger.error('FFmpeg video processing timeout')
            raise Exception('Video processing timed out')
        except Exception as e:
            current_app.logger.error(f"Error processing video: {e}")
            return False

    def process_upload(self, file, metadata):
        """Main processing function"""
        temp_path = None

        try:
            # Validate file format
            ext = self.validator.validate_file_extension(file.filename, metadata['media_type'])

            # Validate MIME type
            self.validator.validate_mime_type(file)

            # Create secure filename
            original_filename = secure_filename(file.filename)
            original_filename = sanitize_filename(original_filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{timestamp}_{current_user.id}_{original_filename}"

            # Save to pending directory first
            temp_path = self.pending_dir / base_name
            file.save(str(temp_path))

            # Get file size
            file_size = temp_path.stat().st_size

            # Scan for malware
            self.validator.scan_malware(temp_path)

            # Generate file hash for duplicate detection
            file_hash = self.get_file_hash(temp_path)

            # Check for duplicates
            existing = Upload.query.filter_by(file_hash=file_hash).first()
            if existing:
                temp_path.unlink()
                raise ValueError(f"This file has already been uploaded (Upload ID: {existing.id})")

            # Get media info
            media_info = self.get_media_info(temp_path)
            if not media_info:
                if temp_path.exists():
                    temp_path.unlink()
                raise ValueError("Could not read media file. File may be corrupted.")

            # Validate duration
            if media_info['duration'] > self.validator.max_duration:
                if temp_path.exists():
                    temp_path.unlink()
                max_minutes = self.validator.max_duration / 60
                raise ValueError(f"File too long (max {max_minutes:.0f} minutes)")

            # Validate media has appropriate streams
            if metadata['media_type'] == 'audio' and not media_info['has_audio']:
                if temp_path.exists():
                    temp_path.unlink()
                raise ValueError("Audio file has no audio stream")

            if metadata['media_type'] == 'video' and not media_info['has_video']:
                if temp_path.exists():
                    temp_path.unlink()
                raise ValueError("Video file has no video stream")

            # Process based on media type
            processed_path = None
            thumbnail_path = None

            if metadata['media_type'] == 'audio':
                processed_filename = f"{base_name}.mp3"
                processed_path = self.audio_dir / processed_filename

                current_app.logger.info(f'Processing audio file: {original_filename}')
                if not self.process_audio(temp_path, processed_path):
                    if temp_path.exists():
                        temp_path.unlink()
                    raise ValueError("Audio processing failed")

            elif metadata['media_type'] == 'video':
                processed_filename = f"{base_name}.mp4"
                processed_path = self.video_dir / processed_filename
                thumbnail_filename = f"{base_name}_thumb.jpg"
                thumbnail_path = self.thumbnail_dir / thumbnail_filename

                current_app.logger.info(f'Processing video file: {original_filename}')
                if not self.process_video(temp_path, processed_path, thumbnail_path):
                    if temp_path.exists():
                        temp_path.unlink()
                    raise ValueError("Video processing failed")

            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

            return {
                'filepath': str(processed_path),
                'thumbnail_path': str(thumbnail_path) if thumbnail_path else None,
                'duration': int(media_info['duration']),
                'file_hash': file_hash,
                'file_size': file_size,
                'original_filename': original_filename
            }

        except Exception as e:
            # Clean up on error
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            raise e


@upload_bp.route('/', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '' or not file:
            return jsonify({'error': 'No file selected'}), 400

        # Get metadata
        metadata = {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
            'media_type': request.form.get('media_type', '').strip().lower(),
            'category': request.form.get('category', '').strip(),
            'tags': [tag.strip() for tag in request.form.get('tags', '').split(',') if tag.strip()]
        }

        # Validation
        if not metadata['title']:
            return jsonify({'error': 'Title is required'}), 400

        if len(metadata['title']) > 200:
            return jsonify({'error': 'Title too long (max 200 characters)'}), 400

        if metadata['description'] and len(metadata['description']) > 5000:
            return jsonify({'error': 'Description too long (max 5000 characters)'}), 400

        if metadata['media_type'] not in ['audio', 'video']:
            return jsonify({'error': 'Media type must be audio or video'}), 400

        if metadata['category'] and len(metadata['category']) > 50:
            return jsonify({'error': 'Category too long (max 50 characters)'}), 400

        if len(metadata['tags']) > 10:
            return jsonify({'error': 'Too many tags (max 10)'}), 400

        # Process upload
        processor = MediaProcessor(current_app.config)
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
            file_size=result['file_size'],
            tags=metadata['tags'],
            status='pending'  # Requires approval
        )

        db.session.add(upload)
        db.session.commit()

        current_app.logger.info(
            f'Upload successful: user={current_user.username}, '
            f'file={result["original_filename"]}, '
            f'size={result["file_size"]} bytes'
        )

        # Queue AI intro generation (async via Celery)
        if current_app.config.get('ENABLE_AI_INTROS', True):
            try:
                from celery_tasks import queue_intro_generation
                queue_intro_generation(upload.id)
                current_app.logger.info(f'Queued AI intro generation for upload {upload.id}')
            except Exception as e:
                current_app.logger.warning(f'Failed to queue AI intro: {e}')

        return jsonify({
            'message': 'Upload successful',
            'upload_id': upload.id,
            'status': 'pending_approval',
            'duration': result['duration'],
            'file_size': result['file_size']
        }), 201

    except ValueError as e:
        current_app.logger.warning(f'Upload validation failed: {e}')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Upload error: {e}', exc_info=True)
        return jsonify({'error': 'Upload failed. Please try again.'}), 500


@upload_bp.route('/my-uploads', methods=['GET'])
@login_required
def get_user_uploads():
    """Get user's uploads"""
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
                'file_size': upload.file_size,
                'status': upload.status,
                'uploaded_at': upload.uploaded_at.isoformat(),
                'played_count': upload.played_count,
                'tags': upload.tags
            } for upload in uploads.items],
            'pagination': {
                'page': uploads.page,
                'pages': uploads.pages,
                'per_page': uploads.per_page,
                'total': uploads.total,
                'has_prev': uploads.has_prev,
                'has_next': uploads.has_next
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f'Failed to fetch uploads: {e}')
        return jsonify({'error': 'Failed to fetch uploads'}), 500
