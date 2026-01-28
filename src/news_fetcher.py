import requests
import os
import json
import time

class NewsFetcher:
    def __init__(self):
        self.api_key = os.getenv("NEWSDATA_API_KEY")
        self.base_url = "https://newsdata.io/api/1/news"
        self.processed_ids_file = "processed_ids.txt"
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self):
        if not os.path.exists(self.processed_ids_file):
            return set()
        with open(self.processed_ids_file, "r") as f:
            return set(line.strip() for line in f)

    def _save_processed_id(self, article_id):
        with open(self.processed_ids_file, "a") as f:
            f.write(f"{article_id}\n")
        self.processed_ids.add(article_id)

    def fetch_fresh_news(self):
        """
        Fetches fresh news for both India and World categories.
        Timeframe: 3 (Last 3 hours)
        """
        all_news = []
        
        # Scope 1: India News
        print("Fetching India News...")
        india_news = self._fetch_news(params={
            "country": "in",
            "language": "en"
            # timeframe removed for Free Tier compatibility (422 Error)
        })
        all_news.extend(india_news)

        # Basic rate limit sleep between calls
        time.sleep(2)

        # Scope 2: World News
        print("Fetching World News...")
        world_news = self._fetch_news(params={
            "category": "world",
            "language": "en"
             # timeframe removed for Free Tier compatibility
        })
        all_news.extend(world_news)

        return all_news

    def _fetch_news(self, params):
        params["apikey"] = self.api_key
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            fresh_articles = []
            if "results" in data:
                for article in data["results"]:
                    article_id = article.get("article_id")
                    if article_id and article_id not in self.processed_ids:
                        fresh_articles.append(article)
                        self._save_processed_id(article_id)
            
            return fresh_articles
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    fetcher = NewsFetcher()
    news = fetcher.fetch_fresh_news()
    print(f"Fetched {len(news)} fresh articles.")
