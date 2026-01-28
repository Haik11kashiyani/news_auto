import requests
import os
import json
import time

class NewsFetcher:
    def __init__(self):
        self.newsdata_api_key = os.getenv("NEWSDATA_API_KEY")
        self.worldnews_api_key = os.getenv("WORLDNEWS_API_KEY")
        self.processed_ids_file = "processed_ids.txt"
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self):
        if not os.path.exists(self.processed_ids_file):
            return set()
        with open(self.processed_ids_file, "r") as f:
            return set(line.strip() for line in f)

    def _save_processed_id(self, article_id):
        # Clean ID to be file-safe
        safe_id = str(article_id).replace("\n", "").strip()
        with open(self.processed_ids_file, "a") as f:
            f.write(f"{safe_id}\n")
        self.processed_ids.add(safe_id)

    def fetch_fresh_news(self):
        """
        Fetches fresh news. Priority: World News API (Realtime) -> NewsData.io (Backup).
        """
        all_news = []
        
        # 1. Try World News API (Best for Realtime + Images)
        if self.worldnews_api_key:
            print("Fetching from World News API (Realtime)...")
            wn_news = self._fetch_worldnews()
            if wn_news:
                return wn_news
        
        # 2. Fallback to NewsData.io
        if self.newsdata_api_key:
            print("Fetching from NewsData.io...")
            # Scope 1: India
            india_news = self._fetch_newsdata(params={"country": "in", "language": "en"})
            all_news.extend(india_news)
            time.sleep(1)
            # Scope 2: World
            world_news = self._fetch_newsdata(params={"category": "world", "language": "en"})
            all_news.extend(world_news)
            
        return all_news

    def _fetch_worldnews(self):
        """
        Provider: World News API
        Limit: 50 requests/day (Free)
        """
        url = "https://api.worldnewsapi.com/search-news"
        # Search for major news
        params = {
            "api-key": self.worldnews_api_key,
            "text": "headlines", 
            "source-countries": "in,us,gb", 
            "language": "en",
            "number": 5
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            fresh_articles = []
            if "news" in data:
                for article in data["news"]:
                    # Map to common format
                    article_id = str(article.get("id", article.get("url")))
                    if article_id not in self.processed_ids:
                        std_article = {
                            "article_id": article_id,
                            "title": article.get("title"),
                            "description": article.get("text", "")[:500],
                            "image_url": article.get("image"),
                            "source_id": "worldnewsapi"
                        }
                        fresh_articles.append(std_article)
                        self._save_processed_id(article_id)
            return fresh_articles
        except Exception as e:
            print(f"World News API failed: {e}")
            return []

    def _fetch_newsdata(self, params):
        url = "https://newsdata.io/api/1/news"
        params["apikey"] = self.newsdata_api_key
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            fresh_articles = []
            if "results" in data:
                for article in data["results"]:
                    article_id = article.get("article_id")
                    if article_id and article_id not in self.processed_ids:
                        # Ensure image_url key exists
                        article["image_url"] = article.get("image_url") 
                        fresh_articles.append(article)
                        self._save_processed_id(article_id)
            return fresh_articles
        except Exception as e:
            print(f"NewsData.io failed: {e}")
            return []

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    fetcher = NewsFetcher()
    news = fetcher.fetch_fresh_news()
    print(f"Fetched {len(news)} fresh articles.")
