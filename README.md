# News Summarizer

Скрипт для автоматической суммаризации новостей: читает топовые новости из NewsData.io, отправляет их в LLM (Wormsoft AI) и сохраняет результат в JSON.

## Важно 

Из .gitignore убрано output/ , logs/, *.log для того что бы показать работу кода. 
при использовании следует добавить папки в исключение

## Что делает

1. Запрашивает топовые новости через [NewsData.io API](https://newsdata.io/)
2. Для каждой новости генерирует краткое содержание (2-3 предложения) через LLM `google/gemma4:31b`
3. Сохраняет результат в JSON-файл вместе с оригинальными данными

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

Создайте файл `.env` в корне проекта (или скопируйте `.env.example`):

```env
NEWSDATA_API_KEY=your_newsdata_api_key_here
WORMSOFT_API_KEY=your_wormsoft_api_key_here
```

Получить ключи:
- **NewsData.io**: https://newsdata.io/
- **Wormsoft AI**: https://ai.wormsoft.ru/

## Запуск

```bash
python main.py
```

Результат появится в папке `output/`:

```
output/
└── news_summary_20260115_143000.json
```

## Структура проекта

```
.
├── .env                  # API-ключи 
├── .env.example          # Шаблон .env
├── requirements.txt      # Зависимости
├── main.py               # Точка входа
├── config.py             # Конфигурация и переменные окружения
├── logger.py             # Логирование (консоль + файл)
├── models.py             # Pydantic-модели данных
├── news_fetcher.py       # Загрузка новостей из NewsData.io
├── llm_client.py         # Суммаризация через Wormsoft AI
├── pipeline.py           # Основной пайплайн
├── logs/                 # Лог-файлы
└── output/               # JSON-результаты
```

## Формат выходного JSON

```json
{
  "generated_at": "2026-01-15T14:30:00+00:00",
  "source_api": "NewsData.io",
  "llm_model": "google/gemma4:31b",
  "total_raw_articles": 10,
  "total_summarized": 10,
  "articles": [
    {
      "summary": "Краткое содержание новости в 2-3 предложениях...",
      "original_data": {
        "title": "Оригинальный заголовок",
        "link": "https://example.com/article",
        "pubDate": "2026-01-15T10:00:00Z",
        "description": "Описание новости",
        "source_id": "bbc-news",
        "language": "en"
      }
    }
  ]
}
```

## Особенности

- **Retry-логика**: при сбоях API выполняется до 3 попыток с экспоненциальной задержкой
- **Сырые данные сохраняются**: полный оригинал каждой статьи доступен в поле `original_data`
- **Нейтральный тон**: LLM инструктирована выделять только факты, без мнений
- **Язык оригинала**: суммаризация выполняется на языке исходной новости
