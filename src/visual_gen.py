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

    def generate_overlay(self, headline, ticker_text, Duration=10):
        """
        Captures the premium Glassmorphism overlay.
        Now inputs both HEADLINE (for the card) and TICKER (for the scroll).
        """
        
        # ROBUST PATH CONSTRUCTION
        # Assuming running from 'news_auto' root directory
        project_root = os.getcwd() 
        template_relative = os.path.join("templates", "overlay.html")
        template_path = os.path.join(project_root, template_relative)
        
        print(f"DEBUG: Reading template from: {template_path}")
        if not os.path.exists(template_path):
             # Try finding it relative to this script if CWD is wrong
            script_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(script_dir, "..", "templates", "overlay.html")
            template_path = os.path.abspath(template_path)
            print(f"DEBUG: Retry reading from: {template_path}")

        # Read content directly to avoid file:// url issues in container
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        output_seq_dir = os.path.join(self.generated_dir, "overlay_seq")
        os.makedirs(output_seq_dir, exist_ok=True)
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            
            # DIRECT INJECTION - 100% Reliable
            print("DEBUG: Setting page content directly...")
            page.set_content(html_content)
            
            # Inject Usage of new function signature in HTML
            # Escape quotes to prevent JS errors
            safe_headline = headline.replace("'", "\\'").replace('"', '\\"')
            safe_ticker = ticker_text.replace("'", "\\'").replace('"', '\\"')
            
            page.evaluate(f"setTickerText('{safe_headline}', '{safe_ticker}')")
            
            # Capture Frames (10fps)
            fps = 10 
            total_frames = int(Duration * fps)
            
            print("Rendering Overlay Sequence...")
            for i in range(total_frames):
                page.screenshot(path=os.path.join(output_seq_dir, f"frame_{i:03d}.png"), omit_background=True)
                
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
