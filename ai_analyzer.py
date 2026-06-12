"""
Шаг 2.2 — ИИ-анализ данных по акции
Использует: ProxyAPI → GPT-4o-mini
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1"),
)


def generate_report(data: dict) -> dict:
    """Отправляет данные в GPT и получает структурированный отчёт."""

    ki = data["key_indicators"]
    fh = data["financial_health"]
    gr = data["growth"]
    an = data["analyst"]
    news = data["news"]
    guru_data = data.get("guru_data", {})

    congress = data.get("congress_trades", [])
    congress_text = ""
    if congress:
        congress_text = "Сделки конгрессменов США:\n"
        for t in congress[:5]:
            congress_text += f"- {t['politician']} ({t['party']}): {t['transaction']} на сумму {t['amount']} ({t['date']})\n"

    # Форматируем новости для промпта
    news_text = "\n".join(
        f"- {n['title']}" for n in news if n.get("title")
    ) or "Нет данных"

    prompt = f"""КРИТИЧЕСКИ ВАЖНО: Весь ответ строго на русском языке.
Никакого английского текста в значениях JSON.
Все текстовые поля — только по-русски.

Ты — профессиональный финансовый аналитик. ВАЖНО: Весь ответ ТОЛЬКО на русском языке, без исключений. Даже если данные на английском — анализ, выводы и все текстовые поля пиши по-русски. Проанализируй акцию и составь отчёт строго в формате JSON.

ДАННЫЕ ПО АКЦИИ:
Компания: {ki['company_name']} ({ki['ticker']})
Цена: ${ki['price']}
52-нед. диапазон: ${ki['week_52_low']} — ${ki['week_52_high']}
Market Cap: {ki['market_cap']}
P/E: {ki['pe_ratio']} | P/E форвардный: {ki['pe_forward']}
EPS: {ki['eps_actual']} | EPS прогноз: {ki['eps_estimate']}
PEG: {ki['peg_ratio']} | EV/EBITDA: {ki['ev_ebitda']}
Выручка: {ki['revenue']} | Рост выручки: {gr['revenue_growth']}
Рост прибыли: {gr['earnings_growth']}
Маржа (gross): {ki['gross_margin']} | Маржа (net): {ki['profit_margin']}
ROE: {fh['return_on_equity']} | ROA: {fh['return_on_assets']}
Долг/Капитал: {fh['debt_to_equity']}
Free Cash Flow: {fh['free_cashflow']}
Дивиденды: {ki['dividend_yield']}
Отрасль: {ki['sector']} / {ki['industry']}

Рекомендация аналитиков: {an['recommendation']}
Целевая цена: ${an['target_mean_price']} (мин: ${an['target_low_price']}, макс: ${an['target_high_price']})
Кол-во аналитиков: {an['number_of_analysts']}

Описание бизнеса: {data['business']['description'][:800]}

Последние новости:
{news_text}

Данные GuruFocus:
GF Score: {guru_data.get('gf_score', 'Н/Д')}
DCF Fair Value: {guru_data.get('dcf_fair_value', 'Н/Д')}
GF Value: {guru_data.get('gf_value', 'Н/Д')}
Рейтинг прибыльности: {guru_data.get('profitability_rank', 'Н/Д')}
Финансовая устойчивость: {guru_data.get('financial_strength', 'Н/Д')}
Рейтинг роста: {guru_data.get('growth_rank', 'Н/Д')}
Предупреждения: {guru_data.get('warning_signs', [])}
Позитивные сигналы: {guru_data.get('positive_signs', [])}

{congress_text}

ЗАДАЧА: Верни ТОЛЬКО валидный JSON без markdown-обёртки, без ```json, без пояснений.

Формат ответа:
{{
  "executive_summary": "3-4 абзаца. Описание компании, текущее состояние бизнеса, ключевые события и финансовые результаты.",
  "fair_value": {{
    "estimate": число (твоя оценка справедливой цены в $),
    "upside_pct": число (% потенциала от текущей цены),
    "methodology": "краткое объяснение метода оценки"
  }},
  "financial_health": {{
    "score": число от 1 до 10,
    "growth_rating": число от 1 до 10,
    "profitability_rating": число от 1 до 10,
    "cashflow_rating": число от 1 до 10,
    "comment": "2-3 предложения об общем финансовом здоровье"
  }},
  "bull_case": [
    "Аргумент 1 в пользу роста",
    "Аргумент 2 в пользу роста",
    "Аргумент 3 в пользу роста",
    "Аргумент 4 в пользу роста",
    "Аргумент 5 в пользу роста"
  ],
  "bear_case": [
    "Риск 1",
    "Риск 2",
    "Риск 3",
    "Риск 4",
    "Риск 5"
  ],
  "swot": {{
    "strengths": ["Сила 1", "Сила 2", "Сила 3", "Сила 4"],
    "weaknesses": ["Слабость 1", "Слабость 2", "Слабость 3"],
    "opportunities": ["Возможность 1", "Возможность 2", "Возможность 3"],
    "threats": ["Угроза 1", "Угроза 2", "Угроза 3"]
  }},
  "pro_tips": [
    "Краткий инсайт 1 (позитивный)",
    "Краткий инсайт 2 (позитивный)",
    "Краткий инсайт 3 (нейтральный или негативный)"
  ],
  "technical_summary": "Strong Buy / Buy / Neutral / Sell / Strong Sell",
  "analyst_consensus": "Buy / Hold / Sell"
}}"""

    print("guru_data в промпте:", guru_data)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )
    except Exception as e:
        print(f"Ошибка вызова client.chat.completions.create: {e}")
        raise

    raw = response.choices[0].message.content.strip()

    # Чистим на случай если GPT всё же добавил markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


if __name__ == "__main__":
    # Тест: читаем сохранённый JSON от data_collector
    with open("AAPL_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Отправляю данные в GPT...")
    report = generate_report(data)

    print("\n--- EXECUTIVE SUMMARY ---")
    print(report["executive_summary"])

    print("\n--- FAIR VALUE ---")
    fv = report["fair_value"]
    print(f"Оценка: ${fv['estimate']} | Потенциал: {fv['upside_pct']}%")

    print("\n--- BULL CASE ---")
    for b in report["bull_case"]:
        print(f"✅ {b}")

    print("\n--- BEAR CASE ---")
    for b in report["bear_case"]:
        print(f"⚠️ {b}")

    # Сохраняем результат
    with open("AAPL_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nОтчёт сохранён в AAPL_report.json")
