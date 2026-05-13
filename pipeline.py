from datetime import datetime, timezone
from typing import List

from config import NEWSDATA_API_KEY, OUTPUT_DIR
from groq_client import summarize_article
from logger import get_logger
from models import ArticleRaw, FinalOutput, ProcessedArticle
from news_fetcher import fetch_top_news

logger = get_logger()


def run() -> None:
    """Основной пайплайн: получение новостей → суммаризация → сохранение JSON."""
    logger.info("=== Pipeline started ===")

    raw_articles: List[ArticleRaw] = fetch_top_news(NEWSDATA_API_KEY)
    if not raw_articles:
        logger.warning("No articles fetched. Exiting.")
        return

    processed: List[ProcessedArticle] = []
    total = len(raw_articles)

    for idx, article in enumerate(raw_articles, start=1):
        logger.info(f"[{idx}/{total}] Summarizing: {article.title[:80]}...")
        summary = summarize_article(article)

        if summary is not None:
            processed.append(
                ProcessedArticle(summary=summary, original_data=article)
            )
        else:
            logger.warning(f"Failed to summarize article: {article.link}")

    result = FinalOutput(
        generated_at=datetime.now(timezone.utc).isoformat(),
        source_api="NewsData.io",
        llm_model="openai/gpt-oss-120b",
        total_raw_articles=total,
        total_summarized=len(processed),
        articles=processed,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"news_summary_{timestamp}.json"

    output_path.write_text(
        result.model_dump_json(indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info(
        f"Saved {len(processed)} of {total} summaries to {output_path}"
    )
    logger.info("=== Pipeline finished ===")
