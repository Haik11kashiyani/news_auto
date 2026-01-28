import os
import requests
import time
from PIL import Image
from playwright.sync_api import sync_playwright
import urllib.parse

class VisualGenerator:
    def __init__(self):
        self.pexels_api_key = os.getenv("PEXELS_API_KEY")
        self.generated_dir = "generated"
        os.makedirs(self.generated_dir, exist_ok=True)

    def get_background_video(self, news_article, keywords):
        """
        Determines and retrieves the background video.
        Priority:
        1. News Image -> Apply Ken Burns Effect (Simulated via simple pan in MoviePy later, or we assume static image for now and animate in editor).
        2. Pexels Video Search (Fallback or if no image).
        
        Returns: Path to local video file or image file.
        """
        image_url = news_article.get("image_url")
        
        # Strategy: Always prefer Pexels for "Viral" look if keywords exist?
        # User said: "If news content is big content... dynamic bg...".
        # Let's try Pexels first for high quality, if fails, fallback to News Image.
        
        video_path = self._search_pexels_video(keywords)
        if video_path:
            return video_path, "video"

        if image_url:
            image_path = self._download_image(image_url)
            if image_path:
                return image_path, "image"

        return None, None

    def _search_pexels_video(self, keywords):
        if not self.pexels_api_key or not keywords:
            return None
        
        # Taking top 2 keywords
        query = " ".join(keywords[:2])
        url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=1"
        headers = {"Authorization": self.pexels_api_key}

        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            if data.get("videos"):
                video_url = data["videos"][0]["video_files"][0]["link"]
                # Find high quality mp4
                for file in data["videos"][0]["video_files"]:
                    if file["height"] >= 1080 and ".mp4" in file["link"]:
                        video_url = file["link"]
                        break
                
                print(f"Downloading Pexels Background: {query}")
                return self._download_file(video_url, f"bg_{int(time.time())}.mp4")
        except Exception as e:
            print(f"Pexels search failed: {e}")
        return None

    def _download_image(self, url):
        try:
            filename = f"news_img_{int(time.time())}.jpg"
            return self._download_file(url, filename)
        except:
            return None

    def _download_file(self, url, filename):
        path = os.path.join(self.generated_dir, filename)
        try:
            # Basic header to avoid 403 on some image servers
            headers = {'User-Agent': 'Mozilla/5.0'} 
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return path
        except Exception as e:
            print(f"Download failed for {url}: {e}")
            return None

    def generate_overlay(self, ticker_text, time_str, Duration=10):
        """
        Uses Playwright to render the HTML overlay and record it (or take screenshots).
        For simplicity and performance in this script, we might just take a screenshot 
        if animation is too complex to record frame-by-frame without heavy re-engineering.
        
        However, User asked for "Playwright can capture... script uploads...".
        To keep it simple: We will capture a transparent screenshot sequence OR 
        just a single static overlay if video is too heavy.
        
        Let's try to capture a 5-second transparent webm if possible, or just return the HTML path 
        for MoviePy to use standard text clips. 
        
        Actually, simplest robust method:
        Update HTML file with text -> Open in Browser -> Screenshot (with transparency) -> Use as Overlay Image.
        (Animation effects like scrolling ticker might need video capture, but let's stick to static overlay with scrolling text handled by MoviePy? 
        No, prompt said: "Playwright can take a sequence of screenshots... stitch into video").
        OK, I will implement the Sequence Capture.
        """
        
        template_path = os.path.abspath("templates/overlay.html")
        output_seq_dir = os.path.join(self.generated_dir, "overlay_seq")
        os.makedirs(output_seq_dir, exist_ok=True)
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            url = f"file:///{template_path}"
            page.goto(url)
            
            # Inject Data
            page.evaluate(f"setTickerText('{ticker_text}')")
            # Page automatically updates time, but we can force it if needed.
            
            # Capture Frames (Simplified 10fps for 5s loop to save time/space)
            # Ticker loop is 15s in CSS.
            fps = 10 
            total_frames = int(Duration * fps)
            
            print("Rendering Overlay Sequence...")
            for i in range(total_frames):
                # We assume the CSS animation is running.
                # To sync, maybe we step time? Playwright doesn't easily step CSS time.
                # We'll just capture real-time.
                page.screenshot(path=os.path.join(output_seq_dir, f"frame_{i:03d}.png"), omit_background=True)
                # Sleep a bit to match FPS roughly (not perfect sync but works for visual ticker)
                # time.sleep(1/fps) # Actually, screenshot takes time, so this will be slow/laggy.
                # Better approach for high quality: Use MoviePy for Ticker, Playwright for Static layout.
                
            browser.close()
            
        return output_seq_dir

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    gen = VisualGenerator()
    # Test Pexels
    # print(gen.get_background_video({}, ["money", "finance"]))
    # Test Overlay
    # gen.generate_overlay("BREAKING NEWS: ALIEN INVASION CONFIRMED", "12:00 IST")
