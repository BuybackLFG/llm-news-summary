import json
import random
import re
import time
from typing import Optional

from openai import OpenAI

from config import LLM_MODEL, RETRY_ATTEMPTS, WORMSOFT_API_KEY, WORMSOFT_API_URL
from logger import get_logger
from models import ArticleRaw, SummarySchema

logger = get_logger()

_client = OpenAI(
    api_key=WORMSOFT_API_KEY,
    base_url=WORMSOFT_API_URL,
)


def _build_system_prompt() -> str:
    return (
        "Ты — ассистент для суммаризации новостей. "
        "Напиши краткое содержание строго в 2-3 предложениях. "
        "Требования:\n"
        "- Сохраняй нейтральный тон\n"
        "- Выделяй только факты, без мнений\n"
        "- Пиши на языке оригинальной новости\n"
        "- Ответь строго в формате JSON: {\"summary\": \"твой текст\"}"
    )


def _build_user_prompt(article: ArticleRaw) -> str:
    return (
        f"Заголовок: {article.title}\n"
        f"Описание: {article.description or 'N/A'}\n"
        f"Ссылка: {article.link}"
    )


def _extract_json(text: str) -> Optional[str]:
    """Извлекает JSON из ответа модели (с markdown-обёрткой или без)."""
    # Сначала ищем markdown-блок ```json ... ```
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Ищем фигурные скобки
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0).strip()

    return text.strip() if text.strip() else None


def summarize_article(article: ArticleRaw) -> Optional[str]:
    """
    Отправляет статью в Wormsoft AI API (google/gemma4:31b).
    Возвращает summary-строку или None при ошибке.
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            logger.info(
                f"Sending article to Wormsoft AI (attempt {attempt}/{RETRY_ATTEMPTS}): {article.title[:60]}..."
            )

            response = _client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": _build_system_prompt()},
                    {"role": "user", "content": _build_user_prompt(article)},
                ],
            )

            raw_content = response.choices[0].message.content
            json_str = _extract_json(raw_content)

            if not json_str:
                logger.warning(f"No JSON found in response for: {article.title[:60]}...")
                if attempt < RETRY_ATTEMPTS:
                    sleep_time = (2 ** (attempt - 1)) + random.uniform(0, 1)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    continue
                else:
                    return None

            parsed = SummarySchema.model_validate_json(json_str)
            logger.info(f"Successfully summarized: {article.title[:60]}...")
            return parsed.summary

        except Exception as e:
            logger.warning(f"Wormsoft AI request failed on attempt {attempt}: {e}")
            if attempt < RETRY_ATTEMPTS:
                sleep_time = (2 ** (attempt - 1)) + random.uniform(0, 1)
                logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(
                    f"All {RETRY_ATTEMPTS} attempts to summarize article failed: {article.link}"
                )

    return None
