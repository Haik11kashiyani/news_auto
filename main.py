import os
import time
import json
from dotenv import load_dotenv

from src.news_fetcher import NewsFetcher
from src.script_gen import ScriptGenerator
from src.audio_gen import AudioGenerator
from src.visual_gen import VisualGenerator
from src.video_editor import VideoEditor

def main():
    load_dotenv()
    
    # 1. Init Modules
    fetcher = NewsFetcher()
    script_gen = ScriptGenerator()
    audio_gen = AudioGenerator()
    visual_gen = VisualGenerator()
    editor = VideoEditor()

    # 2. Fetch News
    print("--- 1. Fetching News ---")
    news_items = fetcher.fetch_fresh_news()
    print(f"Found {len(news_items)} new articles.")
    
    # Process max 1 article per run to avoid timeout/limits in MVP
    # Can loop for more later
    if not news_items:
        print("No new news to process.")
        return

    # Just take 1 for now (Dual Scope means we might get India or World, taking first fresh one)
    # Ideally prioritize India then World, but list is already ordered by fetch
    article = news_items[0] 
    print(f"Processing: {article.get('title')}")

    # 3. Generate Content
    print("--- 2. Generating Script ---")
    script_data = script_gen.generate_script(article)
    if not script_data:
        print("Failed to generate script.")
        return
    
    # 4. Generate Audio
    print("--- 3. Generating Audio ---")
    audio_path = f"generated/audio_{article['article_id']}.mp3"
    voice_script = script_data.get("voice_script", "")
    # Strip speaking instructions like [pause] for TTS if needed, or leave if engine supports it.
    # Play.ht v2 handles some, but let's clean for generic TTS
    clean_voice_text = voice_script.replace("[pause]", "...").replace("[URGENT]", "")
    
    if not audio_gen.generate_audio(clean_voice_text, audio_path):
        print("Failed to generate audio.")
        return

    # 5. Generate Visuals
    print("--- 4. Generating Visuals ---")
    keywords = script_data.get("video_search_keywords", [])
    bg_path, bg_type = visual_gen.get_background_video(article, keywords)
    
    overlay_text = script_data.get("ticker_text", "BREAKING NEWS")
    # Estimate audio duration (mock if file doesn't exist yet properly, but we have it)
    # We will let VideoEditor handle duration reading.
    # Overlay length is handled in Visual Gen but we need duration hint ideally.
    # For now, generate 15s sequence loop, editor truncates.
    overlay_path = visual_gen.generate_overlay(overlay_text, "LIVE", Duration=15) 

    if not bg_path or not overlay_path:
        print("Failed to generate visuals.")
        return

    # 6. Assemble Video
    print("--- 5. Assembling Video ---")
    output_filename = f"news_{article['article_id']}.mp4"
    final_path = editor.assemble_video(bg_path, bg_type, overlay_path, audio_path, output_filename)
    
    if final_path:
        print(f"SUCCESS: Video contents saved to {final_path}")
        # Note: Upload comes next
        print("--- 6. Upload Stub (Pending) ---")
        # uploader.upload(final_path, script_data)

if __name__ == "__main__":
    main()
