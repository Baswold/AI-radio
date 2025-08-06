"""AI Brain Server - Main entry point

This server provides AI capabilities to the AI Radio platform, including:
- GPT-based DJ commentary generation
- Text-to-Speech synthesis
- Background music generation
- Video generation for visual radio
"""

from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import torchaudio
from TTS.api import TTS
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load AI models
try:
    # Load GPT model for DJ commentary
    tokenizer = AutoTokenizer.from_pretrained("AI-Sweden-Models/gpt-sw3-20b")
    model = AutoModelForCausalLM.from_pretrained(
        "AI-Sweden-Models/gpt-sw3-20b",
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # Initialize TTS
    tts = TTS("tts_models/multilingual/multi-dataset/your_tts", gpu=True)
    
    logger.info("AI models loaded successfully")
except Exception as e:
    logger.error(f"Error loading AI models: {e}")
    raise

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'gpu': torch.cuda.is_available(),
        'models_loaded': True
    })

@app.route('/generate/commentary', methods=['POST'])
def generate_commentary():
    """Generate DJ commentary based on context."""
    try:
        data = request.get_json()
        context = data.get('context', '')
        
        # Generate commentary
        inputs = tokenizer(context, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_length=200,
            temperature=0.7,
            top_p=0.9
        )
        commentary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return jsonify({'commentary': commentary})
    except Exception as e:
        logger.error(f"Error generating commentary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate/speech', methods=['POST'])
def generate_speech():
    """Convert text to speech using YourTTS."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        # Generate speech
        output_path = "/tmp/speech.wav"
        tts.tts_to_file(text=text, file_path=output_path)
        
        return jsonify({'audio_path': output_path})
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Start the AI Brain server
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
