import os
import requests
import time
from PIL import Image
from playwright.sync_api import sync_playwright
import urllib.parse

class VisualGenerator:
    # EMBEDDED TEMPLATE TO REMOVE FILE I/O RISKS
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1080, height=1920, initial-scale=1.0">
    <title>News Overlay Style 3</title>
    <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;700&family=Roboto+Condensed:wght@700&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; width: 1080px; height: 1920px; background: transparent; font-family: 'Chakra Petch', sans-serif; overflow: hidden; display: grid; grid-template-rows: 150px 1fr 200px; }
        .header { background: #000; color: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 40px; border-bottom: 5px solid #00ffcc; box-shadow: 0 10px 30px rgba(0, 255, 204, 0.2); }
        .brand { font-size: 48px; font-weight: 700; letter-spacing: 4px; text-transform: uppercase; }
        .brand span { color: #00ffcc; }
        .live-badge { background: #ff0033; color: white; padding: 10px 20px; font-size: 24px; font-weight: 700; border-radius: 5px; animation: pulse 2s infinite; }
        .content { position: relative; }
        .sidebar-card { position: absolute; right: 40px; top: 100px; width: 350px; background: rgba(0, 0, 0, 0.9); border: 2px solid #00ffcc; border-radius: 0 20px 0 20px; padding: 30px; color: white; }
        .topic { font-family: 'Roboto Condensed', sans-serif; font-size: 32px; color: #00ffcc; margin-bottom: 20px; border-bottom: 1px solid #333; padding-bottom: 10px; }
        .headline-main { font-size: 36px; line-height: 1.3; }
        .footer { background: linear-gradient(0deg, #000 0%, rgba(0,0,0,0.8) 100%); display: flex; flex-direction: column; justify-content: flex-end; }
        .ticker-wrap { width: 100%; height: 80px; background: #00ffcc; overflow: hidden; display: flex; align-items: center; }
        .ticker { display: inline-block; white-space: nowrap; padding-left: 100%; animation: ticker 20s linear infinite; font-family: 'Roboto Condensed', sans-serif; font-size: 40px; font-weight: 700; color: #000; text-transform: uppercase; }
        @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="header">
        <div class="brand">LOGIC <span>VAULT</span></div>
        <div class="live-badge">LIVE</div>
    </div>
    <div class="content">
        <div class="sidebar-card">
            <div class="topic">DEVELOPING STORY</div>
            <div class="headline-main" id="headline-display">Data Loading...</div>
        </div>
    </div>
    <div class="footer">
        <div class="ticker-wrap">
            <div class="ticker" id="ticker-display">BREAKING NEWS /// UPDATES COMING IN /// STAY TUNED ///</div>
        </div>
    </div>
    <script>
        function setTickerText(headline, ticker) {
            document.getElementById('headline-display').innerText = headline;
            const fullTicker = ticker + "  ///  " + ticker + "  ///  " + ticker;
            document.getElementById('ticker-display').innerText = fullTicker;
        }
    </script>
</body>
</html>
    """

    def __init__(self):
        self.pexels_api_key = os.getenv("PEXELS_API_KEY")
        self.generated_dir = "generated"
        # CLEANUP: Wipe old files to ensure we don't upload stale artifacts
        if os.path.exists(self.generated_dir):
            import shutil
            try:
                shutil.rmtree(self.generated_dir)
            except: pass
        os.makedirs(self.generated_dir, exist_ok=True)

    def get_background_video(self, news_article, keywords):
        # ... (rest of get_background_video kept same, just ensuring class structure is valid)
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
        Captures the premium Style 3 overlay using EMBEDDED HTML.
        """
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            
            # DIRECT INJECTION - 100% Reliable
            print("DEBUG: Setting page content directly...")
            page.set_content(self.HTML_TEMPLATE, wait_until="networkidle")
            
            # Inject Usage of new function signature in HTML
            # Escape quotes to prevent JS errors
            safe_headline = headline.replace("'", "\\'").replace('"', '\\"')
            safe_ticker = ticker_text.replace("'", "\\'").replace('"', '\\"')
            
            page.evaluate(f"setTickerText('{safe_headline}', '{safe_ticker}')")
            
            # Wait for layout/fonts
            time.sleep(2)

            # Capture Single Static Overlay (Robust)
            output_image_path = os.path.join(self.generated_dir, "overlay_final.png")
            print(f"Capturing Static Overlay to {output_image_path}...")
            
            page.screenshot(path=output_image_path, omit_background=True)
            
            # Verify Size
            size_kb = os.path.getsize(output_image_path) / 1024
            print(f"Overlay Size: {size_kb:.2f} KB")
            
            browser.close()
            
        return output_image_path

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    gen = VisualGenerator()
    # Test Pexels
    # print(gen.get_background_video({}, ["money", "finance"]))
    # Test Overlay
    # gen.generate_overlay("BREAKING NEWS: ALIEN INVASION CONFIRMED", "12:00 IST")
