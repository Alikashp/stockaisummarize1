import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1"),
)


def analyze_earnings_call(transcript_data: dict, ticker: str) -> dict:
    content = transcript_data.get("content", "")[:15000]

    prompt = f"""Ты — финансовый аналитик. Проанализируй транскрипт earnings call компании {ticker} за {transcript_data.get("quarter")} {transcript_data.get("year")}.

ВАЖНО: Весь ответ на русском языке. Цитаты из звонка оставляй на английском в кавычках с переводом рядом.

ТРАНСКРИПТ:
{content}

Верни ТОЛЬКО валидный JSON без markdown-обёртки:
{{
  "key_themes": [
    {{"title": "Название темы", "description": "Описание на русском", "quote_en": "Точная цитата на английском", "quote_ru": "Перевод цитаты"}},
    {{"title": "...", "description": "...", "quote_en": "...", "quote_ru": "..."}},
    {{"title": "...", "description": "...", "quote_en": "...", "quote_ru": "..."}},
    {{"title": "...", "description": "...", "quote_en": "...", "quote_ru": "..."}}
  ],
  "management_tone": "Оценка тона: Уверенный/Осторожный/Защищающийся и т.д., с объяснением почему",
  "guidance_credibility": "Оценка достоверности прогнозов компании — история выполнения обещаний",
  "key_risks_mentioned": ["Риск 1 упомянутый менеджментом", "Риск 2", "Риск 3"],
  "qa_highlights": [
    {{"analyst_question": "О чём спросил аналитик", "management_response": "Суть ответа на русском"}},
    {{"analyst_question": "...", "management_response": "..."}},
    {{"analyst_question": "...", "management_response": "..."}}
  ]
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=3000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
