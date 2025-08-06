"""
Streaming manager for AI Radio platform.
Handles both audio and video streaming integration with Icecast/Liquidsoap and video streaming services.
"""

import subprocess
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from models import db, StreamStatus, Upload, Playlist
import signal

class StreamingManager:
    def __init__(self):
        self.icecast_config = "/Users/basil_jackson/Documents/ai_radio/config/icecast.xml"
        self.liquidsoap_config = "/Users/basil_jackson/Documents/ai_radio/config/liquidsoap.liq"
        self.playlist_dir = "/Users/basil_jackson/Documents/ai_radio/media/playlists"
        self.video_stream_dir = "/Users/basil_jackson/Documents/ai_radio/media/video_stream"
        os.makedirs(self.video_stream_dir, exist_ok=True)
        
        # Process tracking
        self.icecast_process = None
        self.liquidsoap_process = None
        self.video_stream_process = None
    
    def start_audio_streaming(self) -> bool:
        """Start Icecast and Liquidsoap for audio streaming"""
        try:
            # Start Icecast server
            if not self.is_icecast_running():
                print("Starting Icecast server...")
                self.icecast_process = subprocess.Popen([
                    'icecast2', '-c', self.icecast_config
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait a moment for Icecast to start
                import time
                time.sleep(3)
                
                if not self.is_icecast_running():
                    print("Failed to start Icecast")
                    return False
            
            # Start Liquidsoap
            if not self.is_liquidsoap_running():
                print("Starting Liquidsoap...")
                self.liquidsoap_process = subprocess.Popen([
                    'liquidsoap', self.liquidsoap_config
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait for Liquidsoap to connect
                import time
                time.sleep(5)
                
                if not self.is_liquidsoap_running():
                    print("Failed to start Liquidsoap")
                    return False
            
            print("Audio streaming started successfully")
            return True
            
        except Exception as e:
            print(f"Error starting audio streaming: {e}")
            return False
    
    def stop_audio_streaming(self) -> bool:
        """Stop audio streaming services"""
        try:
            success = True
            
            # Stop Liquidsoap
            if self.liquidsoap_process:
                self.liquidsoap_process.terminate()
                self.liquidsoap_process.wait(timeout=10)
                self.liquidsoap_process = None
            
            # Stop Icecast
            if self.icecast_process:
                self.icecast_process.terminate()
                self.icecast_process.wait(timeout=10)
                self.icecast_process = None
            
            print("Audio streaming stopped")
            return success
            
        except Exception as e:
            print(f"Error stopping audio streaming: {e}")
            return False
    
    def start_video_streaming(self) -> bool:
        """Start video streaming for the video tab using HLS"""
        try:
            # Create video streaming playlist
            video_playlist = self.create_video_playlist()
            if not video_playlist:
                print("No video content available for streaming")
                return False
            
            # Start FFmpeg for video streaming (HLS)
            hls_output_dir = os.path.join(self.video_stream_dir, "hls")
            os.makedirs(hls_output_dir, exist_ok=True)
            
            # Create the HLS stream
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-stream_loop', '-1',  # Loop the playlist
                '-i', video_playlist,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'veryfast',
                '-g', '25',  # Keyframe interval
                '-sc_threshold', '0',
                '-f', 'hls',
                '-hls_time', '10',
                '-hls_list_size', '6',
                '-hls_flags', 'delete_segments',
                '-hls_segment_filename', os.path.join(hls_output_dir, 'segment_%03d.ts'),
                os.path.join(hls_output_dir, 'playlist.m3u8')
            ]
            
            print("Starting video streaming...")
            self.video_stream_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            print("Video streaming started successfully")
            return True
            
        except Exception as e:
            print(f"Error starting video streaming: {e}")
            return False
    
    def stop_video_streaming(self) -> bool:
        """Stop video streaming"""
        try:
            if self.video_stream_process:
                self.video_stream_process.terminate()
                try:
                    self.video_stream_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.video_stream_process.kill()
                self.video_stream_process = None
            
            print("Video streaming stopped")
            return True
            
        except Exception as e:
            print(f"Error stopping video streaming: {e}")
            return False
    
    def create_video_playlist(self) -> Optional[str]:
        """Create a video playlist file for FFmpeg concat"""
        try:
            # Get active playlist
            active_playlist = Playlist.query.filter_by(is_active=True).first()
            if not active_playlist:
                return None
            
            # Get video entries from the playlist
            video_entries = []
            for entry in sorted(active_playlist.entries, key=lambda x: x.position):
                upload = entry.upload
                if upload.media_type == 'video' and upload.status == 'approved':
                    if upload.filename and os.path.exists(upload.filename):
                        video_entries.append(upload)
            
            if not video_entries:
                # Fallback to any approved video content
                video_entries = Upload.query.filter_by(
                    media_type='video', 
                    status='approved'
                ).limit(20).all()
            
            if not video_entries:
                return None
            
            # Create FFmpeg concat playlist file
            playlist_file = os.path.join(self.video_stream_dir, "video_playlist.txt")
            
            with open(playlist_file, 'w') as f:
                for upload in video_entries:
                    if upload.filename and os.path.exists(upload.filename):
                        # Escape single quotes for FFmpeg
                        safe_path = upload.filename.replace("'", "'\"'\"'")
                        f.write(f"file '{safe_path}'\n")
            
            return playlist_file
            
        except Exception as e:
            print(f"Error creating video playlist: {e}")
            return None
    
    def get_streaming_status(self) -> Dict:
        """Get current status of all streaming services"""
        return {
            'audio': {
                'icecast_running': self.is_icecast_running(),
                'liquidsoap_running': self.is_liquidsoap_running(),
                'stream_url': 'http://localhost:8000/stream',
                'low_quality_url': 'http://localhost:8000/stream_low'
            },
            'video': {
                'hls_running': self.is_video_streaming_running(),
                'stream_url': 'http://localhost:5000/api/video-stream/playlist.m3u8',
                'status': 'active' if self.is_video_streaming_running() else 'inactive'
            }
        }
    
    def is_icecast_running(self) -> bool:
        """Check if Icecast is running"""
        try:
            response = requests.get('http://localhost:8000/admin/stats.xml', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def is_liquidsoap_running(self) -> bool:
        """Check if Liquidsoap is running"""
        try:
            # Check if telnet interface is responding
            import telnetlib
            tn = telnetlib.Telnet('localhost', 1234, timeout=2)
            tn.close()
            return True
        except:
            return False
    
    def is_video_streaming_running(self) -> bool:
        """Check if video streaming is active"""
        if not self.video_stream_process:
            return False
        
        # Check if process is still running
        if self.video_stream_process.poll() is not None:
            return False
        
        # Check if HLS playlist exists and is recent
        hls_playlist = os.path.join(self.video_stream_dir, "hls", "playlist.m3u8")
        if not os.path.exists(hls_playlist):
            return False
        
        # Check if playlist was modified recently (within last 30 seconds)
        try:
            mtime = os.path.getmtime(hls_playlist)
            now = datetime.now().timestamp()
            return (now - mtime) < 30
        except:
            return False
    
    def get_icecast_listeners(self) -> int:
        """Get current number of listeners from Icecast"""
        try:
            response = requests.get('http://localhost:8000/admin/stats.xml', timeout=5)
            if response.status_code == 200:
                # Parse XML to get listener count
                # For simplicity, we'll use a basic approach
                text = response.text
                if 'listeners>' in text:
                    start = text.find('<listeners>') + len('<listeners>')
                    end = text.find('</listeners>', start)
                    return int(text[start:end])
            return 0
        except:
            return 0
    
    def reload_audio_playlist(self) -> bool:
        """Reload the audio playlist in Liquidsoap"""
        try:
            import telnetlib
            tn = telnetlib.Telnet('localhost', 1234, timeout=5)
            tn.write(b'ai_radio.reload\n')
            response = tn.read_until(b'\n', timeout=5)
            tn.close()
            
            print("Audio playlist reloaded")
            return True
        except Exception as e:
            print(f"Error reloading audio playlist: {e}")
            return False
    
    def skip_current_track(self) -> bool:
        """Skip currently playing audio track"""
        try:
            import telnetlib
            tn = telnetlib.Telnet('localhost', 1234, timeout=5)
            tn.write(b'ai_radio.skip\n')
            response = tn.read_until(b'\n', timeout=5)
            tn.close()
            
            print("Skipped current track")
            return True
        except Exception as e:
            print(f"Error skipping track: {e}")
            return False
    
    def get_current_track_info(self) -> Optional[str]:
        """Get information about currently playing track"""
        try:
            import telnetlib
            tn = telnetlib.Telnet('localhost', 1234, timeout=5)
            tn.write(b'ai_radio.current\n')
            response = tn.read_until(b'\n', timeout=5).decode('utf-8').strip()
            tn.close()
            
            return response
        except Exception as e:
            print(f"Error getting current track info: {e}")
            return None
    
    def start_all_streaming(self) -> Dict:
        """Start both audio and video streaming services"""
        results = {
            'audio': self.start_audio_streaming(),
            'video': self.start_video_streaming()
        }
        
        return results
    
    def stop_all_streaming(self) -> Dict:
        """Stop all streaming services"""
        results = {
            'audio': self.stop_audio_streaming(),
            'video': self.stop_video_streaming()
        }
        
        return results
    
    def restart_streaming(self) -> Dict:
        """Restart all streaming services"""
        print("Restarting streaming services...")
        
        # Stop all services
        stop_results = self.stop_all_streaming()
        
        # Wait a moment
        import time
        time.sleep(3)
        
        # Start all services
        start_results = self.start_all_streaming()
        
        return {
            'stop': stop_results,
            'start': start_results
        }
    
    def update_stream_status_db(self):
        """Update database with current streaming status"""
        try:
            status = StreamStatus.query.first()
            if not status:
                status = StreamStatus()
                db.session.add(status)
            
            status.listeners = self.get_icecast_listeners()
            status.updated_at = datetime.utcnow()
            
            db.session.commit()
        except Exception as e:
            print(f"Error updating stream status in database: {e}")

# Utility functions for easy import
def get_streaming_manager() -> StreamingManager:
    """Get a streaming manager instance"""
    return StreamingManager()

def start_streaming_services() -> bool:
    """Start all streaming services"""
    manager = StreamingManager()
    results = manager.start_all_streaming()
    return all(results.values())

def stop_streaming_services() -> bool:
    """Stop all streaming services"""
    manager = StreamingManager()
    results = manager.stop_all_streaming()
    return all(results.values())