import os
import json
import time
import requests

class ScriptGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found.")
        self.base_url = "https://generativelanguage.googleapis.com"
        # If we hit quota / config issues, we can short‑circuit further Gemini calls
        # in this run and rely on the local backup template instead.
        self.gemini_disabled = False

    def _discover_model(self):
        """
        Dynamically asks Gemini API: "What models can I use?"
        Returns the best available model name.
        """
        if self.gemini_disabled or not self.api_key:
            return None
        try:
            # We check v1beta first as it has the newer models
            url = f"{self.base_url}/v1beta/models?key={self.api_key}"
            print(f"Discovering models from: {url.split('?')[0]}...")
            
            response = requests.get(url)
            if response.status_code != 200:
                print(f"ListModels failed: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            available_models = []
            
            for m in data.get('models', []):
                # We need a model that supports 'generateContent'
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    # Strip 'models/' prefix if present for clean usage
                    name = m['name'].replace("models/", "")
                    available_models.append(name)
            
            print(f"Available Models: {available_models}")
            
            # Priority Logic: Prefer 2.0 Flash -> 1.5 Flash -> Others
            # Note: "gemini-pro-latest" might be v1beta only. 
            # Safer to default all to v1beta unless explicitly known as v1 legacy.
            
            for m in available_models:
                if "gemini-2.0-flash" in m: return (m, "v1beta")
            for m in available_models:
                if "gemini-1.5-flash" in m: return (m, "v1beta")
            
            # If we fall back to generic names, be careful
            for m in available_models:
                if "gemini-pro" in m: 
                    # check if it's the legacy v1 or new v1beta
                    if "latest" in m or "1.5" in m:
                        return (m, "v1beta")
                    return (m, "v1")
                
            # If nothing specific found, take the first valid one and try v1beta (most modern)
            if available_models:
                return (available_models[0], "v1beta")
                
            return None
            
        except Exception as e:
            print(f"Model discovery error: {e}")
            return None

    def generate_script(self, news_article):
        # If Gemini is disabled (quota hit or no key), go straight to backup.
        if self.gemini_disabled or not self.api_key:
            return self._backup_template(news_article)

        # 1. Discover a working model
        model_info = self._discover_model()
        
        if not model_info:
            print("CRITICAL: No usable Gemini models found. Using Backup Template.")
            return self._backup_template(news_article)
            
        model_name, version = model_info
        print(f"Selected Model: {model_name} (API: {version})")
        
        # 2. Build Prompt
        title = news_article.get('title', 'Breaking News')
        description = news_article.get('description', '') or news_article.get('content', '')[:500]
        
        prompt_text = f"""
You are a **top tier Indian news script writer** for viral vertical videos (YouTube Shorts, Reels).

Strictly output JSON only, no extra text:
{{
    "headline": "Viral, curiosity-driving title (max 70 chars)",
    "sub_headline": "One-line summary that can sit under the headline on screen",
    "voice_script": "Full spoken script for the anchor, with emotional delivery",
    "ticker_text": "Short, punchy ticker line that can loop at bottom",
    "viral_description": "YouTube description with hooks + hashtags",
    "viral_tags": ["#tag1", "#tag2", "..."],
    "video_search_keywords": ["short keyword 1", "short keyword 2", "topic keyword 3"]
}}

Rules for voice_script:
- Length: about 40–55 seconds when spoken.
- Language style: conversational Indian English / Hinglish (no very hard words), feel like a human TV anchor.
- Start with a **strong hook in the first 3 seconds** that makes viewer stop scrolling.
- Use **emotion**: urgency, shock, empathy, and suspense where it makes sense.
- Break into **short, punchy sentences** (max 12–14 words per sentence).
- Add [pause] where natural for drama and breathing.
- Do NOT mention that this is AI generated.

Rules for on-screen text:
- "headline": must be short, clickable and curiosity-driven, max ~70 characters.
- "sub_headline": 1 compact sentence (max ~90 characters) that gives clarity about what exactly happened.
- "ticker_text": 1 short line that can repeat in a scrolling bar, ALL CAPS, very punchy.

Rules for other fields:
- "viral_description": 2–3 lines, first line is hook, then 4–6 hashtags.
- "viral_tags": only include tags useful for YouTube Shorts news (e.g. #breakingnews, #india, #shorts, #news, topic tags).
- "video_search_keywords": 3–6 compact keywords that describe the visual/story for stock footage search.

News Article Title: "{title}"
News Context (summary or description): "{description}"

Now return ONLY the JSON object as specified above.
        """

        # 3. Call API
        try:
            url = f"{self.base_url}/{version}/models/{model_name}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                # We omit generationConfig to be safe across all model types (v1 vs v1beta)
                # and rely on the robust prompt for JSON
            }
            
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            
            if response.status_code == 200:
                result = response.json()
                raw_text = result['candidates'][0]['content']['parts'][0]['text']
                clean_text = raw_text.replace('```json', '').replace('```', '').strip()
                return json.loads(clean_text)
            elif response.status_code == 429:
                # Quota exhausted – log once and disable Gemini for the rest of this run.
                self.gemini_disabled = True
                print("Gemini quota exhausted (429). Falling back to local backup template for this and future calls in this run.")
                return self._backup_template(news_article)
            else:
                print(f"Generation failed ({response.status_code}): {response.text}")
                return self._backup_template(news_article)
                
        except Exception as e:
            print(f"Generation Exception: {e}")
            return self._backup_template(news_article)

    def _backup_template(self, article):
        """
        Last resort: Returns a valid script object so the pipeline DOES NOT CRASH.
        """
        print("Using BACKUP TEMPLATE script.")
        title = article.get('title', 'Breaking News')
        full_title = str(title)
        return {
            "headline": f"Must Watch: {full_title}",
            "sub_headline": full_title,
            "voice_script": f"Breaking news from Newsroom. {full_title}. We are tracking this developing story and will bring you updates as they happen. Stay tuned.",
            "ticker_text": f"BREAKING: {full_title}",
            "viral_description": f"Breaking news: {full_title} #shorts #news",
            "viral_tags": ["#breaking", "#news"],
            "video_search_keywords": ["news", "breaking"]
        }

    def pick_best_article(self, articles):
        """
        Uses Gemini to choose the most viral/engaging article out of a small list.
        Returns the chosen article dict, or None on failure.
        """
        if not articles:
            return None
        if self.gemini_disabled or not self.api_key:
            print("Gemini disabled or no API key; skipping AI article ranking.")
            return None
        model_info = self._discover_model()
        if not model_info:
            print("No model for article ranking, falling back to random.")
            return None
        model_name, version = model_info

        # Build compact listing for prompt
        items = []
        for idx, art in enumerate(articles):
            t = art.get("title", "") or ""
            d = art.get("description", "") or art.get("content", "") or ""
            d_short = d[:160].replace("\n", " ")
            items.append(f"{idx}: {t} | {d_short}")
        joined = "\n".join(items)

        prompt = f"""
You are helping choose which news story will go most viral as a short vertical video for 'Newsroom'.

Here are candidate stories (index: title | short description):
{joined}

Think about which one is the most emotionally engaging, surprising, or highly relevant for a general audience today.
Return ONLY JSON of the form: {{"chosen_index": <NUMBER>}} with no extra text.
        """
        try:
            url = f"{self.base_url}/{version}/models/{model_name}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
            }
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code == 429:
                # Quota exhausted for ranking as well – disable Gemini to avoid noisy logs.
                self.gemini_disabled = True
                print("Gemini quota exhausted during article ranking (429). Skipping AI ranking for this and future runs in this process.")
                return None
            if resp.status_code != 200:
                print(f"Article ranking failed: {resp.status_code} - {resp.text}")
                return None
            data = resp.json()
            raw = data["candidates"][0]["content"]["parts"][0]["text"]
            clean = raw.replace("```json", "").replace("```", "").strip()
            obj = json.loads(clean)
            idx = int(obj.get("chosen_index", 0))
            if 0 <= idx < len(articles):
                return articles[idx]
            return None
        except Exception as e:
            print(f"Article ranking exception: {e}")
            return None

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    gen = ScriptGenerator()
    mock_news = {"title": "Test News", "description": "This is a test description."}
    print(gen.generate_script(mock_news))
