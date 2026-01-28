import google.generativeai as genai
import os
import json
import time

class ScriptGenerator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found.")
        genai.configure(api_key=api_key)
        # Using flash model for speed/cost efficiency as per plan
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_script(self, news_article):
        """
        Generates a viral script for the given news article.
        """
        title = news_article.get('title', 'Breaking News')
        description = news_article.get('description', '') or news_article.get('content', '')[:500]
        
        prompt = f"""
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
        
        Ensure valid JSON output.
        """

        try:
            response = self.model.generate_content(prompt)
            # Simple cleanup to ensure JSON parsing if markdown fences are returned
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print(f"Error generating script: {e}")
            return None

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    gen = ScriptGenerator()
    # Mock article for testing
    mock_news = {"title": "Test News", "description": "This is a test description."}
    print(gen.generate_script(mock_news))
