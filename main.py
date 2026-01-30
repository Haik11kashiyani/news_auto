import os
import sys
import time
import json
from dotenv import load_dotenv

from src.news_fetcher import NewsFetcher
from src.script_gen import ScriptGenerator
from src.audio_gen import AudioGenerator
from src.visual_gen import VisualGenerator
from src.video_editor import VideoEditor

import random

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

    # 2b. Build small pool of candidates (top 5) and let Gemini pick the most
    #     viral/engaging one, instead of pure random.
    #     Filter out None/Empty if any.
    valid_items = [n for n in news_items if n]
    selection_pool = valid_items[:5] if len(valid_items) >= 5 else valid_items
    
    if not selection_pool:
         print("No valid news items.")
         return
    
    # Try AI-driven ranking first
    article = script_gen.pick_best_article(selection_pool)
    if article:
        print(f"Processing (AI-picked top story): {article.get('title')}")
    else:
        article = random.choice(selection_pool)
        print(f"Processing (Random fallback): {article.get('title')}")

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

    # 4. Generate Visuals (Multi-Slide)
    print("--- 4. Generating Visuals (Multi-Slide) ---")
    headline_text = script_data.get("headline", "BREAKING NEWS")
    ticker_text = script_data.get("ticker_text", "LIVE UPDATES")
    
    # Get segments or fallback to one big summary
    visual_segments = script_data.get("visual_segments")
    if not visual_segments:
        # Fallback if AI didn't return list
        single_summary = script_data.get("story_summary") or script_data.get("sub_headline") or "See video for details."
        visual_segments = [single_summary]

    overlay_paths = []
    print(f"Generating {len(visual_segments)} slides...")
    
    for idx, segment in enumerate(visual_segments):
        filename = f"slide_{idx}.png"
        path = visual_gen.generate_overlay(
            headline=headline_text,
            ticker_text=ticker_text,
            summary_text=segment,
            filename=filename
        )
        if path:
            overlay_paths.append(path)
    
    if not overlay_paths:
        print("Error: No overlays generated.")
        sys.exit(1)

    # Get Background (Video or Image)
    bg_path, bg_type = visual_gen.get_background_video(article, script_data.get("video_search_keywords", []))
    
    # 5. Assemble Video
    print("--- 5. Assembling Video ---")
    unique_ts = int(time.time())
    
    # Sanitize Filename (remove invalid chars)
    safe_article_id = str(article['article_id']).replace('/', '_').replace(':', '').replace('.', '')
    output_filename = f"news_{safe_article_id}_{unique_ts}.mp4"
    output_abs_path = os.path.join(os.getcwd(), "generated_videos", output_filename)
    # Ensure dir exists
    os.makedirs(os.path.dirname(output_abs_path), exist_ok=True)

    # Call editor with LIST of overlays
    final_path = editor.assemble_video(bg_path, bg_type, overlay_paths, audio_path, output_abs_path)
    
    if final_path and os.path.exists(final_path):
        print(f"SUCCESS: Video generated at {final_path}")
        # Mark as processed
        print(f"Marking article {article['article_id']} as processed...")
        fetcher.mark_as_processed(article['article_id'])
        
        # Note: Upload comes next
        print("--- 6. Upload Stub (Pending) ---")
        # uploader.upload(final_path, script_data)
    else:
        print("FAILURE: Video assembly failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
