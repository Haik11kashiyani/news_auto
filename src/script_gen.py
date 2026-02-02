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

    def pick_and_generate_script(self, articles):
        """
        COMBINED: Picks the best article AND generates the video script in ONE Gemini call.
        This avoids hitting per-minute rate limits by reducing API calls.
        Returns: dict with 'chosen_article' and 'script' keys, or None on failure.
        """
        if not articles:
            return None
        if self.gemini_disabled or not self.api_key:
            print("Gemini disabled. Using backup for first article.")
            return {"chosen_article": articles[0], "script": self._backup_template(articles[0])}

        model_info = self._discover_model()
        if not model_info:
            print("No model available. Using backup.")
            return {"chosen_article": articles[0], "script": self._backup_template(articles[0])}

        model_name, version = model_info
        print(f"[COMBINED] Using Model: {model_name}")

        # Build listing for the prompt - FULL CONTENT for detailed scripts
        items_text = ""
        for idx, art in enumerate(articles):
            t = art.get("title", "") or ""
            # Use FULL content (up to 2000 chars) for detailed video scripts
            d = (art.get("full_content", "") or art.get("description", "") or "")[:2000]
            d = d.replace("\n", " ").strip()
            items_text += f"[{idx}] {t}\n{d}\n\n"

        prompt = f"""
You are a **top tier Indian news curator and video script writer** for viral vertical videos (YouTube Shorts, Reels).

## Task 1: Choose the BEST article
Below are {len(articles)} news articles. Pick the ONE that will go most viral.

IMPORTANT: Do NOT choose an article that is only a "developing story" or has no real content. Prefer complete, substantive news.

{items_text}

## Task 2: Generate Video Script for chosen article (TARGET: 60 seconds)
Create a video script that fits within a 60-SECOND SHORT VIDEO timeframe.

RULES FOR CONTENT LENGTH:
- Total video must be around 50-60 seconds when spoken aloud
- Each segment's "script" should be 2-3 sentences (about 10-12 seconds when spoken)
- 5 segments × 12 seconds = 60 seconds total

IF the article is long (more than 300 words):
- SUMMARIZE intelligently - keep ALL key facts, names, numbers, dates
- Focus on: WHO, WHAT, WHEN, WHERE, WHY, HOW
- DO NOT skip important details - compress them smartly
- Prioritize the most newsworthy/viral aspects

IF the article is short:
- Use ALL the content available
- Expand with context where helpful

=== EXTREMELY CRITICAL RULES FOR "script" FIELD ===
The "script" field will be read aloud by a TTS engine. ANY metadata will be SPOKEN OUT LOUD.

ABSOLUTELY FORBIDDEN in "script" field:
- "Voice", "Speak voice", "Speak voice name =", "Voice name =" (NEVER appear - will be spoken aloud)
- "Inner Engineer" or "voice = Inner Engineer" (metadata, not news)
- "Voice =" or "Voice:" or "Voice -" or "name =" or "Name ="
- "Narrator:" or "Speaker:" or "Audio:"
- "[pause]", "(Happy)", or any direction tags
- ANY prefix before the actual sentence

=== EXAMPLES OF WRONG "script" VALUES (will cause bugs) ===
WRONG: "Voice = Breaking news about politics"
WRONG: "Voice name = The stock market crashed today"
WRONG: "name = Scientists discover new treatment"
WRONG: "Narrator: The election results are in"
WRONG: "Voice: (Excited) This is amazing news"

=== EXAMPLES OF CORRECT "script" VALUES ===
CORRECT: "Breaking news about politics"
CORRECT: "The stock market crashed today"
CORRECT: "Scientists discover new treatment"
CORRECT: "The election results are in"

The script field should contain ONLY the spoken sentence, starting with the actual content.

Strictly output JSON only, no extra text:
{{
    "chosen_index": <0-based index of chosen article>,
    "headline": "Full headline (NO truncation, NO ellipsis)",
    "segments": [
        {{ "visual": "Key point 1 (max 25 words - make it detailed)", "script": "Detailed spoken sentence (2-3 sentences) - JUST the content, no prefixes." }},
        {{ "visual": "Key point 2 (max 25 words - make it detailed)", "script": "Detailed spoken sentence (2-3 sentences) - JUST the content, no prefixes." }},
        {{ "visual": "Key point 3 (max 25 words - make it detailed)", "script": "Detailed spoken sentence (2-3 sentences) - JUST the content, no prefixes." }},
        {{ "visual": "Key point 4 (max 25 words - make it detailed)", "script": "Detailed spoken sentence (2-3 sentences) - JUST the content, no prefixes." }},
        {{ "visual": "Key point 5 (max 25 words - make it detailed)", "script": "Detailed spoken sentence (2-3 sentences) - JUST the content, no prefixes." }}
    ],
    "viral_description": "YouTube description",
    "viral_tags": ["#tag1", "#tag2"]
}}

FINAL REMINDER: If you write "Voice" or "name =" in script field, it will be spoken aloud and ruin the video.
"""

        # RETRY LOGIC with Exponential Backoff
        max_retries = 3
        base_delay = 10  # seconds
        
        url = f"{self.base_url}/{version}/models/{model_name}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        for attempt in range(max_retries):
            try:
                # Pre-call delay (longer on retries)
                wait_time = base_delay * (2 ** attempt)  # 10s, 20s, 40s
                print(f"[Gemini] Attempt {attempt + 1}/{max_retries}, waiting {wait_time}s...")
                time.sleep(wait_time)

                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})

                if response.status_code == 200:
                    result = response.json()
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    clean_text = raw_text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(clean_text)

                    chosen_idx = int(data.get("chosen_index", 0))
                    if chosen_idx < 0 or chosen_idx >= len(articles):
                        chosen_idx = 0

                    chosen_article = articles[chosen_idx]
                    script = {k: v for k, v in data.items() if k != "chosen_index"}
                    
                    # CLEAN THE SCRIPT SEGMENTS AT SOURCE (FIRST LINE OF DEFENSE)
                    if "segments" in script:
                        import re
                        for seg in script["segments"]:
                            if "script" in seg:
                                s = seg["script"]
                                # DIRECT REMOVALS (exact patterns)
                                for bad in ["Voice name =", "voice name =", "Voice Name =",
                                            "Speak voice name =", "speak voice name =", "speek voice name =",
                                            "Voice =", "voice =", "Name =", "name =",
                                            "Speak voice =", "Inner Engineer", "voice = Inner Engineer"]:
                                    s = s.replace(bad, "")
                                # Remove Voice:/Narrator:/etc prefixes
                                s = re.sub(r'^(Voice|Narrator|Speaker|Audio|VO|Name)\s*[:=\-]?\s*', '', s, flags=re.IGNORECASE)
                                # Remove ANY word followed by = at start
                                s = re.sub(r'^[A-Za-z]+\s*[:=]\s*', '', s.strip())
                                # Remove emotion tags
                                s = re.sub(r'[\(\[\{](Happy|Sad|Excited|Serious|Urgent|Warm|Caution|Pause|Beat)[\)\]\}]', '', s, flags=re.IGNORECASE)
                                # Remove standalone Voice/Name/Speak voice name/typos
                                s = re.sub(r'\b(Voice|Name)\b', '', s, flags=re.IGNORECASE)
                                s = re.sub(r'\bInner\s*Engineer\b', '', s, flags=re.IGNORECASE)
                                s = re.sub(r'\b(ingenier|inginer)\b', '', s, flags=re.IGNORECASE)
                                s = re.sub(r'\bSpeak\s+voice\s+name\b', '', s, flags=re.IGNORECASE)
                                s = re.sub(r'\bSpeak\s+voice\b', '', s, flags=re.IGNORECASE)
                                s = re.sub(r'\bspeek\s+voice\s+name\b', '', s, flags=re.IGNORECASE)
                                # Clean double spaces
                                s = re.sub(r'\s+', ' ', s).strip()
                                seg["script"] = s
                    
                    print(f"[Gemini] Success on attempt {attempt + 1}")
                    return {"chosen_article": chosen_article, "script": script}

                elif response.status_code == 429:
                    print(f"[Gemini] Rate limited (429). Will retry after backoff...")
                    # Continue to next iteration (retry with longer delay)
                    continue
                else:
                    print(f"[Gemini] Error ({response.status_code}): {response.text}")
                    # Non-rate-limit error, try again
                    continue

            except Exception as e:
                print(f"[Gemini] Exception: {e}")
                continue

        # All retries exhausted - use backup
        print("[Gemini] All retries failed. Using backup template.")
        return {"chosen_article": articles[0], "script": self._backup_template(articles[0])}

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
        # PREFER FULL SCRAPED CONTENT
        description = news_article.get('full_content', '') or news_article.get('description', '') or news_article.get('content', '')[:500]
        
        prompt_text = f"""
You are a **top tier Indian news script writer** for viral vertical videos (YouTube Shorts, Reels).

Strictly output JSON only, no extra text:
{{
    "headline": "Viral, curiosity-driving title (max 85 chars)",
    "ticker_text": "Short, punchy ticker line",
    "segments": [
        {{ "visual": "Slide 1 text (Max 15 words)", "script": "Spoken sentence for this slide." }},
        {{ "visual": "Slide 2 text (Max 15 words)", "script": "Spoken sentence for this slide." }},
        {{ "visual": "Slide 3 text (Max 15 words)", "script": "Spoken sentence for this slide." }}
    ],
    "viral_description": "YouTube description",
    "viral_tags": ["#tag1", "..."],
    "video_search_keywords": ["keyword1", "keyword2"]
}}

Rules for "segments":
- Create 3-5 segments that flow logically.
- **SYNC IS CRITICAL**: The "script" text MUST match exactly what should be spoken while the "visual" text is shown.
- **NO FILLER**: Start immediately with the news.
- Tone: Urgent, Insider, Fast-paced.

Rules for visual text:
- NOT subtitles. Visual Headlines. Large font, few words.
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

        if self.gemini_disabled or not self.api_key:
             return self._backup_template(news_article)

    def _backup_template(self, article):
        """
        Last resort: Returns a valid script object so the pipeline DOES NOT CRASH.
        Enhanced to use FULL CONTENT and fix truncated headlines.
        """
        print("Using BACKUP TEMPLATE script.")
        title = article.get('title', 'Breaking News')
        
        # FIX: Detect and clean truncated titles (RSS feeds often have ... or …)
        if '...' in title or '…' in title or title.endswith("'"):
            # Title is truncated, try to get a cleaner one from content
            print("[Backup] Detected truncated title, extracting from content...")
            content = article.get('full_content', '') or article.get('description', '')
            if content:
                # Take first sentence as headline (up to first period or 100 chars)
                first_sentence = content.split('.')[0].strip()
                if len(first_sentence) > 20 and len(first_sentence) < 150:
                    title = first_sentence
                else:
                    # Just clean the existing title
                    title = title.replace('...', '').replace('…', '').strip()
                    if title.endswith("'") or title.endswith(":"):
                        title = title[:-1].strip()
        
        # Prioritize full scraped content -> description -> fallback
        content_source = article.get('full_content', '') or article.get('description', '') or "More details to follow."
        
        # Robust HTML cleaning using BeautifulSoup
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content_source, "html.parser")
            content_source = soup.get_text(separator=" ", strip=True)
        except ImportError:
            # Fallback if bs4 fails (though it should be installed)
            content_source = content_source.replace("<p>", "").replace("</p>", "").replace("<b>", "").replace("</b>", "").replace("\n", " ")
        except Exception as e:
            print(f"Error cleaning HTML: {e}")
            # Minimal cleanup
            content_source = content_source.replace("<", " ").replace(">", " ")
        
        full_title = str(title)
        
        # Build segments of roughly 150 chars (approx 25-30 words) - LONGER content
        segments = []
        words = content_source.split(" ")
        current_segment = []
        current_len = 0
        
        for word in words:
            if current_len + len(word) > 150:  # Increased from 75 to 150 for longer content
                text = " ".join(current_segment)
                segments.append({
                    "visual": text,
                    "script": text  # Script matches visual for backup
                })
                current_segment = [word]
                current_len = len(word)
            else:
                current_segment.append(word)
                current_len += len(word) + 1
        
        if current_segment:
            text = " ".join(current_segment)
            segments.append({"visual": text, "script": text})
            
        # Limit to max 5 segments for video length
        segments = segments[:5] 
        
        # If very short, ensure at least 1
        if not segments:
             segments = [{"visual": content_source[:100], "script": content_source}]

        return {
            "headline": full_title,  # No limit, now cleaned
            "segments": segments,
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
You are helping choose which news story will go most viral as a short vertical video for 'Logic Vault'.

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
