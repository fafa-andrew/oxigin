import html
import bleach
import feedparser
import requests
import logging
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from django.db.models import Q
from feeds.models import Feed
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Fetcher:
    def __init__(self):
        self.current_time = datetime.now(timezone.utc)
        self.current_time_iso = self.current_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        self.feeds = self.__load_active_feeds()

    def __load_active_feeds(self, stale_minutes=10):
        stale_time = self.current_time - timedelta(minutes=stale_minutes)
        return Feed.objects.filter(is_active=True).filter(
            Q(last_fetched_at__lt=stale_time) | Q(last_fetched_at__isnull=True)
        )

    @staticmethod
    def __fetch_feed(feed_url):
        try:
            response = requests.get(feed_url, timeout=10)
            response.raise_for_status()

            return feedparser.parse(response.content)
        except requests.RequestException as e:
            logger.debug(f"Failed to fetch feed {feed_url}: {e}")
            return None

    def fetch_all_feeds(self):
        all_stories = []

        for feed in self.feeds:
            parsed_feed = self.__fetch_feed(feed.rss_url)
            if parsed_feed and parsed_feed.entries:
                for entry in parsed_feed.entries:
                    story = self.__normalize_entry(feed.name, entry)
                    all_stories.append(story)
                feed.last_fetched_at = datetime.now(timezone.utc)
                feed.save()

        return all_stories

    def __normalize_entry(self, name, entry):
        try:
            published = entry.get("published") or entry.get("updated") or entry.get("pubDate")
            content = self.__extract_content(entry) or entry.get("summary", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            title = entry.get("title", "")

            return {
                "source": name,
                "title_html": title,
                "title_text": html.unescape(title),
                "summary_html": self.__sanitize(summary),
                "summary_text": self.__extract_plain_text(summary),
                "content_html": self.__sanitize(content),
                "content_text": self.__extract_plain_text(content),
                "url": entry.get("link", ""),
                "author": entry.get("author", "") or entry.get("dc_creator", ""),
                "categories": [tag.get("term", "") for tag in entry.get("tags", []) if "term" in tag],
                "guid": entry.get("guid", ""),
                "published_at": self.__parse_date(published),
                "fetched_at": self.current_time_iso,
                "image_url": self.__extract_image(entry),
                "language": entry.get("language", "")
            }

        except Exception as e:
            logger.debug(f"Failed to normalize entry: {e}")
            return None

    @staticmethod
    def __parse_date(date_str):
        if not date_str:
            return None
        try:
            parsed_date = date_parser.parse(date_str)
            if parsed_date:
                return parsed_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        except (ValueError, TypeError):
            return None

    @staticmethod
    def __extract_image(entry):
        # Try to pull image from media content if available
        media_content = entry.get("media_content", [])
        if media_content and isinstance(media_content, list):
            return media_content[0].get("url", "")

        return ""

    @staticmethod
    def __extract_content(entry):
        content = entry.get("content", [])
        if isinstance(content, list) and content:
            return content[0].get("value", "") or ""
        return ""

    @staticmethod
    def __sanitize(html_content):
        safe_html = bleach.clean(html_content, tags={"p", "em", "a"}, attributes={"a": ["href"]})
        return safe_html

    @staticmethod
    def __extract_plain_text(html_content):
        plain_text = BeautifulSoup(html_content, "html.parser").get_text()
        return plain_text
