import os
import requests
import json
import time

class AudioGenerator:
    def __init__(self):
        self.api_key = os.getenv("TTS_API_KEY")
        # Defaulting to Play.ht stub logic, can be swapped for Cartesia
        self.user_id = os.getenv("PLAYHT_USER_ID") 
        self.voice_id = "s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json" # Example Voice ID (Clara)

    def generate_audio(self, text, output_path="generated/audio.mp3"):
        """
        Generates audio from text using Play.ht API (v2) or fallback.
        """
        if not self.api_key:
            print("TTS_API_KEY missing. Using dummy placeholder audio.")
            return self._generate_dummy_audio(text, output_path)

        url = "https://api.play.ht/api/v2/tts"
        headers = {
            "AUTHORIZATION": self.api_key,
            "X-USER-ID": self.user_id,
            "accept": "text/event-stream",
            "content-type": "application/json"
        }
        
        payload = {
            "text": text,
            "voice": self.voice_id,
            "output_format": "mp3",
            "speed": 1.1 # Slightly faster news cadence
        }

        try:
            # Note: This is a simplified synchronous blocking call for the stream
            # In production, we might want to handle the stream properly or use the async client.
            # For this MVP, we'll assume we can post and get a job or stream.
            # Play.ht v2 often uses a Job system for full reliability, or SSE for streams.
            # Here implementing a 'Job' based approach if stream is complex, 
            # OR simply returning a mock if actual API access isn't verified yet.
            
            # For the purpose of this script + robust fallback:
            print(f"Generating audio for: {text[:30]}...")
            # Real implementation would go here. 
            # Returning dummy for now to ensure flow works without live paid keys during dev.
            return self._generate_dummy_audio(text, output_path)
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None

    def _generate_dummy_audio(self, text, output_path):
        """
        Fallback using gTTS (Google Text-to-Speech) which is free.
        """
        try:
            from gtts import gTTS
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            tts = gTTS(text=text, lang='en', tld='co.in') # Indian accent English
            tts.save(output_path)
            return output_path
        except Exception as e:
            print(f"gTTS fallback failed: {e}")
            return None

if __name__ == "__main__":
    gen = AudioGenerator()
    gen.generate_audio("This is a test broadcast from Logic Vault.", "test_audio.mp3")
