import feedparser
from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright
import argparse
import textwrap
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime
import logging
import re
logger = logging.getLogger(__name__)

# ===== Base class and Yahoo implementation =====
class BaseRSSScraper(ABC):
    def __init__(self, filter: str = ""):
        self.feed_url = self.get_feed_url()
        self.entries = []
        self.default_filter = filter if filter else ""

    @abstractmethod
    def get_feed_url(self):
        pass

    @abstractmethod
    def extract_article(self, url):
        pass
    
    def _apply_filter(self, articles: list[dict]):
        filtered_articles = [
            article for article in articles
            if self.default_filter in article.get('link', '')
        ]
        return filtered_articles

    def fetch_feed(self):
        feed = feedparser.parse(self.feed_url)
        self.entries = self._apply_filter(feed.entries)
        return self.entries

    def list_feed_items(self):
        if not self.entries:
            self.fetch_feed()
        return [{
            "title": e.get("title"),
            "link": e.get("link"),
            "published": e.get("published"),
        } for e in self.entries]

    def get_entry(self, index):
        if not self.entries:
            self.fetch_feed()
        if index < 0 or index >= len(self.entries):
            raise IndexError(f"Invalid index: {index}")
        return self.entries[index]

    def fetch_articles(self, max_workers: int = 5):
        if not self.entries:
            self.fetch_feed()
        results = []
        tasks = []
        link_prefix = filter if filter else self.default_filter

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for entry in self.entries:
                link = entry.get("link", "")
                tasks.append(executor.submit(self.extract_article, link))
            for future in as_completed(tasks):
                try:
                    article = future.result()
                    if article:
                        results.append(article)
                except Exception as e:
                    logger.info(f"[!] Failed to extract article: {e}")
        return results


class YahooFinanceScraper(BaseRSSScraper):
    def __init__(self):
        super(YahooFinanceScraper, self).__init__()
        self.default_filter = "https://finance.yahoo.com/news"


    def get_feed_url(self):
        return "https://finance.yahoo.com/rss/topstories"
    
    
    def extract_article_content(self, html, url):
        soup = BeautifulSoup(html, "html.parser")
        # 1. Title
        title_tag = soup.select_one(".cover-title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        # 2. Author
        author_tag = soup.select_one(".byline-attr-author")
        author = author_tag.get_text(strip=True) if author_tag else ""
        # 3. Time
        time_tag = soup.select_one("time.byline-attr-meta-time")
        time_str = time_tag["datetime"].strip() if time_tag and time_tag.has_attr("datetime") else ""
        # 4. Content (multiple <p> inside .body.yf-1ir6o1g)
        content_blocks = []
        for p in soup.select(".body p"):
            text = p.get_text(strip=True)
            if text:
                new_text = re.sub("Sign in to access your portfolio", "", text, flags=re.IGNORECASE)
                if new_text and new_text.strip():
                    content_blocks.append(new_text)
        content = "\n".join(content_blocks)
        return {
            "url": url,
            "title": title,
            "author": author,
            "published": time_str,
            "content": content
        }


    def extract_article(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                #page.wait_for_selector('#nimbus-app > section > section > section > article', timeout=30000)
                page.wait_for_load_state('domcontentloaded', timeout=60000)
                #page.wait_for_selector('main > section > section > section > section > article', timeout=60000)
                html = page.content()
                return self.extract_article_content(html, url)
            except Exception as e:
                return {"url": url, "error": str(e)}
            finally:
                browser.close()


def get_rss_scraper(rss_name: str):
    if rss_name == "yahoo":
        return YahooFinanceScraper()
    else:
        raise Exception(f"Unsupported RSS scraper: {rss_name}")
    

# ===== CLI Entrypoint =====
def list_news(rss_name):
    scraper = get_rss_scraper(rss_name)
    items = scraper.list_feed_items()
    for i, item in enumerate(items):
        logger.info(f"[{i}] {item['link']}")
        if 'error' in item:
            logger.error(f"    Error: {item['error']}")
        else:
            logger.info(f"    {item['title']}")
            logger.info(f"    {item['published']}\n")


def get_news(rss_name, index):
    scraper = get_rss_scraper(rss_name)
    try:
        entry = scraper.get_entry(index)
        logger.info(f"🔗 Fetching: {entry.link}\n")
        article = scraper.extract_article(entry.link)
        if article:
            logger.info(f"URL      : {article['url']}")
            if 'error' in article:
                logger.error(f"Error    : {article['error']}")
            else:
                logger.info(f"Title    : {article['title']}")
                logger.info(f"Published: {article['published']}")
                logger.info("Content  :\n")
                logger.info(textwrap.shorten(article['content'], width=1000, placeholder="..."))
        else:
            logger.info("[!] No content found.")
    except IndexError:
        logger.error(f"[!] Invalid index {index}")

def get_all_news(rss_name):
    start_time = time.time()
    scraper = get_rss_scraper(rss_name)
    logger.info(f"[{datetime.now()}] Start fetching all news from: {rss_name}")
    articles = scraper.fetch_articles()
    for i, article in enumerate(articles, 1):
        logger.info(f"\n{i}. {article.get('url')}")
        if 'error' in article:
            logger.error(f"Error: {article['error']}")
        else:
            logger.info(f"Title     : {article.get('title')}")
            logger.info(f"Published : {article.get('published')}")
            logger.info(f"Author    : {article.get('author')}")
            logger.info(f"Content   :\n{article.get('content')[:500]}...\n")

    end_time = time.time()
    logger.info(f"[{datetime.now()}] Finished. Total time: {end_time - start_time:.2f} seconds")


def main():
    parser = argparse.ArgumentParser(description="RSS News Scraper")
    subparsers = parser.add_subparsers(dest="command")
    parser_list = subparsers.add_parser("list-news", help="List news items from a RSS source")
    parser_list.add_argument("--rss", required=True, help="RSS source name (e.g. yahoo)")
    parser_get = subparsers.add_parser("get-news", help="Get full content of a news article")
    parser_get.add_argument("--rss", required=True, help="RSS source name")
    parser_get.add_argument("--n", required=True, type=int, help="Index of the news item")
    parser_get_all = subparsers.add_parser("get-all-news", help="Get full content of all news article")
    parser_get_all.add_argument("--rss", required=True, help="RSS source name")

    args = parser.parse_args()

    if args.command == "list-news":
        list_news(args.rss)
    elif args.command == "get-news":
        get_news(args.rss, args.n, args.translate)
    elif args.command == "get-all-news":
        get_all_news(args.rss)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
