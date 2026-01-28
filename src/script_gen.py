import os
import json
import time
import requests

class ScriptGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found.")
        
        # We will iterate manually over endpoints/models if needed
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def generate_script(self, news_article):
        """
        Generates a viral script using the Gemini REST API.
        Bypasses SDK versioning issues.
        """
        title = news_article.get('title', 'Breaking News')
        description = news_article.get('description', '') or news_article.get('content', '')[:500]
        
        prompt_text = f"""
        Role: You are the Lead Scriptwriter for "Logic Vault," a viral 2026 digital news network. Your specialty is high-retention, fast-paced news "Shorts" that combine the authority of a 20th-century TV anchor with the energy of a viral TikTok creator.

        Task: Transform the provided raw news data into a 45-second high-impact video script.

        Input News:
        Title: {title}
        Context: {description}

        Instructions:
        1. Voice Persona: Act as a high-octane 2026 digital news anchor. Tone: Urgent, Dramatic, Authoritative.
        2. Phonetic Guardrails: Spell difficult names/places phonetically in brackets (e.g., 'Ajit Pawar' as 'Uh-jeet Puh-vaar').
        3. Pacing: Use '...' for short breaths and '[pause]' for 1-second dramatic stops.
        4. Structure:
           - Hook (0-5s): Pattern-interrupting opening.
           - The Lead (5-35s): 3-4 punchy facts. "Sources on the ground confirm..."
           - The Outro (35-45s): Sharp opinion + "Logic Vault" branding.

        Output Format (Strict JSON):
        {{
            "headline": "Viral Title for Thumbnail",
            "voice_script": "[URGENT] BREAKING NEWS... [pause] ...",
            "ticker_text": "LATEST: {title} ...",
            "viral_description": "YouTube/Instagram Caption with hooks...",
            "viral_tags": ["#logicvault", "#breaking", "#news"],
            "video_search_keywords": ["keyword1", "keyword2"]
        }}
        
        Ensure valid JSON output. Do not include markdown naming like ```json.
        """

        # Define configurations: (Model Name, API Version, Mode)
        # Gemini 1.5 Flash is Free of Charge (15 RPM) - v1beta
        # Gemini 1.0 Pro is Free of Charge (15 RPM) - v1beta/v1
        configurations = [
            ("gemini-1.5-flash", "v1beta", "json"),
            ("gemini-1.5-pro", "v1beta", "json"),
            ("gemini-pro", "v1", "text"),      # Legacy Stable on v1
            ("gemini-1.0-pro", "v1beta", "text") 
        ]
        
        for model, version, mode in configurations:
            try:
                print(f"Trying {model} on {version} ({mode} mode)...")
                base_url = f"https://generativelanguage.googleapis.com/{version}/models"
                url = f"{base_url}/{model}:generateContent?key={self.api_key}"
                
                if mode == "json":
                    payload = {
                        "contents": [{"parts": [{"text": prompt_text}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    }
                else:
                    # Text mode fallback
                    payload = {
                        "contents": [{"parts": [{"text": prompt_text + "\nIMPORTANT: Return ONLY raw JSON. No markdown."}]}]
                    }
                
                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                
                if response.status_code == 200:
                    result = response.json()
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    # Clean markdown
                    clean_text = raw_text.replace('```json', '').replace('```', '').strip()
                    return json.loads(clean_text)
                else:
                    print(f"API Error ({model}): {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"Request failed for {model}: {e}")
                time.sleep(1)
        
        print("!!! ALL GEMINI MODELS FAILED !!!")
        return None

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    gen = ScriptGenerator()
    mock_news = {"title": "Test News", "description": "This is a test description."}
    print(gen.generate_script(mock_news))
