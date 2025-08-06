"""
Playlist scheduler and management system for the AI radio platform.
Handles playlist generation, content scheduling, and streaming coordination.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import subprocess
from models import db, Upload, Playlist, PlaylistEntry, Segment, StreamStatus
from ai_generator import create_ai_host, create_tts_handler

class PlaylistManager:
    def __init__(self):
        self.ai_host = create_ai_host()
        self.tts_handler = create_tts_handler()
        self.playlist_dir = "/Users/basil_jackson/Documents/ai_radio/media/playlists"
        os.makedirs(self.playlist_dir, exist_ok=True)
    
    def create_daily_playlist(self, date: datetime = None) -> Playlist:
        """Create a balanced playlist for a specific day"""
        if not date:
            date = datetime.now()
        
        # Get approved content
        audio_content = Upload.query.filter_by(
            status='approved', 
            media_type='audio'
        ).all()
        
        video_content = Upload.query.filter_by(
            status='approved', 
            media_type='video'
        ).all()
        
        if not audio_content and not video_content:
            print("No approved content available for playlist")
            return None
        
        # Create playlist with balanced content
        playlist_name = f"Daily Mix - {date.strftime('%Y-%m-%d')}"
        playlist = Playlist(
            name=playlist_name,
            description=f"AI-curated daily playlist for {date.strftime('%B %d, %Y')}",
            is_active=False  # Will be activated when scheduled
        )
        
        db.session.add(playlist)
        db.session.flush()  # Get the ID
        
        # Balance content types (70% audio, 30% video for variety)
        total_slots = 50  # ~6-8 hours of content assuming 7-10 min average
        audio_slots = int(total_slots * 0.7)
        video_slots = total_slots - audio_slots
        
        selected_content = []
        
        # Select audio content
        if audio_content:
            audio_picks = random.sample(
                audio_content, 
                min(audio_slots, len(audio_content))
            )
            selected_content.extend(audio_picks)
        
        # Select video content
        if video_content:
            video_picks = random.sample(
                video_content, 
                min(video_slots, len(video_content))
            )
            selected_content.extend(video_picks)
        
        # Shuffle the combined content
        random.shuffle(selected_content)
        
        # Create playlist entries
        for position, upload in enumerate(selected_content):
            entry = PlaylistEntry(
                playlist_id=playlist.id,
                upload_id=upload.id,
                position=position
            )
            db.session.add(entry)
        
        db.session.commit()
        return playlist
    
    def generate_playlist_segments(self, playlist_id: int):
        """Generate DJ intro segments for all items in playlist"""
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return False
        
        for entry in playlist.entries:
            upload = entry.upload
            
            # Check if segment already exists
            existing_segment = Segment.query.filter_by(upload_id=upload.id).first()
            if existing_segment:
                continue
            
            # Generate AI intro
            metadata = {
                'title': upload.title,
                'username': upload.user.username,
                'media_type': upload.media_type,
                'description': upload.description,
                'category': upload.category
            }
            
            intro_result = self.ai_host.generate_intro(metadata)
            if not intro_result:
                continue
            
            # Generate TTS audio
            audio_filename = f"intro_{upload.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            audio_path = self.tts_handler.generate_audio(
                intro_result['text'], 
                audio_filename
            )
            
            # Create segment
            segment = Segment(
                upload_id=upload.id,
                dj_intro_text=intro_result['text'],
                dj_intro_audio=audio_path,
                position_in_playlist=entry.position
            )
            
            db.session.add(segment)
        
        db.session.commit()
        return True
    
    def export_playlist_to_m3u(self, playlist_id: int) -> str:
        """Export playlist to M3U format for Liquidsoap"""
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return None
        
        m3u_path = os.path.join(self.playlist_dir, f"playlist_{playlist_id}.m3u")
        
        with open(m3u_path, 'w') as f:
            f.write("#EXTM3U\n")
            
            for entry in sorted(playlist.entries, key=lambda x: x.position):
                upload = entry.upload
                segment = Segment.query.filter_by(upload_id=upload.id).first()
                
                # Write DJ intro if exists
                if segment and segment.dj_intro_audio and os.path.exists(segment.dj_intro_audio):
                    f.write(f"#EXTINF:-1,DJ Intro - {upload.title}\n")
                    f.write(f"{segment.dj_intro_audio}\n")
                
                # Write main content
                if upload.filename and os.path.exists(upload.filename):
                    duration = upload.duration or -1
                    f.write(f"#EXTINF:{duration},{upload.title} - {upload.user.username}\n")
                    f.write(f"{upload.filename}\n")
        
        return m3u_path
    
    def activate_playlist(self, playlist_id: int):
        """Activate a playlist for streaming"""
        # Deactivate current playlist
        current = Playlist.query.filter_by(is_active=True).first()
        if current:
            current.is_active = False
        
        # Activate new playlist
        new_playlist = Playlist.query.get(playlist_id)
        if new_playlist:
            new_playlist.is_active = True
            db.session.commit()
            
            # Export to M3U and notify streaming system
            m3u_path = self.export_playlist_to_m3u(playlist_id)
            if m3u_path:
                self.update_streaming_playlist(m3u_path)
            
            return True
        return False
    
    def update_streaming_playlist(self, m3u_path: str):
        """Update the streaming system with new playlist"""
        try:
            # Copy to expected location for Liquidsoap
            current_playlist_path = os.path.join(self.playlist_dir, "current.m3u")
            subprocess.run(['cp', m3u_path, current_playlist_path], check=True)
            
            # Optionally reload Liquidsoap (if running)
            # This would typically involve sending a signal to Liquidsoap
            # For now, we'll just update the file and Liquidsoap will pick it up
            print(f"Updated streaming playlist: {current_playlist_path}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error updating streaming playlist: {e}")
    
    def get_current_playing(self) -> Optional[Dict]:
        """Get information about currently playing content"""
        status = StreamStatus.query.first()
        if not status or not status.current_upload_id:
            return None
        
        upload = Upload.query.get(status.current_upload_id)
        segment = Segment.query.get(status.current_segment_id) if status.current_segment_id else None
        
        return {
            'upload': {
                'id': upload.id,
                'title': upload.title,
                'username': upload.user.username,
                'media_type': upload.media_type,
                'category': upload.category,
                'duration': upload.duration,
                'thumbnail_path': upload.thumbnail_path
            },
            'segment': {
                'id': segment.id,
                'dj_intro_text': segment.dj_intro_text
            } if segment else None,
            'started_at': status.started_at.isoformat() if status.started_at else None,
            'listeners': status.listeners
        }
    
    def update_now_playing(self, upload_id: int, segment_id: int = None):
        """Update the currently playing status"""
        status = StreamStatus.query.first()
        if not status:
            status = StreamStatus()
            db.session.add(status)
        
        status.current_upload_id = upload_id
        status.current_segment_id = segment_id
        status.started_at = datetime.utcnow()
        
        # Increment play count
        upload = Upload.query.get(upload_id)
        if upload:
            upload.played_count += 1
            upload.last_played = datetime.utcnow()
        
        db.session.commit()
    
    def generate_content_recommendations(self, user_id: int = None) -> List[Upload]:
        """Generate content recommendations based on play history and popularity"""
        # Base query for approved content
        query = Upload.query.filter_by(status='approved')
        
        # Exclude recently played content (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        query = query.filter(
            (Upload.last_played == None) | 
            (Upload.last_played < recent_cutoff)
        )
        
        # Prioritize content with fewer plays
        query = query.order_by(Upload.played_count.asc())
        
        # Get a mix of content types
        recommendations = []
        
        # Get some fresh content (never played)
        fresh_content = query.filter(Upload.played_count == 0).limit(10).all()
        recommendations.extend(fresh_content)
        
        # Get some popular but not overplayed content
        popular_content = query.filter(
            Upload.played_count.between(1, 5)
        ).order_by(Upload.played_count.desc()).limit(10).all()
        recommendations.extend(popular_content)
        
        # Remove duplicates and shuffle
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec.id not in seen:
                unique_recommendations.append(rec)
                seen.add(rec.id)
        
        random.shuffle(unique_recommendations)
        return unique_recommendations[:20]


class SchedulerService:
    """Main scheduler service for automated playlist management"""
    
    def __init__(self):
        self.playlist_manager = PlaylistManager()
    
    def run_daily_scheduling(self):
        """Run daily playlist creation and scheduling"""
        try:
            # Create today's playlist
            today = datetime.now()
            playlist = self.playlist_manager.create_daily_playlist(today)
            
            if playlist:
                # Generate segments
                self.playlist_manager.generate_playlist_segments(playlist.id)
                
                # Activate playlist
                self.playlist_manager.activate_playlist(playlist.id)
                
                print(f"Successfully created and activated playlist: {playlist.name}")
                return playlist
            else:
                print("Failed to create daily playlist")
                return None
                
        except Exception as e:
            print(f"Error in daily scheduling: {e}")
            return None
    
    def cleanup_old_playlists(self, days_to_keep: int = 7):
        """Clean up old playlists to save space"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        old_playlists = Playlist.query.filter(
            Playlist.created_at < cutoff_date,
            Playlist.is_active == False
        ).all()
        
        for playlist in old_playlists:
            # Remove M3U file
            m3u_path = os.path.join(self.playlist_manager.playlist_dir, f"playlist_{playlist.id}.m3u")
            if os.path.exists(m3u_path):
                os.remove(m3u_path)
            
            # Delete playlist entries and segments
            PlaylistEntry.query.filter_by(playlist_id=playlist.id).delete()
            
            # Delete playlist
            db.session.delete(playlist)
        
        db.session.commit()
        print(f"Cleaned up {len(old_playlists)} old playlists")


# Utility functions
def get_playlist_manager() -> PlaylistManager:
    """Get a playlist manager instance"""
    return PlaylistManager()

def get_scheduler_service() -> SchedulerService:
    """Get a scheduler service instance"""
    return SchedulerService()