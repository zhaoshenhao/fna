# run.py
from webui.agent.rss_scraper import get_rss_scraper
from webui.agent.translator import get_translator
from webui.agent.analyzer import get_analyzer
from concurrent.futures import ThreadPoolExecutor
from webui.models import NewsArticles
import logging
from django.conf import settings
from django.utils.timezone import now

logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self, workers: int = 5, test: bool = False):
        self.rss_scraper = get_rss_scraper(settings.RSS_SCRAPER)
        self.translator = get_translator(settings.TRANSLATOR)
        self.ai_analyzer = get_analyzer(settings.ANALYZER)
        self.articles = []
        self.workers = workers
        self.tasks = []
        self.test = test
        
    def is_dup(self, source_url: str) -> bool:
        if not source_url:
            return False
        qs = NewsArticles.objects.filter(source_url=source_url)
        return qs.exists()
        
    def run(self):
        self.articles = self.rss_scraper.list_feed_items()
        if not self.articles:
            logger.info("No articles to process after fetching and filtering. Exiting run.")
        if self.workers > 1:
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                for article in self.articles:
                    self.tasks.append(executor.submit(self.process_article, article))
        else:
            for article in self.articles:
                    self.process_article(article)

    def process_article(self, article):
        logger.info(f"Processing {article['link']}")
        # Check database
        logger.info("Check duplication...")
        if self.is_dup(article['link']):
            logger.info(f"Data exist for URL: {article['link']}")
            return

        if self.test:
            logger.info("Skip duplication check")
        else:
            pass
        # Extract Content
        logger.info("Extract content...")
        a2 = self.rss_scraper.extract_article(article['link'])
        if not a2:
            logger.warnning(f"Warning: Failed to extract content for '{article['title']}'. Skipping analysis.")
            return
        content = a2['content']
        author = a2['author']
        title = a2['title']
        url = a2['url']
        published = a2['published']
        # Translate content
        logger.info("Translating article content to Chinese...")
        translated_content = self.translator.translate_text(content)
        translated_title = self.translator.translate_text(title)
        if not translated_content:
            logger.warnning(f"Warning: Failed to translate content for '{title}'. Skipping analysis.")
            return
        # Analyze news impact
        logger.info("Analyzing news impact with AI...")
        analysis_result = self.ai_analyzer.analyze_news_impact(translated_title, translated_content)
        if analysis_result:
            if self.test:
                logger.info(f"url: {url}")
                logger.info(f"title: {title}")
                logger.info(f"published: {published}")
                logger.info(f"content: {content}")
                logger.info(f"cn_title: {translated_title}")
                logger.info(f"cn_content: {translated_content}")
                logger.info(f"Analysis:\n{analysis_result}")
            else:
                logger.info("Save to database...")
                a = NewsArticles(
                    title = title,
                    cn_title = translated_title,
                    original_content = content,
                    source_url = url,
                    source_name = settings.RSS_SCRAPER,
                    publish_date = published,
                    crawl_date = now(),
                    result = analysis_result,
                    translated_content = translated_content,
                    created_at = now(),
                    author = author,
                )
                try:
                    a.save()
                except Exception as e:
                    logger.error(e)
                logger.info("Save to database done.")
        else:
            logger.error(f"Failed to get analysis for '{article['title']}'.")


if __name__ == "__main__":
    p = Pipeline(test=True, workers=1)
    p.run()