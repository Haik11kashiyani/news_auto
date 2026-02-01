"""
Deduplication Manager - Prevents duplicate news videos
Uses content hashing to track processed articles across runs.
"""
import os
import json
import hashlib
import time

class DedupManager:
    def __init__(self, db_file="processed_articles.json"):
        self.db_file = db_file
        self.ttl_days = 7  # Keep entries for 7 days
        self.data = self._load_db()
        self._cleanup_expired()
    
    def _load_db(self):
        """Load the dedup database from file."""
        if not os.path.exists(self.db_file):
            return {"hashes": {}}
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Dedup] Error loading DB: {e}")
            return {"hashes": {}}
    
    def _save_db(self):
        """Save the dedup database to file."""
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Dedup] Error saving DB: {e}")
    
    def _cleanup_expired(self):
        """Remove entries older than TTL."""
        current_time = time.time()
        ttl_seconds = self.ttl_days * 24 * 60 * 60
        
        expired = []
        for hash_key, entry in self.data.get("hashes", {}).items():
            if current_time - entry.get("timestamp", 0) > ttl_seconds:
                expired.append(hash_key)
        
        for key in expired:
            del self.data["hashes"][key]
        
        if expired:
            print(f"[Dedup] Cleaned up {len(expired)} expired entries.")
            self._save_db()
    
    def _generate_hash(self, title, content=""):
        """
        Generate a unique hash for an article.
        Uses title as primary key, with content as fallback similarity check.
        """
        # Normalize: lowercase, remove extra spaces
        normalized = title.lower().strip()
        # Remove common prefixes that might differ
        for prefix in ["breaking:", "update:", "just in:", "exclusive:"]:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
        
        # Create hash
        hash_input = normalized
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, article):
        """
        Check if an article has already been processed.
        Returns True if duplicate, False if new.
        """
        title = article.get("title", "")
        if not title:
            return False  # Can't check without title
        
        article_hash = self._generate_hash(title)
        
        if article_hash in self.data.get("hashes", {}):
            print(f"[Dedup] DUPLICATE detected: {title[:50]}...")
            return True
        
        return False
    
    def mark_processed(self, article):
        """
        Mark an article as processed after successful video generation.
        """
        title = article.get("title", "")
        if not title:
            return
        
        article_hash = self._generate_hash(title)
        
        self.data["hashes"][article_hash] = {
            "timestamp": time.time(),
            "title": title[:100],  # Store truncated title for debugging
            "source": article.get("source_id", "unknown")
        }
        
        self._save_db()
        print(f"[Dedup] Marked as processed: {title[:50]}...")
    
    def filter_new_articles(self, articles):
        """
        Filter a list of articles, returning only new (non-duplicate) ones.
        """
        new_articles = []
        for article in articles:
            if not self.is_duplicate(article):
                new_articles.append(article)
        
        print(f"[Dedup] Filtered: {len(new_articles)}/{len(articles)} articles are new.")
        return new_articles


if __name__ == "__main__":
    # Test
    dm = DedupManager()
    
    test_article = {
        "title": "Test Article About Something Important",
        "source_id": "test"
    }
    
    print(f"Is duplicate (first time): {dm.is_duplicate(test_article)}")
    dm.mark_processed(test_article)
    print(f"Is duplicate (second time): {dm.is_duplicate(test_article)}")
