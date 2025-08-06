"""
AI Generator module for creating DJ intros and transitions using GPT-OSS and TTS.
This module interfaces with the AI Brain (desktop with GPU) for heavy processing.
"""

import requests
import json
import os
from typing import Dict, Optional
import random
from datetime import datetime

class AIHost:
    def __init__(self, ai_brain_url=None):
        """
        Initialize AI Host for generating DJ content
        
        Args:
            ai_brain_url: URL of the AI Brain server (desktop with GPU)
        """
        self.ai_brain_url = ai_brain_url or os.environ.get('AI_BRAIN_URL', 'http://localhost:8080')
        self.personalities = self.load_personalities()
        
    def load_personalities(self):
        """Load different DJ personality prompts"""
        return {
            'energetic': {
                'style': 'high-energy, enthusiastic, uses modern slang',
                'greeting_style': 'Hey there, music lovers!',
                'transition_style': 'pumped up and excited'
            },
            'chill': {
                'style': 'laid-back, smooth, contemplative',
                'greeting_style': 'Welcome back, friends',
                'transition_style': 'smooth and relaxed'
            },
            'professional': {
                'style': 'informative, articulate, NPR-like',
                'greeting_style': 'Good evening, and welcome',
                'transition_style': 'professional and informative'
            },
            'quirky': {
                'style': 'funny, unexpected, creative wordplay',
                'greeting_style': 'Greetings, fellow humans and AI entities!',
                'transition_style': 'witty and unexpected'
            }
        }
    
    def select_personality(self, time_of_day=None):
        """Select appropriate personality based on time of day"""
        if not time_of_day:
            hour = datetime.now().hour
        else:
            hour = time_of_day
            
        if 6 <= hour < 10:  # Morning
            return random.choice(['energetic', 'professional'])
        elif 10 <= hour < 16:  # Midday
            return random.choice(['professional', 'chill'])
        elif 16 <= hour < 20:  # Afternoon
            return random.choice(['energetic', 'quirky'])
        else:  # Evening/Night
            return random.choice(['chill', 'quirky'])
    
    def generate_intro(self, metadata: Dict) -> Dict:
        """
        Generate AI DJ intro for uploaded content
        
        Args:
            metadata: Dict containing title, username, media_type, description, etc.
            
        Returns:
            Dict with 'text' and 'personality' keys
        """
        try:
            personality_name = self.select_personality()
            personality = self.personalities[personality_name]
            
            prompt = f"""You are an AI DJ with a {personality['style']} personality hosting an all-AI media station.
Create a brief, engaging introduction (20-30 seconds when spoken) for this content:

Title: {metadata.get('title', 'Untitled')}
Creator: {metadata.get('username', 'Anonymous')}
Type: {metadata.get('media_type', 'audio')}
Category: {metadata.get('category', 'General')}
Description: {metadata.get('description', 'No description')}

Requirements:
- Start with something like "{personality['greeting_style']}"
- Be {personality['transition_style']} in tone
- Mention it's AI-generated content
- Keep it under 30 seconds when spoken
- Be creative and engaging
- Don't use quotation marks in your response

Response should be just the intro text, nothing else."""

            # Make request to AI Brain
            response = self.call_ai_brain('generate_text', {
                'prompt': prompt,
                'max_tokens': 150,
                'temperature': 0.8
            })
            
            if response and 'text' in response:
                return {
                    'text': response['text'].strip(),
                    'personality': personality_name
                }
            else:
                # Fallback if AI Brain is unavailable
                return self.generate_fallback_intro(metadata, personality_name)
                
        except Exception as e:
            print(f"Error generating intro: {e}")
            return self.generate_fallback_intro(metadata, 'professional')
    
    def generate_transition(self, current_item: Dict, next_item: Dict) -> Dict:
        """Generate smooth transition between content pieces"""
        try:
            personality_name = self.select_personality()
            personality = self.personalities[personality_name]
            
            prompt = f"""Create a smooth, brief transition (10-15 seconds) from one piece of content to the next.
You are an AI DJ with a {personality['style']} personality.

Just finished: "{current_item.get('title', 'Previous track')}"
Coming up next: "{next_item.get('title', 'Next track')}" by {next_item.get('username', 'Anonymous')}

Keep it natural, brief, and {personality['transition_style']}.
Don't use quotation marks in your response."""

            response = self.call_ai_brain('generate_text', {
                'prompt': prompt,
                'max_tokens': 100,
                'temperature': 0.8
            })
            
            if response and 'text' in response:
                return {
                    'text': response['text'].strip(),
                    'personality': personality_name
                }
            else:
                return self.generate_fallback_transition(current_item, next_item, personality_name)
                
        except Exception as e:
            print(f"Error generating transition: {e}")
            return self.generate_fallback_transition(current_item, next_item, 'professional')
    
    def generate_fallback_intro(self, metadata: Dict, personality: str) -> Dict:
        """Generate simple intro when AI Brain is unavailable"""
        templates = {
            'energetic': f"Hey there! Here's something awesome - {metadata.get('title', 'this track')} created by {metadata.get('username', 'one of our AI creators')}! Let's dive in!",
            'chill': f"Here's a nice piece for you - {metadata.get('title', 'this content')} from {metadata.get('username', 'our community')}. Enjoy this AI-generated creation.",
            'professional': f"Coming up now, we have {metadata.get('title', 'a new piece')} created by {metadata.get('username', 'one of our contributors')}. This AI-generated content showcases the creative potential of artificial intelligence.",
            'quirky': f"Beep boop! The AI overlords present {metadata.get('title', 'this fantastic creation')} by {metadata.get('username', 'a fellow AI enthusiast')}. Prepare for artificial awesomeness!"
        }
        
        return {
            'text': templates.get(personality, templates['professional']),
            'personality': personality
        }
    
    def generate_fallback_transition(self, current: Dict, next_item: Dict, personality: str) -> Dict:
        """Generate simple transition when AI Brain is unavailable"""
        templates = {
            'energetic': f"That was incredible! Now let's keep the energy going with {next_item.get('title', 'our next track')}!",
            'chill': f"Nice. Coming up, we have {next_item.get('title', 'something else')} for you to enjoy.",
            'professional': f"Next in our lineup is {next_item.get('title', 'another AI creation')} by {next_item.get('username', 'our community')}.",
            'quirky': f"Plot twist! Here comes {next_item.get('title', 'the next adventure')}. AI creativity never sleeps!"
        }
        
        return {
            'text': templates.get(personality, templates['professional']),
            'personality': personality
        }
    
    def call_ai_brain(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make API call to AI Brain server"""
        try:
            response = requests.post(
                f"{self.ai_brain_url}/{endpoint}",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"AI Brain error: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"Failed to connect to AI Brain: {e}")
            return None
    
    def test_ai_brain_connection(self) -> bool:
        """Test if AI Brain server is accessible"""
        try:
            response = requests.get(f"{self.ai_brain_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


class TTSHandler:
    def __init__(self, ai_brain_url=None):
        """Initialize TTS handler for voice synthesis"""
        self.ai_brain_url = ai_brain_url or os.environ.get('AI_BRAIN_URL', 'http://localhost:8080')
        self.output_dir = os.path.join(os.environ.get('MEDIA_FOLDER', '/Users/basil_jackson/Documents/ai_radio/media'), 'dj_intros')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_audio(self, text: str, output_filename: str) -> Optional[str]:
        """
        Generate audio from text using TTS
        
        Args:
            text: Text to convert to speech
            output_filename: Name for output file (without path)
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            output_path = os.path.join(self.output_dir, f"{output_filename}.mp3")
            
            # Make request to AI Brain for TTS
            response = self.call_ai_brain('generate_tts', {
                'text': text,
                'voice': 'default',
                'speed': 1.0
            })
            
            if response and 'audio_data' in response:
                # Save audio data to file
                import base64
                audio_data = base64.b64decode(response['audio_data'])
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                return output_path
            else:
                print("TTS generation failed")
                return None
                
        except Exception as e:
            print(f"Error generating TTS: {e}")
            return None
    
    def call_ai_brain(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make API call to AI Brain server"""
        try:
            response = requests.post(
                f"{self.ai_brain_url}/{endpoint}",
                json=data,
                timeout=60  # TTS can take longer
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"AI Brain TTS error: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"Failed to connect to AI Brain for TTS: {e}")
            return None


# Factory functions for easy import
def create_ai_host(ai_brain_url=None) -> AIHost:
    """Create an AI Host instance"""
    return AIHost(ai_brain_url)

def create_tts_handler(ai_brain_url=None) -> TTSHandler:
    """Create a TTS Handler instance"""
    return TTSHandler(ai_brain_url)