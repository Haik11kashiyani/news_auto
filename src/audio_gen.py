import os
import requests
import json
import time

class AudioGenerator:
    def __init__(self):
        # Optional: Check for Keys, but don't require them.
        # Prefer explicit ELEVENLABS_API_KEY, but also support legacy TTS_API_KEY from workflow/README.
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("TTS_API_KEY")
        self.eleven_voice_id = "nPczCjz86I70pA5ccg71" 

    def generate_audio(self, text, output_path="generated/audio.mp3"):
        """
        Generates audio. Defaults to Free gTTS (Google TTS).
        """
        # 1. ElevenLabs (Only if user explicitly provided key in Secrets)
        if self.elevenlabs_api_key:
            return self._generate_elevenlabs_audio(text, output_path)

        # 2. Free Fallback (Default)
        print("Using Free TTS (gTTS)...")
        return self._generate_free_audio(text, output_path)

    def _generate_elevenlabs_audio(self, text, output_path):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.eleven_voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        try:
            print(f"Generating ElevenLabs audio...")
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path
        except Exception as e:
            print(f"ElevenLabs failed: {e}. Falling back to free.")
            return self._generate_free_audio(text, output_path)

    def _generate_free_audio(self, text, output_path):
        """
        Uses gTTS (Google Text-to-Speech) - Completely Free.
        """
        try:
            from gtts import gTTS
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Indian Accent English (co.in)
            tts = gTTS(text=text, lang='en', tld='co.in') 
            tts.save(output_path)
            return output_path
        except Exception as e:
            print(f"gTTS fallback failed: {e}")
            return None

if __name__ == "__main__":
    gen = AudioGenerator()
    gen.generate_audio("This is a test broadcast from Logic Vault.", "test_audio.mp3")
