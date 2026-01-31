import os
import requests
import time
from PIL import Image
from playwright.sync_api import sync_playwright
import urllib.parse

class VisualGenerator:
    # EMBEDDED TEMPLATE - CENTER CARD STYLE WITH GSAP
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1080, height=1920, initial-scale=1.0">
    <title>News Overlay Newsroom</title>
    <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;700&family=Roboto+Condensed:wght@700&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <style>
        body { margin: 0; padding: 0; width: 1080px; height: 1920px; background: transparent; font-family: 'Inter', sans-serif; overflow: hidden; display: flex; align-items: center; justify-content: center; }
        
        /* Background dim layer (optional if we had video) */
        .glass-backdrop { position: absolute; top:0; left:0; width:100%; height:100%; z-index: -1; }

        /* MAIN CARD */
        .news-card {
            width: 940px; /* Wider */
            background: rgba(15, 15, 15, 0.90); /* Darker, more premium */
            border: 3px solid rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(40px); /* Stronger blur */
            border-radius: 50px;
            padding: 70px 60px;
            box-shadow: 0 30px 80px rgba(0,0,0,0.8);
            display: flex;
            flex-direction: column;
            gap: 30px;
            transform-origin: center center;
            opacity: 0; /* JS will fade in */
        }

        /* HEADER SECTION */
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 30px;
        }
        .brand-pill {
            background: #FF0033;
            color: #fff;
            padding: 10px 24px;
            border-radius: 100px;
            font-family: 'Chakra Petch', sans-serif;
            font-weight: 700;
            font-size: 24px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .topic-label {
            color: #00FFCC;
            font-family: 'Roboto Condensed', sans-serif;
            font-size: 28px;
            letter-spacing: 3px;
            text-transform: uppercase;
            font-weight: 700;
        }

        /* CONTENT SECTION */
        .headline-main {
            font-size: 56px;
            line-height: 1.1;
            font-weight: 800;
            color: #ffffff;
            margin: 0;
            letter-spacing: -1px;
        }
        
        .separator {
            width: 100px;
            height: 6px;
            background: #00FFCC;
            border-radius: 10px;
        }

        .summary-text {
            font-size: 32px;
            line-height: 1.4;
            color: #d0d0d0;
            font-weight: 400;
            border-left: 8px solid #FF0033;
            padding-left: 40px;
            margin-top: 30px;
            min-height: 500px; /* REQUEST: Make news div longer */
            display: flex;
            align-items: flex-start; /* Top align for long text */
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }

        /* FOOTER / TICKER */
        .card-footer {
            margin-top: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 15px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .ticker-text {
            font-family: 'Chakra Petch', sans-serif;
            font-size: 24px;
            color: #ccc;
            white-space: nowrap;
            display: inline-block;
            text-transform: uppercase;
        }

    </style>
</head>
<body>

    <div class="news-card" id="mainCard">
        <div class="card-header">
            <div class="brand-pill">NEWSROOM</div>
            <div class="topic-label" id="headline-label">TOP STORY</div>
        </div>
        
        <div class="headline-main" id="headline-display">
            Loading Headline...
        </div>

        <div class="separator"></div>

        <div class="summary-text" id="summary-display">
            Loading summary content...
        </div>

        <div class="card-footer">
             <marquee scrollamount="10" class="ticker-text" id="ticker-display">
                 LIVE UPDATES /// BREAKING NEWS ///
             </marquee>
        </div>
    </div>

    <script>
        function setOverlayText(headline, summary, label, ticker) {
            document.getElementById('headline-display').innerText = headline;
            document.getElementById('summary-display').innerText = summary;
            document.getElementById('headline-label').innerText = label;
            document.getElementById('ticker-display').innerText = ticker + "   ///   " + ticker;

            // GSAP Animations
            const tl = gsap.timeline();
            
            // 1. Card entry (scale up + fade)
            tl.to("#mainCard", { duration: 0.8, opacity: 1, scale: 1, ease: "power3.out" });
            
            // 2. Elements stagger in
            tl.from(".card-header", { duration: 0.5, y: -20, opacity: 0, ease: "power2.out" }, "-=0.4");
            tl.from(".headline-main", { duration: 0.6, x: -30, opacity: 0, ease: "power2.out" }, "-=0.3");
            tl.from(".separator", { duration: 0.4, width: 0, ease: "power2.out" }, "-=0.3");
            tl.from(".summary-text", { duration: 0.8, y: 20, opacity: 0, ease: "power2.out" }, "-=0.2");
            tl.from(".card-footer", { duration: 0.5, y: 20, opacity: 0, ease: "power2.out" }, "-=0.4");
        }
        
        // Initial set (hidden)
        gsap.set("#mainCard", { opacity: 0, scale: 0.9 });
    </script>
</body>
</html>
    """

    def __init__(self):
        self.generated_dir = "generated"
        # CLEANUP: Wipe old files to ensure we don't upload stale artifacts
        if os.path.exists(self.generated_dir):
            import shutil
            try:
                shutil.rmtree(self.generated_dir)
            except: pass
        os.makedirs(self.generated_dir, exist_ok=True)

    def _build_label(self, headline: str) -> str:
        """
        Build a small dynamic label based on the headline content.
        """
        if not headline:
            return "TOP STORY"
        h = headline.upper()
        if "BREAKING" in h:
            return "BREAKING"
        if "ALERT" in h:
            return "URGENT"
        if "UPDATE" in h:
            return "UPDATE"
        if "EXCLUSIVE" in h:
            return "EXCLUSIVE"
        return "TOP STORY"

    def get_background_video(self, news_article, keywords):
        """
        NO API CALLS.
        Returns:
            - Path to article image (if exists) -> 'image'
            - OR None -> 'image' (which VideoEditor will handle as black fallback)
        """
        image_url = news_article.get("image_url")
        if image_url:
            print(f"Downloading Article Image: {image_url}")
            image_path = self._download_image(image_url)
            if image_path:
                return image_path, "image"

        return None, "image"

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

    def generate_overlay(self, headline, ticker_text, summary_text=None, filename="overlay_final.png"):
        """
        Captures the premium Center Card overlay with GSAP animations.
        """
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            
            # DIRECT INJECTION
            print("DEBUG: Setting page content directly...")
            page.set_content(self.HTML_TEMPLATE, wait_until="networkidle")
            
            # Escape quotes
            safe_headline = (headline or "Top Story").replace("'", "\\'").replace('"', '\\"')
            safe_ticker = (ticker_text or "LATEST NEWS").replace("'", "\\'").replace('"', '\\"')
            safe_summary = (summary_text or "Loading...").replace("'", "\\'").replace('"', '\\"')
            label = self._build_label(headline or "")
            safe_label = label.replace("'", "\\'").replace('"', '\\"')
            
            # Trigger setup AND Animation
            page.evaluate(f"setOverlayText('{safe_headline}', '{safe_summary}', '{safe_label}', '{safe_ticker}')")
            
            # WAIT FOR GSAP ANIMATION TO COMPLETE
            # Animation duration sums to ~1.5s total including offsets. 
            # We wait 2.5s to be safe and capture the final settled state.
            print("Waiting for GSAP animations to settle...")
            time.sleep(2.5)

            # Capture Static Overlay (Final State)
            output_image_path = os.path.join(self.generated_dir, filename)
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
    # Test
    # gen.generate_overlay("GSAP ADDED TO SYSTEM", "SYSTEM UPGRADE", "This is the summary text that sits in the center card.", 10)

