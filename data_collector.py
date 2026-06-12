"""
Шаг 2.1 — Сбор данных по тикеру акции
Использует: yfinance (бесплатно, без API-ключа)
"""

import os
import yfinance as yf
import json
import requests
from datetime import datetime


def get_stock_data(ticker: str) -> dict:
    """Собирает все нужные данные по тикеру для ИИ-анализа."""

    # Если тикер без точки и состоит только из кириллицы или 
    # это известный паттерн MOEX — добавляем .ME
    # Пользователь может ввести SBER, GAZP, LKOH и любой другой
    if "." not in ticker:
        # Пробуем сначала как есть (американский)
        test = yf.Ticker(ticker)
        test_info = test.info
        if not test_info.get("regularMarketPrice") and not test_info.get("currentPrice"):
            # Данных нет — пробуем как российский
            ticker = ticker.upper() + ".ME"
    
    currency_symbol = "₽" if ".ME" in ticker else "$"
    
    stock = yf.Ticker(ticker)
    info = stock.info

    # --- Ключевые метрики (блок Key Indicators из PDF) ---
    key_indicators = {
        "ticker": ticker.upper(),
        "company_name": info.get("longName", "N/A"),
        "date": datetime.today().strftime("%Y-%m-%d"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "currency": info.get("currency", "USD"),
        "currency_symbol": currency_symbol,
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "pe_forward": info.get("forwardPE"),
        "eps_actual": info.get("trailingEps"),
        "eps_estimate": info.get("forwardEps"),
        "peg_ratio": info.get("pegRatio"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "price_to_book": info.get("priceToBook"),
        "revenue": info.get("totalRevenue"),
        "gross_margin": info.get("grossMargins"),
        "profit_margin": info.get("profitMargins"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }

    # --- Описание бизнеса (для Executive Summary) ---
    business = {
        "description": info.get("longBusinessSummary", "")[:1500],
        "employees": info.get("fullTimeEmployees"),
        "country": info.get("country"),
        "website": info.get("website"),
    }

    # --- Финансовое здоровье ---
    financial_health = {
        "total_cash": info.get("totalCash"),
        "total_debt": info.get("totalDebt"),
        "current_ratio": info.get("currentRatio"),
        "return_on_equity": info.get("returnOnEquity"),
        "return_on_assets": info.get("returnOnAssets"),
        "free_cashflow": info.get("freeCashflow"),
        "operating_cashflow": info.get("operatingCashflow"),
        "debt_to_equity": info.get("debtToEquity"),
        "quick_ratio": info.get("quickRatio"),
    }

    # --- Рост ---
    growth = {
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
    }

    # --- Рекомендации аналитиков ---
    analyst = {
        "recommendation": info.get("recommendationKey", "N/A"),
        "target_mean_price": info.get("targetMeanPrice"),
        "target_high_price": info.get("targetHighPrice"),
        "target_low_price": info.get("targetLowPrice"),
        "number_of_analysts": info.get("numberOfAnalystOpinions"),
    }

    # --- Последние новости (до 5 штук) ---
    news_raw = stock.news or []
    news = []
    for item in news_raw[:5]:
        content = item.get("content", {})
        news.append({
            "title": content.get("title", item.get("title", "")),
            "date": content.get("pubDate", ""),
            "summary": content.get("summary", "")[:300],
        })

        # --- Данные GuruFocus ---
    try:
        gurufocus_api_key = os.getenv("GURUFOCUS_API_KEY")
        print(f"GuruFocus API key found: {bool(gurufocus_api_key)}")
        guru_url = f"https://api.gurufocus.com/public/user/{gurufocus_api_key}/stock/{ticker}/summary"
        print(f"GuruFocus request URL: https://api.gurufocus.com/public/user/***/stock/{ticker}/summary")
        guru_response = requests.get(guru_url)
        print(f"GuruFocus response status: {guru_response.status_code}")
        print(f"GuruFocus response (first 200 chars): {guru_response.text[:200]}")
        guru_summary = guru_response.json().get("summary", {})
        guru_data = {
            "dcf_fair_value": guru_summary.get("dcf_msf"),
            "gf_value": guru_summary.get("gf_value"),
            "profitability_rank": guru_summary.get("rank_profitability"),
            "financial_strength": guru_summary.get("rank_balancesheet"),
            "warning_signs": guru_summary.get("warning_signs"),
            "positive_signs": guru_summary.get("good_signs"),
        }
    except Exception:
        guru_data = {}



def format_for_display(data: dict) -> str:
    """Красивый вывод в терминал для проверки."""
    ki = data["key_indicators"]
    an = data["analyst"]
    fh = data["financial_health"]

    def fmt_num(val, suffix=""):
        if val is None:
            return "N/A"
        if abs(val) >= 1_000_000_000:
            return f"${val/1_000_000_000:.1f}B{suffix}"
        if abs(val) >= 1_000_000:
            return f"${val/1_000_000:.0f}M{suffix}"
        return f"{val:.2f}{suffix}"

    lines = [
        f"\n{'='*50}",
        f"  {ki['company_name']} ({ki['ticker']}) — {ki['date']}",
        f"{'='*50}",
        f"  Цена:          ${ki['price']}",
        f"  52 нед. диап:  ${ki['week_52_low']} — ${ki['week_52_high']}",
        f"  Market Cap:    {fmt_num(ki['market_cap'])}",
        f"  P/E (тек.):    {ki['pe_ratio']}",
        f"  P/E (форв.):   {ki['pe_forward']}",
        f"  EPS (тек.):    {ki['eps_actual']}",
        f"  EPS (оценка):  {ki['eps_estimate']}",
        f"  Дивиденды:     {ki['dividend_yield']}",
        f"  Выручка:       {fmt_num(ki['revenue'])}",
        f"  Отрасль:       {ki['sector']} / {ki['industry']}",
        f"\n  --- Финансовое здоровье ---",
        f"  ROE:           {fh['return_on_equity']}",
        f"  ROA:           {fh['return_on_assets']}",
        f"  Долг/Капитал:  {fh['debt_to_equity']}",
        f"  Free Cash Flow:{fmt_num(fh['free_cashflow'])}",
        f"\n  --- Аналитики ---",
        f"  Рекомендация:  {an['recommendation'].upper()}",
        f"  Цель (средн.): ${an['target_mean_price']}",
        f"  Цель (макс.):  ${an['target_high_price']}",
        f"  Цель (мин.):   ${an['target_low_price']}",
        f"  Кол-во аналит: {an['number_of_analysts']}",
        f"\n  --- Последние новости ---",
    ]

    for i, n in enumerate(data["news"], 1):
        lines.append(f"  {i}. {n['title']}")

    lines.append(f"{'='*50}\n")
    return "\n".join(lines)


if __name__ == "__main__":
    TICKER = "AAPL"
    print(f"\nСобираю данные по {TICKER}...")

    data = get_stock_data(TICKER)

    # Вывод в терминал
    print(format_for_display(data))

    # Сохраняем JSON для следующего шага (передача в ИИ)
    with open(f"{TICKER}_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"Данные сохранены в {TICKER}_data.json")
    print("Готово к передаче в ИИ (Шаг 2.2)")
