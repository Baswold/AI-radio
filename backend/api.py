from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Upload, Playlist, StreamStatus, User
from scheduler import get_playlist_manager
from streaming_manager import get_streaming_manager
import os

api_bp = Blueprint('api', __name__)


def serialize_upload(upload, fields):
    """Convert an ``Upload`` model instance to a dictionary.

    Args:
        upload: ``Upload`` model instance to serialize.
        fields: Iterable of field names to include in the output.

    Returns:
        Dictionary containing the requested fields.
    """

    field_map = {
        'id': lambda u: u.id,
        'title': lambda u: u.title,
        'username': lambda u: u.user.username,
        'description': lambda u: u.description,
        'media_type': lambda u: u.media_type,
        'category': lambda u: u.category,
        'duration': lambda u: u.duration,
        'played_count': lambda u: u.played_count,
        'tags': lambda u: u.tags,
        'thumbnail_url': lambda u: f'/api/media/thumbnail/{u.id}' if u.thumbnail_path else None,
        'uploaded_at': lambda u: u.uploaded_at.isoformat(),
        'status': lambda u: u.status,
        'last_played': lambda u: u.last_played.isoformat() if u.last_played else None,
    }

    return {field: field_map[field](upload) for field in fields}


# Public endpoints (no auth required)

@api_bp.route('/now-playing', methods=['GET'])
def get_now_playing():
    """Get currently playing content info"""
    try:
        playlist_manager = get_playlist_manager()
        now_playing = playlist_manager.get_current_playing()
        
        if now_playing:
            return jsonify({
                'status': 'playing',
                'data': now_playing
            }), 200
        else:
            return jsonify({
                'status': 'idle',
                'message': 'No content currently playing'
            }), 200
            
    except Exception as e:
        return jsonify({'error': 'Failed to get now playing info'}), 500

