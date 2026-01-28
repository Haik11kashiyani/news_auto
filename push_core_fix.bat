@echo off
git add src/news_fetcher.py src/script_gen.py main.py requirements.txt
git commit -m "Fix: Replace Gemini SDK with REST API & Fix Data Loss Bug"
git push origin main
