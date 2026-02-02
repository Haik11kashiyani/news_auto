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

        /* MAIN CARD - Premium Gradient */
        .news-card {
            width: 940px;
            /* PREMIUM GRADIENT - Deep purple to dark blue with subtle glow */
            background: linear-gradient(145deg, 
                rgba(25, 10, 40, 0.95) 0%, 
                rgba(15, 15, 35, 0.98) 35%, 
                rgba(10, 20, 45, 0.95) 70%, 
                rgba(20, 10, 35, 0.95) 100%);
            border: 2px solid rgba(255, 255, 255, 0.12);
            /* Subtle glow effect */
            box-shadow: 
                0 0 60px rgba(100, 50, 180, 0.15),
                0 30px 80px rgba(0, 0, 0, 0.7),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(40px);
            border-radius: 45px;
            padding: 60px 55px 50px 55px;
            display: flex;
            flex-direction: column;
            gap: 25px;
            transform-origin: center center;
            opacity: 0;
        }

        /* HEADER SECTION */
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 25px;
        }
        .brand-pill {
            /* Gradient red pill */
            background: linear-gradient(135deg, #FF0044 0%, #CC0033 100%);
            color: #fff;
            padding: 12px 28px;
            border-radius: 100px;
            font-family: 'Chakra Petch', sans-serif;
            font-weight: 700;
            font-size: 22px;
            text-transform: uppercase;
            letter-spacing: 2px;
            box-shadow: 0 4px 15px rgba(255, 0, 68, 0.4);
        }
        .topic-label {
            /* Cyan accent */
            color: #00E5CC;
            font-family: 'Roboto Condensed', sans-serif;
            font-size: 26px;
            letter-spacing: 3px;
            text-transform: uppercase;
            font-weight: 700;
            text-shadow: 0 0 20px rgba(0, 229, 204, 0.3);
        }

        /* CONTENT SECTION */
        .headline-main {
            font-size: 68px;
            line-height: 1.12;
            font-weight: 800;
            color: #ffffff;
            margin: 0;
            letter-spacing: -1.5px;
            padding-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }
        
        .separator {
            width: 120px;
            height: 6px;
            /* Gradient separator */
            background: linear-gradient(90deg, #00E5CC 0%, #00AAFF 100%);
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 0 15px rgba(0, 229, 204, 0.4);
        }

        .summary-text {
            font-size: 46px;
            line-height: 1.35;
            color: #e8e8e8;
            font-weight: 500;
            /* Gradient border left */
            border-left: 6px solid;
            border-image: linear-gradient(180deg, #FF0044, #FF6600) 1;
            padding-left: 28px;
            margin-top: 20px;
            padding-bottom: 15px;
            /* LARGER - fits 6 lines now */
            min-height: 380px;
            max-width: 860px;
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
        .ticker-container {
            width: 100%;
            overflow: hidden;
            white-space: nowrap;
        }
        .ticker-text {
            font-family: 'Chakra Petch', sans-serif;
            font-size: 32px; /* Larger */
            color: #ccc;
            white-space: nowrap;
            display: inline-block;
            text-transform: uppercase;
            padding-left: 100%; /* Start from right */
            animation: ticker-slide 15s linear infinite;
        }
        @keyframes ticker-slide {
            0% { transform: translate3d(0, 0, 0); }
            100% { transform: translate3d(-100%, 0, 0); }
        }

        /* ANIMATION CLASSES */
        .word { display: inline-block; opacity: 0; transform: translateY(20px); will-change: transform, opacity; margin-right: 0.2em; }
        .char { display: inline-block; opacity: 0; transform: translateY(10px); will-change: transform, opacity; }
        
        .live-pulse {
            animation: pulse-red 2s infinite;
        }
        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(255, 0, 51, 0.7); }
            70% { box-shadow: 0 0 0 15px rgba(255, 0, 51, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 0, 51, 0); }
        }

    </style>
</head>
<body>

    <div class="news-card" id="mainCard">
        <div class="card-header">
            <div class="brand-pill live-pulse">NEWSROOM</div>
            <div class="topic-label" id="headline-label">{{LABEL}}</div>
        </div>
        
        <div class="headline-main" id="headline-display">
            {{HEADLINE}}
        </div>

        <div class="separator"></div>

        <div class="summary-text" id="summary-display">
            {{SUMMARY}}
        </div>

        <div class="card-footer">
        </div>
    </div>

    <script>
        function wrapWords(str) {
            if (!str) return "";
            return str.split(' ').map(word => `<span class="word">${word}</span>`).join('');
        }
        
        function wrapChars(str) {
            return str.split('').map(char => `<span class="char">${char === ' ' ? '&nbsp;' : char}</span>`).join('');
        }

        function animateContent() {
            // 1. Get current content
            const hlNode = document.getElementById('headline-display');
            const smNode = document.getElementById('summary-display');
            
            const hlText = hlNode.innerText;
            const smText = smNode.innerText;
            
            // 2. Wrap for animation
            hlNode.innerHTML = wrapWords(hlText);
            smNode.innerHTML = wrapWords(smText);

            // GSAP Animations
            const tl = gsap.timeline();
            
            // 1. Card Entry (Pop in)
            tl.to("#mainCard", { duration: 0.6, opacity: 1, scale: 1, ease: "back.out(1.2)" });
            
            // 2. Header Elements
            tl.from(".brand-pill", { duration: 0.4, y: -20, opacity: 0, ease: "power2.out" }, "-=0.2");
            tl.from("#headline-label", { duration: 0.4, x: 20, opacity: 0, ease: "power2.out" }, "-=0.3");

            // 3. Headline: Staggered Word Reveal
            tl.to("#headline-display .word", { 
                duration: 0.6, 
                opacity: 1, 
                y: 0, 
                stagger: 0.05, 
                ease: "power3.out" 
            }, "-=0.2");

            // 4. Separator expand
            tl.from(".separator", { duration: 0.4, width: 0, opacity: 0, ease: "power2.out" }, "-=0.4");

            // 5. Summary: Staggered Word Reveal (Fast)
            tl.to("#summary-display .word", { 
                duration: 0.5, 
                opacity: 1, 
                y: 0, 
                stagger: 0.02, 
                ease: "power2.out" 
            }, "-=0.2");

            // 6. Footer Slide Up
            tl.from(".card-footer", { duration: 0.5, y: 30, opacity: 0, ease: "power2.out" }, "-=0.3");
        }
        
        // Initial set (hidden)
        gsap.set("#mainCard", { opacity: 0, scale: 0.95 });
    </script>
</body>
</html>
    """

    TICKER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Ticker Strip</title>
    <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@600&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; background: transparent; }
        .ticker-box {
            background: #FF0033; /* Red background for visibility */
            color: #FFFFFF;
            font-family: 'Chakra Petch', sans-serif;
            font-size: 32px;
            padding: 15px 30px;
            white-space: nowrap;
            border-radius: 8px;
            display: inline-block;
            text-transform: uppercase;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="ticker-box" id="ticker-content">{{TICKER_TEXT}}</div>
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
        import html
        
        with sync_playwright() as p:
            # CI/Linux often requires --no-sandbox
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            
            # Console listener for debugging JS errors
            page.on("console", lambda msg: print(f"PAGE LOG: {msg.text}"))
            page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

            # BAKE CONTENT INTO HTML (No JS Injection fragility)
            print("DEBUG: Baking content into HTML...")
            safe_headline = html.escape(headline or "Top Story")
            safe_summary = html.escape(summary_text or "Loading...")
            label = self._build_label(headline or "")
            safe_label = html.escape(label)

            final_html = self.HTML_TEMPLATE.replace("{{HEADLINE}}", safe_headline)\
                                           .replace("{{SUMMARY}}", safe_summary)\
                                           .replace("{{LABEL}}", safe_label)

            page.set_content(final_html, wait_until="load")
            
            # Trigger setup AND Animation
            print("DEBUG: Calling animateContent via JS...")
            page.evaluate("try { animateContent(); } catch(e) { console.error(e); }")
            
            # WAIT FOR GSAP ANIMATION TO COMPLETE
            # Animation duration sums to ~1.5s total including offsets. 
            # We wait 3.0s to be safe and capture the final settled state.
            print("Waiting for GSAP animations to settle...")
            time.sleep(3.0)

            # Capture Static Overlay (Final State)
            output_image_path = os.path.join(self.generated_dir, filename)
            print(f"Capturing Static Overlay to {output_image_path}...")
            
            page.screenshot(path=output_image_path, omit_background=True)
            
            # Verify Size
            size_kb = os.path.getsize(output_image_path) / 1024
            print(f"Overlay Size: {size_kb:.2f} KB")
            
            browser.close()
            
        return output_image_path

    def generate_ticker_image(self, text, filename="ticker_strip.png"):
        """
        Generates a wide image containing the ticker text for scrolling.
        """
        import html
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
            page = browser.new_page() # Default size
            
            # BAKE CONTENT
            safe_text = html.escape(text or "BREAKING NEWS")
            full_text = f"{safe_text}   ///   {safe_text}   ///   {safe_text}"
            final_html = self.TICKER_TEMPLATE.replace("{{TICKER_TEXT}}", full_text)
            
            page.set_content(final_html)
            
            # Element handle
            element = page.query_selector("#ticker-content")
            
            output_image_path = os.path.join(self.generated_dir, filename)
            element.screenshot(path=output_image_path, omit_background=True)
            
            browser.close()
            return output_image_path

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    gen = VisualGenerator()
    # Test
    # gen.generate_overlay("GSAP ADDED TO SYSTEM", "SYSTEM UPGRADE", "This is the summary text that sits in the center card.", 10)

