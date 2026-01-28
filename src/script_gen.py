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

    def _discover_model(self):
        """
        Dynamically asks Gemini API: "What models can I use?"
        Returns the best available model name.
        """
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
        output_json_formatting:
        {{
            "headline": "Viral Title",
            "voice_script": "Script text...",
            "ticker_text": "Ticker text...",
            "viral_description": "Description...",
            "viral_tags": ["tag1", "tag2"],
            "video_search_keywords": ["keyword1", "keyword2"]
        }}
        
        Task: Create a 45s viral news script for 'Logic Vault'. 
        News: "{title}". Context: "{description}".
        Persona: High-energy 2026 anchor.
        Return ONLY valid JSON.
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
        return {
            "headline": f"Must Watch: {title[:30]}...",
            "voice_script": f"Breaking news from Logic Vault. {title}. We are tracking this developing story and will bring you updates as they happen. Stay tuned.",
            "ticker_text": f"BREAKING: {title}",
            "viral_description": f"Breaking news: {title} #shorts #news",
            "viral_tags": ["#breaking", "#news"],
            "video_search_keywords": ["news", "breaking"]
        }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    gen = ScriptGenerator()
    mock_news = {"title": "Test News", "description": "This is a test description."}
    print(gen.generate_script(mock_news))
