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
        ABSOLUTE NUCLEAR OPTION: Remove ALL possible prefixes.
        This is the FINAL checkpoint before TTS.
        """
        if not text:
            return ""
        
        # Start fresh
        clean = str(text)
        original = clean  # Keep for debug
        
        # STEP 0: DIRECT STRING REPLACEMENTS (exact patterns - case sensitive)
        # These are the EXACT patterns Gemini is generating
        exact_patterns = [
            # Multi-word patterns (MOST IMPORTANT)
            "Voice name = Inner Engineer", "voice name = Inner Engineer",
            "Voice name = inner engineer", "Voice Name = Inner Engineer",
            "Voice name =", "voice name =", "Voice Name =", "voice Name =",
            "Voice name=", "voice name=", "VOICE NAME =", "VOICE NAME=",
            # Single word patterns
            "Voice =", "voice =", "Voice=", "voice=", "Voice:", "voice:", 
            "Voice -", "voice -", "VOICE =", "VOICE:",
            "Name =", "name =", "Name=", "name=", "Name:", "name:", "NAME =",
            "Inner Engineer", "inner engineer", "INNER ENGINEER",
            # Narrator/Speaker/Audio
            "Narrator:", "narrator:", "Narrator =", "narrator =", "NARRATOR:",
            "Speaker:", "speaker:", "Speaker =", "speaker =", "SPEAKER:",
            "Audio:", "audio:", "Audio =", "audio =", "AUDIO:",
            "VO:", "vo:", "VO =", "vo =",
            "Voiceover:", "voiceover:", "Voiceover =", "voiceover =",
        ]
        for pattern in exact_patterns:
            clean = clean.replace(pattern, "")
        
        # STEP 1: AGGRESSIVE REGEX - Remove ANY words before = or : at start
        # This matches: "Word1 Word2 Word3 = ..." or "Word1 Word2:"
        # Catches up to 5 words before the separator
        clean = re.sub(r'^([A-Za-z]+\s+){0,5}[A-Za-z]+\s*[:=]\s*', '', clean.strip())
        
        # STEP 2: Remove ANYWHERE in text (not just start)
        clean = re.sub(r'\b(Voice|Narrator|Speaker|Audio|VO|Voiceover|Name|Inner\s+Engineer)\s*[:=\-]?\s*', '', clean, flags=re.IGNORECASE)
        
        # STEP 3: Remove standalone "Voice", "Name", "Inner Engineer" completely
        clean = re.sub(r'\bVoice\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\bName\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\bInner\s*Engineer\b', '', clean, flags=re.IGNORECASE)
        
        # STEP 4: Remove emotion/direction tags
        clean = re.sub(r'[\(\[\{][^\)\]\}]{0,30}[\)\]\}]', '', clean)
        
        # STEP 5: Remove any = or : at the very start (leftover separators)
        clean = re.sub(r'^[\s:=\-]+', '', clean)
        
        # STEP 6: Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # Debug output
        print(f"[TTS SANITIZER] BEFORE: '{original[:100]}'")
        print(f"[TTS SANITIZER] AFTER:  '{clean[:100]}'")
        
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

    def mix_with_music(self, voice_path, music_path, output_path=None, music_volume=0.15):
        """
        Mix voice audio with background music.
        Voice stays at full volume, music is lowered significantly.
        
        Args:
            voice_path: Path to the voice audio file
            music_path: Path to the background music file
            output_path: Optional output path (defaults to replacing voice_path)
            music_volume: Volume of music (0.0 to 1.0), default 0.15 (15%)
        
        Returns:
            Path to the mixed audio file
        """
        try:
            from moviepy.editor import AudioFileClip, CompositeAudioClip
            
            if not output_path:
                output_path = voice_path  # Replace in place
            
            if not music_path or not os.path.exists(music_path):
                print("[Mix] No music file, skipping mix")
                return voice_path
            
            print(f"[Mix] Mixing voice with background music (volume: {music_volume})...")
            
            # Load voice
            voice = AudioFileClip(voice_path)
            voice_duration = voice.duration
            
            # Load and adjust music
            music = AudioFileClip(music_path)
            
            # Loop music if shorter than voice
            if music.duration < voice_duration:
                from moviepy.audio.fx.all import audio_loop
                music = audio_loop(music, duration=voice_duration)
            else:
                music = music.subclip(0, voice_duration)
            
            # Lower music volume
            music = music.volumex(music_volume)
            
            # Composite (voice on top)
            final = CompositeAudioClip([music, voice])
            
            # Write
            final.write_audiofile(output_path, fps=44100, verbose=False, logger=None)
            
            # Cleanup
            voice.close()
            music.close()
            final.close()
            
            print(f"[Mix] Mixed audio saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[Mix] Error mixing audio: {e}")
            return voice_path  # Return original if mix fails

if __name__ == "__main__":
    gen = AudioGenerator()
    gen.generate_audio("This is a test broadcast from Logic Vault.", "test_audio.mp3")

