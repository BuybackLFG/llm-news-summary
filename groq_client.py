import json
import time
from typing import Optional

import requests

from config import GROQ_API_URL, GROQ_MIN_INTERVAL_SEC, LLM_MODEL, RETRY_ATTEMPTS
from logger import get_logger
from models import ArticleRaw, SummarySchema

logger = get_logger()


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


def _build_request_payload(article: ArticleRaw) -> dict:
    return {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": _build_user_prompt(article)},
        ],
        "response_format": {
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
    }


def summarize_article(article: ArticleRaw, api_key: str) -> Optional[str]:
    """
    Отправляет статью в Groq API (openai/gpt-oss-120b) с Strict Mode
    Возвращает summary-строку или None при ошибке.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = _build_request_payload(article)
    last_exception: Optional[Exception] = None

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            _groq_limiter.wait_if_needed()
            logger.info(
                f"Sending article to Groq (attempt {attempt}/{RETRY_ATTEMPTS}): {article.title[:60]}..."
            )

            response = requests.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            parsed = SummarySchema.model_validate_json(content)
            logger.info(f"Successfully summarized: {article.title[:60]}...")
            return parsed.summary

        except requests.RequestException as e:
            last_exception = e
            logger.warning(f"Groq request failed on attempt {attempt}: {e}")
        except (KeyError, json.JSONDecodeError, Exception) as e:
            last_exception = e
            logger.warning(f"Groq response parsing failed on attempt {attempt}: {e}")

        if attempt < RETRY_ATTEMPTS:
            sleep_time = 2 ** (attempt - 1)
            logger.info(f"Retrying Groq request in {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            logger.error(
                f"All {RETRY_ATTEMPTS} attempts to summarize article failed: {article.link}"
            )

    return None
