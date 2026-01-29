import requests
import os
import json
import time
import feedparser

class NewsFetcher:
    def __init__(self):
        self.newsdata_api_key = os.getenv("NEWSDATA_API_KEY")
        self.worldnews_api_key = os.getenv("WORLDNEWS_API_KEY")
        self.processed_ids_file = "processed_ids.txt"
        self.processed_ids = self._load_processed_ids()
        # Curated free RSS feeds: mix of India + World.
        # Note: we only use title/summary/link as signals; we don't re-host full articles.
        self.rss_feeds_india = [
            "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
            "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",  # India
            "https://feeds.feedburner.com/ndtvnews-top-stories",
            "https://indianexpress.com/feed/",
            "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        ]
        self.rss_feeds_world = [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
            "https://rss.cnn.com/rss/edition_world.rss",
            "https://rss.cnn.com/rss/edition_asia.rss",
            "https://www.aljazeera.com/xml/rss/all.xml",
        ]

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
        Fetches fresh news.
        Priority:
          1) World News API (Realtime)
          2) NewsData.io (India + World)
          3) Curated RSS feeds (India + World)
        """
        all_news = []
        
        # 1. Try World News API (Best for Realtime + Images)
        if self.worldnews_api_key:
            print("Fetching from World News API (Realtime)...")
            wn_news = self._fetch_worldnews()
            all_news.extend(wn_news)
        
        # 2. NewsData.io (India + World)
        if self.newsdata_api_key:
            print("Fetching from NewsData.io...")
            # Scope 1: India
            india_news = self._fetch_newsdata(params={"country": "in", "language": "en"})
            all_news.extend(india_news)
            time.sleep(1)
            # Scope 2: World
            world_news = self._fetch_newsdata(params={"category": "world", "language": "en"})
            all_news.extend(world_news)

        # 3. RSS feeds (India + World) – fully free, no key.
        print("Fetching from RSS feeds (India + World)...")
        rss_news = self._fetch_rss_sources(self.rss_feeds_india + self.rss_feeds_world)
        all_news.extend(rss_news)

        return all_news

    def mark_as_processed(self, article_id):
        """
        Manually marks an article as processed (saved to file).
        Call this ONLY after video is successfully generated.
        """
        self._save_processed_id(article_id)

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
                        # REMOVED: self._save_processed_id(article_id) 
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
                        # REMOVED: self._save_processed_id(article_id)
            return fresh_articles
        except Exception as e:
            print(f"NewsData.io failed: {e}")
            return []

    def _fetch_rss_sources(self, feed_urls):
        """
        Fetch news from curated RSS feeds (India + World).
        We only use title + summary + link; full article stays on source site.
        """
        articles = []
        for url in feed_urls:
            try:
                print(f"Parsing RSS: {url}")
                feed = feedparser.parse(url)
                for entry in feed.entries[:10]:
                    link = getattr(entry, "link", None)
                    title = getattr(entry, "title", None)
                    summary = getattr(entry, "summary", "") or ""
                    if not title or not link:
                        continue
                    article_id = link
                    if article_id in self.processed_ids:
                        continue

                    # Try to pull an image URL if present.
                    image_url = None
                    media_content = getattr(entry, "media_content", None)
                    if media_content and isinstance(media_content, list):
                        image_url = media_content[0].get("url")
                    if not image_url and hasattr(entry, "links"):
                        for l in entry.links:
                            if isinstance(l, dict) and l.get("type", "").startswith("image/"):
                                image_url = l.get("href")
                                break

                    std_article = {
                        "article_id": article_id,
                        "title": title,
                        "description": summary[:600],
                        "image_url": image_url,
                        "source_id": "rss",
                        "source_url": link,
                    }
                    articles.append(std_article)
            except Exception as e:
                print(f"RSS fetch failed for {url}: {e}")
        return articles

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    fetcher = NewsFetcher()
    news = fetcher.fetch_fresh_news()
    print(f"Fetched {len(news)} fresh articles.")
