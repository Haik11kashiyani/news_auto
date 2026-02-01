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
        # DEBUG: Show what we received
        print(f"[TTS DEBUG] ORIGINAL INPUT: {text}")
        
        # FINAL CHECKPOINT: Clean ALL metadata before TTS
        text = self._sanitize_for_tts(text)
        
        # DEBUG: Show what we're sending to TTS
        print(f"[TTS DEBUG] CLEANED OUTPUT: {text}")
        
        if not text.strip():
            print("ERROR: Text is empty after sanitization!")
            return None
        
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

    def _sanitize_for_tts(self, text):
        """
        NUCLEAR OPTION: Remove ALL possible script/direction tags.
        This is the FINAL checkpoint before TTS.
        """
        if not text:
            return ""
        
        # Start fresh
        clean = str(text)
        
        # 0. DIRECT STRING REPLACEMENTS for exact patterns (case-insensitive workaround)
        # These MUST come first before any regex
        for pattern in ["Voice =", "voice =", "Voice=", "voice=", 
                        "Voice:", "voice:", "Voice -", "voice -",
                        "Narrator:", "narrator:", "Speaker:", "speaker:",
                        "Audio:", "audio:", "VO:", "vo:"]:
            clean = clean.replace(pattern, "")
        
        # 1. Regex: Remove any remaining "Voice/Narrator/etc" with separators
        clean = re.sub(r'\b(Voice|Narrator|Speaker|Audio|VO|Voiceover)\s*[:=\-]?\s*', '', clean, flags=re.IGNORECASE)
        
        # 2. Remove the standalone word "Voice" completely
        clean = re.sub(r'\bVoice\b', '', clean, flags=re.IGNORECASE)
        
        # 3. Remove emotion/direction tags: (Happy), [Excited], {Serious}, etc.
        clean = re.sub(r'[\(\[\{][^\)\]\}]{0,20}[\)\]\}]', '', clean)
        
        # 4. Remove bracketed instructions: [pause], [URGENT], [SFX], [beat]
        clean = re.sub(r'\[[^\]]*\]', '', clean)
        
        # 5. Remove "Inner Engineer" or similar if present
        clean = re.sub(r'\bInner\s+Engineer\b', '', clean, flags=re.IGNORECASE)
        
        # 6. Remove any remaining special markers
        clean = clean.replace("***", "").replace("**", "").replace("##", "")
        
        # 7. Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        print(f"[TTS Sanitizer] Input: {text[:80]}...")
        print(f"[TTS Sanitizer] Output: {clean[:80]}...")
        return clean

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

        # Remove artificial prosody to fix "shaking" voice issues.
        body = esc(normalized)
        return (
            f"<speak>"
            f"<voice name=\"{esc(self.edge_voice)}\">"
            f"{body}" 
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
                # Removed pitch/rate args that were causing errors/robotic sound
                # en-US-AriaNeural is naturally good paced.
                communicate = edge_tts.Communicate(ssml, voice=self.edge_voice)
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

    def get_audio_duration(self, audio_path):
        try:
            from moviepy.editor import AudioFileClip
            clip = AudioFileClip(audio_path)
            duration = clip.duration
            clip.close()
            return duration
        except Exception as e:
            print(f"Error getting duration: {e}")
            return 0

if __name__ == "__main__":
    gen = AudioGenerator()
    gen.generate_audio("This is a test broadcast from Logic Vault.", "test_audio.mp3")
