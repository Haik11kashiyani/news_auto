import os
import requests
import json
import time
import re
import asyncio

class AudioGenerator:
    def __init__(self):
        # 100% free path: prefer Edge Neural TTS (no API key).
        # Paid path (optional): ElevenLabs if key provided.
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("TTS_API_KEY")
        self.eleven_voice_id = "nPczCjz86I70pA5ccg71"

        # Free, natural-ish voices (no key). Pick one default.
        # You can change this later for style.
        self.edge_voice = os.getenv("EDGE_TTS_VOICE", "en-IN-NeerjaNeural")

    def generate_audio(self, text, output_path="generated/audio.mp3"):
        """
        Generates audio.
        Priority:
        1) Edge Neural TTS (FREE, no key) -> most human-like
        2) ElevenLabs (if key provided)
        3) gTTS fallback (FREE, but more robotic)
        """
        # 1) Free, human-like (no key)
        edge_path = self._generate_edge_tts_audio(text, output_path)
        if edge_path:
            return edge_path

        # 2) Paid (optional)
        if self.elevenlabs_api_key:
            return self._generate_elevenlabs_audio(text, output_path)

        # 3) Free fallback
        print("Using Free TTS fallback (gTTS)...")
        return self._generate_gtts_audio(text, output_path)

    def _to_ssml(self, text: str) -> str:
        """
        Convert our script markers into SSML for better pacing.
        Supports [pause] and keeps text safe for XML.
        """
        # Basic escaping for SSML XML
        def esc(s: str) -> str:
            return (
                s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
            )

        # Normalize pauses
        # - [pause] -> 450ms break
        # - multiple dots / ellipsis -> small break
        normalized = text
        normalized = normalized.replace("[pause]", " <break time=\"450ms\"/> ")
        normalized = re.sub(r"\.\.\.+", " <break time=\"250ms\"/> ", normalized)

        # Add slight prosody for news-anchor vibe: a bit faster, medium pitch.
        body = esc(normalized)
        return (
            f"<speak>"
            f"<voice name=\"{esc(self.edge_voice)}\">"
            f"<prosody rate=\"+8%\" pitch=\"+2%\">{body}</prosody>"
            f"</voice>"
            f"</speak>"
        )

    def _generate_edge_tts_audio(self, text, output_path):
        """
        Uses edge-tts (FREE, no key). Requires internet access.
        """
        try:
            import edge_tts  # type: ignore

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            ssml = self._to_ssml(text)

            async def _run():
                communicate = edge_tts.Communicate(ssml, voice=self.edge_voice, rate="+8%", pitch="+2%")
                await communicate.save(output_path)

            print(f"Using FREE Edge Neural TTS voice: {self.edge_voice}")
            asyncio.run(_run())

            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return output_path
            print("Edge TTS produced empty audio; falling back...")
            return None
        except Exception as e:
            print(f"Edge TTS failed: {e}")
            return None

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
            return self._generate_gtts_audio(text, output_path)

    def _generate_gtts_audio(self, text, output_path):
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
    gen.generate_audio("This is a test broadcast from Newsroom.", "test_audio.mp3")
