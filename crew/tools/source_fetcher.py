import feedparser
from datetime import datetime, timedelta
from typing import List, Dict

class SourceFetcher:
    """Fetches content from RSS feeds and web sources"""
    
    def __init__(self, lookback_hours: int = 168):
        """
        Initialize source fetcher
        
        Args:
            lookback_hours: How many hours back to fetch content (default: 168 = 1 week)
        """
        self.lookback_hours = lookback_hours
        self.cutoff_date = datetime.now() - timedelta(hours=lookback_hours)
    
    def fetch_rss(self, url: str, source_name: str) -> List[Dict]:
        """Fetch entries from an RSS feed"""
        entries = []
        
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                # Parse published date
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                
                # Skip if too old (if date available)
                if pub_date and pub_date < self.cutoff_date:
                    continue
                
                # Extract entry data
                entry_data = {
                    'source': source_name,
                    'title': entry.get('title', 'No title'),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'published': pub_date.isoformat() if pub_date else 'Unknown',
                    'content': self._extract_content(entry)
                }
                
                entries.append(entry_data)
            
            print(f"[SourceFetcher] {source_name}: Fetched {len(entries)} entries")
            return entries
            
        except Exception as e:
            print(f"[SourceFetcher] Error fetching {source_name}: {str(e)}")
            return []
    
    def _extract_content(self, entry) -> str:
        """Extract full content from entry"""
        # Try content first (more complete)
        if hasattr(entry, 'content') and entry.content:
            return entry.content[0].get('value', '')
        
        # Fallback to summary
        if hasattr(entry, 'summary'):
            return entry.summary
        
        # Fallback to description
        if hasattr(entry, 'description'):
            return entry.description
        
        return ''
    
    def format_for_scout(self, entries: List[Dict]) -> str:
        """Format fetched entries for Scout agent consumption"""
        if not entries:
            return "No new content found in the specified timeframe."
        
        formatted = f"# Content Summary ({len(entries)} items)\n\n"
        
        for i, entry in enumerate(entries, 1):
            formatted += f"## Item {i}: {entry['title']}\n"
            formatted += f"**Source:** {entry['source']}\n"
            formatted += f"**Published:** {entry['published']}\n"
            formatted += f"**Link:** {entry['link']}\n\n"
            
            # Truncate very long content
            content = entry['summary'][:1000] if len(entry['summary']) > 1000 else entry['summary']
            formatted += f"{content}\n\n"
            formatted += "---\n\n"
        
        return formatted