@api_bp.route('/stream-info', methods=['GET'])
def get_stream_info():
    """Get basic stream information"""
    try:
        status = StreamStatus.query.first()
        
        return jsonify({
            'stream_url': 'http://localhost:8000/stream',  # Icecast stream URL
            'listeners': status.listeners if status else 0,
            'status': 'live' if status and status.current_upload_id else 'offline'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get stream info'}), 500

@api_bp.route('/featured-content', methods=['GET'])
def get_featured_content():
    """Get featured/popular content for homepage"""
    try:
        limit = min(request.args.get('limit', 12, type=int), 50)
        
        # Get most played content from last week
        featured = Upload.query.filter_by(status='approved')\
                         .order_by(Upload.played_count.desc())\
                         .limit(limit).all()
        
        return jsonify({
            'featured': [
                serialize_upload(upload, [
                    'id', 'title', 'username', 'media_type', 'category',
                    'duration', 'played_count', 'thumbnail_url', 'uploaded_at'
                ])
                for upload in featured
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get featured content'}), 500

@api_bp.route('/explore', methods=['GET'])
def explore_content():
    """Browse all approved content with filters"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        media_type = request.args.get('type', 'all')
        category = request.args.get('category')
        sort_by = request.args.get('sort', 'recent')  # recent, popular, duration
        
        # Base query
        query = Upload.query.filter_by(status='approved')
        
        # Apply filters
        if media_type != 'all':
            query = query.filter_by(media_type=media_type)
        
        if category:
            query = query.filter_by(category=category)
        
        # Apply sorting
        if sort_by == 'popular':
            query = query.order_by(Upload.played_count.desc())
        elif sort_by == 'duration':
            query = query.order_by(Upload.duration.asc())
        else:  # recent
            query = query.order_by(Upload.uploaded_at.desc())
        
        uploads = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'uploads': [
                serialize_upload(upload, [
                    'id', 'title', 'username', 'description', 'media_type',
                    'category', 'duration', 'played_count', 'tags',
                    'thumbnail_url', 'uploaded_at'
                ])
                for upload in uploads.items
            ],
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
        return jsonify({'error': 'Failed to explore content'}), 500

@api_bp.route('/search', methods=['GET'])
def search_content():
    """Search content by title, description, or tags"""
    try:
        query_text = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        if not query_text:
            return jsonify({'error': 'Search query required'}), 400
        
        # Search in title, description, and tags
        search_pattern = f"%{query_text}%"
        
        uploads = Upload.query.filter_by(status='approved').filter(
            (Upload.title.ilike(search_pattern)) |
            (Upload.description.ilike(search_pattern)) |
            (Upload.tags.contains(query_text))
        ).order_by(Upload.uploaded_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'query': query_text,
            'results': [
                serialize_upload(upload, [
                    'id', 'title', 'username', 'description', 'media_type',
                    'category', 'duration', 'tags', 'thumbnail_url', 'uploaded_at'
                ])
                for upload in uploads.items
            ],
            'pagination': {
                'page': uploads.page,
                'pages': uploads.pages,
                'per_page': uploads.per_page,
                'total': uploads.total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Search failed'}), 500

# Media serving endpoints

@api_bp.route('/media/audio/<int:upload_id>')
def serve_audio(upload_id):
    """Serve audio files"""
    try:
        upload = Upload.query.get_or_404(upload_id)
        
        if upload.status != 'approved':
            return jsonify({'error': 'Content not available'}), 404
        
        if upload.media_type != 'audio':
            return jsonify({'error': 'Not an audio file'}), 400
        
        if not upload.filename or not os.path.exists(upload.filename):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(upload.filename, as_attachment=False)
        
    except Exception as e:
        return jsonify({'error': 'Failed to serve audio'}), 500

@api_bp.route('/media/video/<int:upload_id>')
def serve_video(upload_id):
    """Serve video files"""
    try:
        upload = Upload.query.get_or_404(upload_id)
        
        if upload.status != 'approved':
            return jsonify({'error': 'Content not available'}), 404
        
        if upload.media_type != 'video':
            return jsonify({'error': 'Not a video file'}), 400
        
        if not upload.filename or not os.path.exists(upload.filename):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(upload.filename, as_attachment=False)
        
    except Exception as e:
        return jsonify({'error': 'Failed to serve video'}), 500

@api_bp.route('/media/thumbnail/<int:upload_id>')
def serve_thumbnail(upload_id):
    """Serve thumbnail images"""
    try:
        upload = Upload.query.get_or_404(upload_id)
        
        if not upload.thumbnail_path or not os.path.exists(upload.thumbnail_path):
            # Return a default thumbnail or 404
            return jsonify({'error': 'Thumbnail not found'}), 404
        
        return send_file(upload.thumbnail_path, as_attachment=False)
        
    except Exception as e:
        return jsonify({'error': 'Failed to serve thumbnail'}), 500

# Video streaming endpoints

@api_bp.route('/video-stream/playlist.m3u8')
def serve_video_stream():
    """Serve HLS video stream playlist"""
    try:
        hls_dir = "/Users/basil_jackson/Documents/ai_radio/media/video_stream/hls"
        playlist_file = os.path.join(hls_dir, "playlist.m3u8")
        
        if not os.path.exists(playlist_file):
            return jsonify({'error': 'Video stream not available'}), 404
        
        return send_file(playlist_file, mimetype='application/vnd.apple.mpegurl')
        
    except Exception as e:
        return jsonify({'error': 'Failed to serve video stream'}), 500

@api_bp.route('/video-stream/segment/<filename>')
def serve_video_segment(filename):
    """Serve HLS video segments"""
    try:
        hls_dir = "/Users/basil_jackson/Documents/ai_radio/media/video_stream/hls"
        segment_file = os.path.join(hls_dir, filename)
        
        if not os.path.exists(segment_file) or not filename.endswith('.ts'):
            return jsonify({'error': 'Segment not found'}), 404
        
        return send_file(segment_file, mimetype='video/MP2T')
        
    except Exception as e:
        return jsonify({'error': 'Failed to serve video segment'}), 500

# Streaming control endpoints

@api_bp.route('/streaming/status', methods=['GET'])
def get_streaming_status():
    """Get current streaming status for both audio and video"""
    try:
        streaming_manager = get_streaming_manager()
        status = streaming_manager.get_streaming_status()
        
        # Add listener count
        status['audio']['listeners'] = streaming_manager.get_icecast_listeners()
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get streaming status'}), 500

# Authenticated endpoints

@api_bp.route('/playlist/current', methods=['GET'])
@login_required
def get_current_playlist():
    """Get currently active playlist"""
    try:
        current_playlist = Playlist.query.filter_by(is_active=True).first()
        
        if not current_playlist:
            return jsonify({'error': 'No active playlist'}), 404
        
        # Get playlist entries with upload details
        entries = []
        for entry in sorted(current_playlist.entries, key=lambda x: x.position):
            entries.append({
                'position': entry.position,
                'upload': serialize_upload(entry.upload, [
                    'id', 'title', 'username', 'media_type', 'duration', 'category'
                ])
            })
        
        return jsonify({
            'playlist': {
                'id': current_playlist.id,
                'name': current_playlist.name,
                'description': current_playlist.description,
                'created_at': current_playlist.created_at.isoformat(),
                'entries': entries
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get current playlist'}), 500

@api_bp.route('/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    """Get personalized content recommendations"""
    try:
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        playlist_manager = get_playlist_manager()
        recommendations = playlist_manager.generate_content_recommendations(current_user.id)
        
        return jsonify({
            'recommendations': [
                serialize_upload(upload, [
                    'id', 'title', 'username', 'media_type', 'category',
                    'duration', 'played_count', 'thumbnail_url', 'uploaded_at'
                ])
                for upload in recommendations[:limit]
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get recommendations'}), 500

@api_bp.route('/upload/<int:upload_id>', methods=['GET'])
@login_required
def get_upload_details(upload_id):
    """Get detailed information about a specific upload"""
    try:
        upload = Upload.query.get_or_404(upload_id)
        
        # Only show full details to the owner or if approved
        if upload.user_id != current_user.id and upload.status != 'approved':
            return jsonify({'error': 'Content not found'}), 404
        
        data = serialize_upload(upload, [
            'id', 'title', 'description', 'username', 'media_type', 'category',
            'duration', 'status', 'played_count', 'last_played', 'tags',
            'thumbnail_url', 'uploaded_at'
        ])
        data['can_edit'] = upload.user_id == current_user.id

        return jsonify({'upload': data}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get upload details'}), 500

@api_bp.route('/stats/overview', methods=['GET'])
@login_required
def get_stats_overview():
    """Get platform statistics"""
    try:
        total_uploads = Upload.query.filter_by(status='approved').count()
        total_users = User.query.count()
        total_audio = Upload.query.filter_by(status='approved', media_type='audio').count()
        total_video = Upload.query.filter_by(status='approved', media_type='video').count()
        
        # User's personal stats
        user_uploads = Upload.query.filter_by(user_id=current_user.id).count()
        user_total_plays = db.session.query(db.func.sum(Upload.played_count))\
                                   .filter_by(user_id=current_user.id).scalar() or 0
        
        return jsonify({
            'platform': {
                'total_content': total_uploads,
                'total_users': total_users,
                'audio_content': total_audio,
                'video_content': total_video
            },
            'user': {
                'uploads': user_uploads,
                'total_plays': user_total_plays
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get stats'}), 500

# Admin endpoints (simplified - should check for admin role)

@api_bp.route('/admin/pending', methods=['GET'])
@login_required
def get_pending_uploads():
    """Get uploads pending approval (admin only)"""
    try:
        # TODO: Add admin role check
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        pending = Upload.query.filter_by(status='pending')\
                        .order_by(Upload.uploaded_at.asc())\
                        .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'pending': [
                serialize_upload(upload, [
                    'id', 'title', 'username', 'media_type', 'duration', 'uploaded_at'
                ])
                for upload in pending.items
            ],
            'pagination': {
                'page': pending.page,
                'pages': pending.pages,
                'total': pending.total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get pending uploads'}), 500

@api_bp.route('/admin/approve/<int:upload_id>', methods=['POST'])
@login_required
def approve_upload(upload_id):
    """Approve an upload (admin only)"""
    try:
        # TODO: Add admin role check
        upload = Upload.query.get_or_404(upload_id)
        
        if upload.status != 'pending':
            return jsonify({'error': 'Upload not pending approval'}), 400
        
        upload.status = 'approved'
        db.session.commit()
        
        return jsonify({'message': 'Upload approved successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to approve upload'}), 500

# Streaming management endpoints (admin)

@api_bp.route('/admin/streaming/start', methods=['POST'])
@login_required
def start_streaming():
    """Start streaming services (admin only)"""
    try:
        # TODO: Add admin role check
        streaming_manager = get_streaming_manager()
        service = request.json.get('service', 'all')  # 'audio', 'video', or 'all'
        
        if service == 'audio':
            result = streaming_manager.start_audio_streaming()
        elif service == 'video':
            result = streaming_manager.start_video_streaming()
        else:  # all
            results = streaming_manager.start_all_streaming()
            result = all(results.values())
        
        if result:
            return jsonify({'message': f'{service.title()} streaming started successfully'}), 200
        else:
            return jsonify({'error': f'Failed to start {service} streaming'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Failed to start streaming'}), 500

@api_bp.route('/admin/streaming/stop', methods=['POST'])
@login_required
def stop_streaming():
    """Stop streaming services (admin only)"""
    try:
        # TODO: Add admin role check
        streaming_manager = get_streaming_manager()
        service = request.json.get('service', 'all')  # 'audio', 'video', or 'all'
        
        if service == 'audio':
            result = streaming_manager.stop_audio_streaming()
        elif service == 'video':
            result = streaming_manager.stop_video_streaming()
        else:  # all
            results = streaming_manager.stop_all_streaming()
            result = all(results.values())
        
        if result:
            return jsonify({'message': f'{service.title()} streaming stopped successfully'}), 200
        else:
            return jsonify({'error': f'Failed to stop {service} streaming'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Failed to stop streaming'}), 500

@api_bp.route('/admin/streaming/restart', methods=['POST'])
@login_required
def restart_streaming():
    """Restart streaming services (admin only)"""
    try:
        # TODO: Add admin role check
        streaming_manager = get_streaming_manager()
        results = streaming_manager.restart_streaming()
        
        return jsonify({
            'message': 'Streaming services restarted',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to restart streaming'}), 500

@api_bp.route('/admin/streaming/skip-track', methods=['POST'])
@login_required
def skip_track():
    """Skip currently playing track (admin only)"""
    try:
        # TODO: Add admin role check
        streaming_manager = get_streaming_manager()
        result = streaming_manager.skip_current_track()
        
        if result:
            return jsonify({'message': 'Track skipped successfully'}), 200
        else:
            return jsonify({'error': 'Failed to skip track'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Failed to skip track'}), 500