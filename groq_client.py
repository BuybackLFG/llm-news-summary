import random
import time
from typing import Optional

from openai import OpenAI

from config import GROQ_API_KEY, GROQ_API_URL, GROQ_MIN_INTERVAL_SEC, LLM_MODEL, RETRY_ATTEMPTS
from logger import get_logger
from models import ArticleRaw, SummarySchema

logger = get_logger()

_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_API_URL,
)


class GroqRateLimiter:
    """Ограничивает частоту запросов к Groq API (RPM 30 → минимум 2 сек между запросами)."""

    def __init__(self, min_interval: float = GROQ_MIN_INTERVAL_SEC):
        self._min_interval = min_interval
        self._last_request_time: Optional[float] = None

    def wait_if_needed(self) -> None:
        if self._last_request_time is not None:
            elapsed = time.monotonic() - self._last_request_time
            if elapsed < self._min_interval:
                sleep_time = self._min_interval - elapsed
                logger.debug(f"Rate limiter: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        self._last_request_time = time.monotonic()


_groq_limiter = GroqRateLimiter()


def _build_system_prompt() -> str:
    return (
        "Ты — ассистент для суммаризации новостей. "
        "Напиши краткое содержание строго в 2-3 предложениях. "
        "Требования:\n"
        "- Сохраняй нейтральный тон\n"
        "- Выделяй только факты, без мнений\n"
        "- Пиши на языке оригинальной новости"
    )


def _build_user_prompt(article: ArticleRaw) -> str:
    return (
        f"Заголовок: {article.title}\n"
        f"Описание: {article.description or 'N/A'}\n"
        f"Ссылка: {article.link}"
    )


def summarize_article(article: ArticleRaw) -> Optional[str]:
    """
    Отправляет статью в Groq API (openai/gpt-oss-120b) с Strict Mode Structured Outputs.
    Возвращает summary-строку или None при ошибке.
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            _groq_limiter.wait_if_needed()
            logger.info(
                f"Sending article to Groq (attempt {attempt}/{RETRY_ATTEMPTS}): {article.title[:60]}..."
            )

            response = _client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": _build_system_prompt()},
                    {"role": "user", "content": _build_user_prompt(article)},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "news_summary",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "summary": {
                                    "type": "string",
                                    "description": (
                                        "Краткое содержание новости в 2-3 предложениях, "
                                        "нейтральный тон, только факты, на языке оригинала"
                                    ),
                                }
                            },
                            "required": ["summary"],
                            "additionalProperties": False,
                        },
                    },
                },
            )

            content = response.choices[0].message.content
            parsed = SummarySchema.model_validate_json(content)
            logger.info(f"Successfully summarized: {article.title[:60]}...")
            return parsed.summary

        except Exception as e:
            logger.warning(f"Groq request failed on attempt {attempt}: {e}")
            if attempt < RETRY_ATTEMPTS:
                sleep_time = (2 ** (attempt - 1)) + random.uniform(0, 1)
                logger.info(f"Retrying Groq request in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(
                    f"All {RETRY_ATTEMPTS} attempts to summarize article failed: {article.link}"
                )

    return None
