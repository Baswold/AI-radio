"""
Celery tasks for background processing in the AI Radio platform.
Handles AI intro generation, media processing, and scheduled tasks.
"""

from celery import Celery
from celery.schedules import crontab
from models import db, Upload, Segment
from ai_generator import create_ai_host, create_tts_handler
from scheduler import get_scheduler_service
import os

# Initialize Celery
celery = Celery('ai_radio_tasks')

# Configuration
celery.conf.update(
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'ai_radio_tasks.generate_dj_intro': {'queue': 'ai_processing'},
        'ai_radio_tasks.process_uploaded_media': {'queue': 'media_processing'},
        'ai_radio_tasks.create_daily_playlist': {'queue': 'scheduling'}
    }
)

# Scheduled tasks
celery.conf.beat_schedule = {
    'create-daily-playlist': {
        'task': 'ai_radio_tasks.create_daily_playlist',
        'schedule': crontab(hour=6, minute=0),  # 6 AM daily
    },
    'cleanup-old-playlists': {
        'task': 'ai_radio_tasks.cleanup_old_playlists',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'health-check': {
        'task': 'ai_radio_tasks.health_check',
        'schedule': 300.0,  # Every 5 minutes
    },
}

@celery.task(bind=True, max_retries=3)
def generate_dj_intro(self, upload_id):
    """
    Generate AI DJ intro for uploaded content
    
    Args:
        upload_id: ID of the Upload record
        
    Returns:
        dict: Success/failure status
    """
    try:
        # Import app context here to avoid circular imports
        from app import create_app
        app = create_app()
        
        with app.app_context():
            upload = Upload.query.get(upload_id)
            if not upload:
                return {'status': 'error', 'message': 'Upload not found'}
            
            # Check if intro already exists
            existing_segment = Segment.query.filter_by(upload_id=upload_id).first()
            if existing_segment:
                return {'status': 'skipped', 'message': 'Intro already exists'}
            
            # Initialize AI components
            ai_host = create_ai_host()
            tts_handler = create_tts_handler()
            
            # Prepare metadata
            metadata = {
                'title': upload.title,
                'username': upload.user.username,
                'media_type': upload.media_type,
                'description': upload.description,
                'category': upload.category
            }
            
            # Generate intro text
            intro_result = ai_host.generate_intro(metadata)
            if not intro_result:
                raise Exception("Failed to generate intro text")
            
            # Generate audio
            audio_filename = f"intro_{upload_id}_{int(upload.uploaded_at.timestamp())}"
            audio_path = tts_handler.generate_audio(intro_result['text'], audio_filename)
            
            if not audio_path:
                raise Exception("Failed to generate intro audio")
            
            # Create segment record
            segment = Segment(
                upload_id=upload_id,
                dj_intro_text=intro_result['text'],
                dj_intro_audio=audio_path
            )
            
            db.session.add(segment)
            db.session.commit()
            
            return {
                'status': 'success',
                'segment_id': segment.id,
                'intro_text': intro_result['text'][:100] + '...',
                'personality': intro_result.get('personality', 'default')
            }
    
    except Exception as e:
        print(f"Error generating DJ intro for upload {upload_id}: {e}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries  # Exponential backoff
            raise self.retry(countdown=countdown, exc=e)
        
        return {'status': 'error', 'message': str(e)}

@celery.task(bind=True, max_retries=2)
def process_uploaded_media(self, upload_id):
    """
    Post-process uploaded media (additional optimization, analysis)
    
    Args:
        upload_id: ID of the Upload record
    """
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            upload = Upload.query.get(upload_id)
            if not upload:
                return {'status': 'error', 'message': 'Upload not found'}
            
            # Additional processing could include:
            # - Generating waveform data for audio visualization
            # - Creating additional thumbnail sizes for video
            # - Content analysis for auto-tagging
            # - Quality assessment
            
            # For now, just trigger DJ intro generation
            generate_dj_intro.delay(upload_id)
            
            return {'status': 'success', 'message': 'Media processed successfully'}
    
    except Exception as e:
        print(f"Error processing media for upload {upload_id}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=e)
        
        return {'status': 'error', 'message': str(e)}

@celery.task
def create_daily_playlist():
    """Create and activate daily playlist"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            scheduler_service = get_scheduler_service()
            playlist = scheduler_service.run_daily_scheduling()
            
            if playlist:
                return {
                    'status': 'success',
                    'playlist_id': playlist.id,
                    'playlist_name': playlist.name
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to create daily playlist'
                }
    
    except Exception as e:
        print(f"Error creating daily playlist: {e}")
        return {'status': 'error', 'message': str(e)}

@celery.task
def cleanup_old_playlists():
    """Clean up old playlists and files"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            scheduler_service = get_scheduler_service()
            scheduler_service.cleanup_old_playlists()
            
            return {'status': 'success', 'message': 'Cleanup completed'}
    
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return {'status': 'error', 'message': str(e)}

@celery.task
def generate_batch_intros(upload_ids):
    """
    Generate DJ intros for multiple uploads in batch
    
    Args:
        upload_ids: List of upload IDs
    """
    results = []
    
    for upload_id in upload_ids:
        try:
            result = generate_dj_intro.delay(upload_id)
            results.append({
                'upload_id': upload_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            results.append({
                'upload_id': upload_id,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'status': 'success',
        'total': len(upload_ids),
        'results': results
    }

@celery.task
def health_check():
    """Perform system health checks"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            # Check database connectivity
            try:
                db.session.execute('SELECT 1')
                db_status = 'healthy'
            except Exception:
                db_status = 'error'
            
            # Check AI Brain connectivity
            ai_host = create_ai_host()
            ai_brain_status = 'healthy' if ai_host.test_ai_brain_connection() else 'error'
            
            # Check disk space
            media_folder = os.environ.get('MEDIA_FOLDER', '/Users/basil_jackson/Documents/ai_radio/media')
            disk_usage = get_disk_usage(media_folder)
            disk_status = 'healthy' if disk_usage < 0.9 else 'warning'  # 90% threshold
            
            status = {
                'timestamp': celery.now(),
                'database': db_status,
                'ai_brain': ai_brain_status,
                'disk_usage': disk_usage,
                'disk_status': disk_status,
                'overall': 'healthy' if all(s in ['healthy', 'warning'] for s in [db_status, ai_brain_status, disk_status]) else 'error'
            }
            
            return status
    
    except Exception as e:
        return {
            'timestamp': celery.now(),
            'overall': 'error',
            'error': str(e)
        }

def get_disk_usage(path):
    """Get disk usage percentage for given path"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        return used / total
    except:
        return 0.0

# Utility functions for managing tasks

def queue_intro_generation(upload_id):
    """Helper function to queue DJ intro generation"""
    return generate_dj_intro.delay(upload_id)

def queue_media_processing(upload_id):
    """Helper function to queue media processing"""
    return process_uploaded_media.delay(upload_id)

def get_task_status(task_id):
    """Get status of a Celery task"""
    try:
        result = celery.AsyncResult(task_id)
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result,
            'ready': result.ready()
        }
    except Exception as e:
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        }

# Worker startup configuration
if __name__ == '__main__':
    celery.start()