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
    calculated_ratings = ki.get("calculated_ratings", {})

    insiders = data.get("insider_trades", [])
    congress_text = ""
    if insiders:
        congress_text = "Сделки инсайдеров компании:\n"
        for t in insiders[:5]:
            congress_text += f"- {t['name']} ({t['title']}): {t['transaction']} {t['shares']} акций на сумму {t['value']} ({t['date']})\n"

    # Форматируем новости для промпта
    news_text = "\n".join(
        f"- {n['title']}" for n in news if n.get("title")
    ) or "Нет данных"

    # Готовые рейтинги (рассчитаны точно по формулам, не угадываются ИИ)
    cr_score = calculated_ratings.get("score", 5)
    cr_growth = calculated_ratings.get("growth_rating", 5)
    cr_profit = calculated_ratings.get("profitability_rating", 5)
    cr_cashflow = calculated_ratings.get("cashflow_rating", 5)

    prompt = f"""КРИТИЧЕСКИ ВАЖНО:
1. Весь ответ строго на русском языке
2. Пиши как умный друг-аналитик, не как робот
3. Конкретика вместо общих слов
4. Только валидный JSON без markdown

Ты — опытный аналитик и одновременно умный друг, который разбирается в акциях и рассказывает про них за чашкой кофе. Не сухие факты и не канцелярит — живой язык, интерпретация происходящего, конкретные причины и следствия. Не "выручка выросла на X%", а "компания последние полгода делала ставку на AI и это начинает окупаться". Расскажи историю компании прямо сейчас, а не отчитайся цифрами.

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

ФИНАНСОВЫЕ РЕЙТИНГИ (рассчитаны точно по формулам — используй их как есть, не меняй цифры):
Общий балл: {cr_score}/10
Рост: {cr_growth}/10
Рентабельность: {cr_profit}/10
Денежный поток: {cr_cashflow}/10

ЗАДАЧА: Верни ТОЛЬКО валидный JSON без markdown-обёртки, без ```json, без пояснений.

Формат ответа:
{{
  "what_is_happening": "3-4 абзаца живым языком. Не 'выручка выросла на X%', а 'компания последние полгода делала ставку на AI и это начинает окупаться'. Расскажи историю компании прямо сейчас.",
  "main_catalyst": "Одно предложение — главная причина почему акция может вырасти. Конкретно, с триггером.",
  "main_risk": "Одно предложение — главная угроза. Конкретно, что должно случиться чтобы акция упала.",
  "scenarios": {{
    "optimistic": "2-3 предложения. Если случится X — увидим цену Y. Конкретный триггер и конкретная цель.",
    "pessimistic": "2-3 предложения. Если случится X — увидим цену Y. Конкретный триггер и конкретная цель."
  }},
  "bull_case": [
    "Аргумент написанный как мысль аналитика, не как пункт списка. Например: 'Сервисный сегмент растёт быстрее железа — это меняет всю модель оценки компании'",
    "Аргумент 2 живым языком",
    "Аргумент 3 живым языком",
    "Аргумент 4 живым языком",
    "Аргумент 5 живым языком"
  ],
  "bear_case": [
    "Риск 1 живым языком",
    "Риск 2 живым языком",
    "Риск 3 живым языком",
    "Риск 4 живым языком",
    "Риск 5 живым языком"
  ],
  "swot": {{
    "strengths": ["Сила 1", "Сила 2", "Сила 3", "Сила 4"],
    "weaknesses": ["Слабость 1", "Слабость 2", "Слабость 3"],
    "opportunities": ["Возможность 1", "Возможность 2", "Возможность 3"],
    "threats": ["Угроза 1", "Угроза 2", "Угроза 3"]
  }},
  "financial_health": {{
    "score": {cr_score},
    "growth_rating": {cr_growth},
    "profitability_rating": {cr_profit},
    "cashflow_rating": {cr_cashflow},
    "comment": "2-3 предложения о финансовом состоянии живым языком, опираясь на эти рейтинги"
  }},
  "fair_value": {{
    "estimate": число (твоя оценка справедливой цены в $),
    "upside_pct": число (% потенциала от текущей цены),
    "methodology": "Одно предложение как считали"
  }},
  "interest_level": "Интересна для изучения / Требует осторожности / Не время",
  "interest_reason": "Одно предложение почему именно такой вывод"
}}"""

    print("guru_data в промпте:", guru_data)
    print(f"calculated_ratings: {calculated_ratings}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000,
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
    print(report["what_is_happening"])

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
