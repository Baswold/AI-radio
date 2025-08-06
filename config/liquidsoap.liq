#!/usr/bin/liquidsoap

# AI Radio Platform - Liquidsoap Configuration
# Handles playlist management, DJ intros, and streaming to Icecast

# Set log file location
set("log.file.path","/var/log/liquidsoap/ai_radio.log")
set("log.level",3)

# Server settings
set("server.telnet",true)
set("server.telnet.bind_addr","127.0.0.1")
set("server.telnet.port",1234)

# Playlists and content sources
playlist_path = "/Users/basil_jackson/Documents/ai_radio/media/playlists/current.m3u"
silence_path = "/Users/basil_jackson/Documents/ai_radio/media/silence.mp3"

# Create a silence track for gaps
silence = single(silence_path)

# Main playlist source with reloading capability
main_playlist = playlist(
  reload=10,          # Reload every 10 seconds to pick up changes
  reload_mode="watch", # Watch file system for changes
  playlist_path
)

# Fallback to silence if playlist is empty
safe_playlist = fallback(track_sensitive=false, [main_playlist, silence])

# Audio processing and normalization
processed_audio = normalize(safe_playlist)

# Apply audio effects for consistent sound
processed_audio = compress(processed_audio)
processed_audio = normalize(processed_audio)

# Add crossfade between tracks for smooth transitions
smooth_audio = crossfade(start_next=2.0, fade_in=1.0, fade_out=1.0, processed_audio)

# Function to handle DJ intro insertion
def add_dj_intro(m) =
  # Extract upload ID from metadata if available
  upload_id = m["upload_id"]
  
  # Look for corresponding DJ intro file
  intro_file = "/Users/basil_jackson/Documents/ai_radio/media/dj_intros/intro_#{upload_id}.mp3"
  
  if file.exists(intro_file) then
    log("Playing DJ intro for upload #{upload_id}")
    # Play intro followed by main content
    sequence([single(intro_file), once(single(m["filename"]))])
  else
    log("No DJ intro found for upload #{upload_id}, playing content directly")
    once(single(m["filename"]))
  end
end

# Apply DJ intro logic to playlist items
enhanced_audio = map_metadata(add_dj_intro, smooth_audio)

# Stream metadata handling
def update_metadata(m) =
  # Extract information for now-playing updates
  title = m["title"]
  artist = m["artist"] 
  upload_id = m["upload_id"]
  
  # Log current track info
  log("Now playing: #{artist} - #{title} (Upload ID: #{upload_id})")
  
  # You could make HTTP requests here to update the backend's now-playing status
  # For now, we'll just ensure proper metadata is sent to Icecast
  
  [("title", title), ("artist", artist), ("comment", "AI Generated Content")]
end

# Apply metadata updates
final_audio = map_metadata(update_metadata, enhanced_audio)

# Output to Icecast - Main stream (Ogg Vorbis, high quality)
output.icecast(
  %vorbis(quality=0.7),
  host="localhost",
  port=8000,
  password="ai_radio_source_2024",
  mount="/stream",
  name="AI Radio - All AI Generated Content",
  description="24/7 stream of AI-generated music, podcasts, and video content",
  url="http://localhost:5000",
  genre="AI Generated",
  public=true,
  final_audio
)

# Output to Icecast - Low quality stream (MP3, for mobile/slow connections)
output.icecast(
  %mp3(bitrate=96),
  host="localhost",
  port=8000,
  password="ai_radio_source_2024",
  mount="/stream_low",
  name="AI Radio - Low Quality Stream",
  description="Low bandwidth AI-generated content stream",
  url="http://localhost:5000",
  genre="AI Generated",
  public=true,
  final_audio
)

# Harbor input for live DJ sessions (future feature)
live_input = input.harbor(
  "live",
  port=8001,
  password="ai_radio_live_2024"
)

# Mix live input with playlist when available
mixed_audio = fallback(track_sensitive=false, [live_input, final_audio])

# Command-line interface functions for remote control
def skip_track() =
  log("Skipping current track via command")
  source.skip(main_playlist)
  "Track skipped"
end

def reload_playlist() =
  log("Reloading playlist via command")
  playlist.reload(main_playlist)
  "Playlist reloaded"
end

def get_current_metadata() =
  m = source.last_metadata(final_audio)
  title = m["title"]
  artist = m["artist"]
  "Now playing: #{artist} - #{title}"
end

# Register server commands for remote control
server.register(
  namespace="ai_radio",
  usage="skip",
  description="Skip current track",
  "skip",
  fun (_) -> skip_track()
)

server.register(
  namespace="ai_radio",
  usage="reload",
  description="Reload playlist",
  "reload", 
  fun (_) -> reload_playlist()
)

server.register(
  namespace="ai_radio",
  usage="current",
  description="Get current track info",
  "current",
  fun (_) -> get_current_metadata()
)

# Logging and monitoring
def log_track_start(m) =
  title = m["title"]
  artist = m["artist"]
  upload_id = m["upload_id"]
  timestamp = time()
  
  log("TRACK_START: #{timestamp} - #{artist} - #{title} (ID: #{upload_id})")
  
  # Here you could make an HTTP request to update the backend
  # with the current playing status
  
  # Example (commented out - would need HTTP support):
  # http.post(
  #   "http://localhost:5000/api/internal/update-now-playing",
  #   headers=[("Content-Type", "application/json")],
  #   data=json.stringify([("upload_id", upload_id), ("started_at", timestamp)])
  # )
end

# Hook into track changes to log starts
def on_track_change(m) = 
  log_track_start(m)
end

# Apply track change monitoring
on_metadata(final_audio, on_track_change)

# Error handling and recovery
def on_error(msg) =
  log.severe("Liquidsoap error: #{msg}")
end

# Health check - create a simple HTTP status endpoint
def health_check(~protocol, ~data, ~headers, uri) =
  if uri == "/health" then
    log("Health check requested")
    http.response(
      protocol=protocol,
      code=200,
      headers=[("Content-Type", "application/json")],
      data="{\"status\": \"healthy\", \"service\": \"liquidsoap\"}"
    )
  else
    http.response(
      protocol=protocol,
      code=404,
      data="Not found"
    )
  end
end

# Start HTTP server for health checks
harbor.http.register(port=8002, method="GET", "^/", health_check)

log("AI Radio Liquidsoap configuration loaded successfully")
log("Telnet server: localhost:1234")
log("Health check: localhost:8002/health")
log("Live input: harbor://localhost:8001/live")
log("Main stream: http://localhost:8000/stream")
log("Low quality stream: http://localhost:8000/stream_low")