from typing import List, Optional

from pydantic import BaseModel


class ArticleRaw(BaseModel):
    title: str
    link: str
    pubDate: str
    description: Optional[str] = None
    source_id: Optional[str] = None
    language: Optional[str] = None


class SummarySchema(BaseModel):
    """Модель для валидации строгого JSON-ответа от Groq API."""
    summary: str


class ProcessedArticle(BaseModel):
    summary: str
    original_data: ArticleRaw


class FinalOutput(BaseModel):
    generated_at: str
    source_api: str
    llm_model: str
    total_raw_articles: int
    total_summarized: int
    articles: List[ProcessedArticle]
