import time
from typing import List, Optional

import requests

from config import NEWSDATA_URL, RETRY_ATTEMPTS
from logger import get_logger
from models import ArticleRaw

logger = get_logger()


def fetch_top_news(api_key: str) -> List[ArticleRaw]:
    """Получает топ новости из NewsData.io с retry-логикой."""
    params = {
        "apikey": api_key,
        "language": "*",
    }

    last_exception: Optional[Exception] = None

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            logger.info(f"Fetching news from NewsData.io (attempt {attempt}/{RETRY_ATTEMPTS})")
            response = requests.get(NEWSDATA_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            raw_results = data.get("results", [])
            if not raw_results:
                logger.warning("No articles returned from NewsData.io")
                return []

            articles = []
            for item in raw_results:
                try:
                    article = ArticleRaw.model_validate(item)
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Skipping invalid article item: {e}")

            logger.info(f"Successfully fetched {len(articles)} articles")
            return articles

        except requests.RequestException as e:
            last_exception = e
            logger.warning(f"NewsData.io request failed on attempt {attempt}: {e}")
            if attempt < RETRY_ATTEMPTS:
                sleep_time = 2 ** (attempt - 1)
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"All {RETRY_ATTEMPTS} attempts to fetch news failed")
                raise last_exception

    return []
