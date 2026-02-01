"""
Music Manager - Handles mood-based background music selection and mixing.
Uses royalty-free music from public sources.
"""
import os
import requests

class MusicManager:
    def __init__(self):
        self.music_dir = "assets/music"
        os.makedirs(self.music_dir, exist_ok=True)
        
        # Royalty-free music URLs (from Pixabay/FreePD - no attribution required)
        # These are short loops suitable for news videos
        self.music_sources = {
            "urgent": "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8c8a73467.mp3",  # Tense news
            "neutral": "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946b0939c8.mp3",  # Calm background
            "positive": "https://cdn.pixabay.com/download/audio/2021/11/01/audio_5a24fbfb20.mp3",  # Upbeat
            "dramatic": "https://cdn.pixabay.com/download/audio/2022/05/16/audio_169df226f1.mp3",  # Intense
        }
        
        # Local fallback paths
        self.music_files = {
            "urgent": os.path.join(self.music_dir, "urgent.mp3"),
            "neutral": os.path.join(self.music_dir, "neutral.mp3"),
            "positive": os.path.join(self.music_dir, "positive.mp3"),
            "dramatic": os.path.join(self.music_dir, "dramatic.mp3"),
        }
    
    def ensure_music_downloaded(self, mood="neutral"):
        """
        Ensures the music file for the given mood is downloaded.
        Returns the path to the music file, or None if download fails.
        """
        if mood not in self.music_files:
            mood = "neutral"
        
        local_path = self.music_files[mood]
        
        # Check if already exists
        if os.path.exists(local_path) and os.path.getsize(local_path) > 10000:
            print(f"[Music] Using cached: {local_path}")
            return local_path
        
        # Download
        url = self.music_sources.get(mood)
        if not url:
            print(f"[Music] No URL for mood: {mood}")
            return None
        
        try:
            print(f"[Music] Downloading {mood} music...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print(f"[Music] Downloaded: {local_path}")
            return local_path
        except Exception as e:
            print(f"[Music] Download failed: {e}")
            return None
    
    def detect_mood(self, headline, content=""):
        """
        Simple mood detection based on keywords.
        Returns: 'urgent', 'positive', 'dramatic', or 'neutral'
        """
        text = (headline + " " + content).lower()
        
        # Urgent keywords
        urgent_words = ["breaking", "alert", "emergency", "crisis", "attack", 
                       "killed", "dead", "death", "explosion", "war", "terror"]
        if any(word in text for word in urgent_words):
            return "urgent"
        
        # Positive keywords
        positive_words = ["wins", "victory", "success", "achieves", "record", 
                         "celebrates", "happy", "growth", "breakthrough", "launch"]
        if any(word in text for word in positive_words):
            return "positive"
        
        # Dramatic keywords
        dramatic_words = ["scandal", "investigation", "accused", "arrested", 
                         "controversial", "shocking", "revealed", "exposed"]
        if any(word in text for word in dramatic_words):
            return "dramatic"
        
        # Default
        return "neutral"
    
    def get_music_for_news(self, headline, content=""):
        """
        Main entry point: Detects mood and returns path to appropriate music.
        """
        mood = self.detect_mood(headline, content)
        print(f"[Music] Detected mood: {mood}")
        return self.ensure_music_downloaded(mood), mood


if __name__ == "__main__":
    mm = MusicManager()
    
    # Test
    path, mood = mm.get_music_for_news("Breaking: Major earthquake hits city")
    print(f"Got: {path} (mood: {mood})")
    
    path, mood = mm.get_music_for_news("India wins Cricket World Cup")
    print(f"Got: {path} (mood: {mood})")
