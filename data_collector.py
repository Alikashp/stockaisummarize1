"""
Шаг 2.1 — Сбор данных по тикеру акции
Использует: yfinance (бесплатно, без API-ключа)
"""

import os
import math
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
    guru_data = {}
    try:
        gf_key = os.getenv("GURUFOCUS_API_KEY")
        print(f"GuruFocus API key found: {bool(gf_key)}")
        guru_url = f"https://api.gurufocus.com/data/stocks/{ticker}/summary"
        print(f"GuruFocus request URL: {guru_url}")
        guru_response = requests.get(guru_url, headers={"Authorization": gf_key})
        print(f"GuruFocus response status: {guru_response.status_code}")
        print(f"GuruFocus response (first 200 chars): {guru_response.text[:200]}")
        gf_json = guru_response.json()
        general = gf_json.get("summary", {}).get("general", {})
        guru_data = {
            "gf_score": general.get("gf_score"),
            "dcf_fair_value": general.get("price_dcf_projected_fcf"),
            "gf_value": general.get("gf_value"),
            "profitability_rank": general.get("rank_profitability"),
            "financial_strength": general.get("rank_financial_strength"),
            "growth_rank": general.get("rank_growth"),
            "warning_signs": general.get("warning_sign", []),
            "positive_signs": general.get("good_sign", []),
        }
        print(f"GuruFocus parsed guru_data: {guru_data}")
    except Exception as e:
        print(f"GuruFocus error: {e}")
        guru_data = {}
    insider_trades = get_insider_trades(stock)
    politician_trades = get_politician_trades(ticker)

    return {
        "key_indicators": key_indicators,
        "business": business,
        "financial_health": financial_health,
        "growth": growth,
        "analyst": analyst,
        "news": news,
        "guru_data": guru_data,
        "insider_trades": insider_trades,
        "politician_trades": politician_trades,
    }

TRANSACTION_TRANSLATIONS = {
    "Sale": "Продажа",
    "Purchase": "Покупка",
    "Stock Gift": "Дарение акций",
    "Option Exercise": "Исполнение опциона",
    "Stock Award": "Награждение акциями",
    "Tax Withholding": "Уплата налога",
    "Conversion of Exercise of derivative security": "Конвертация производной ценной бумаги",
}


def get_insider_trades(stock) -> list:
    """Получает данные о сделках инсайдеров через Yahoo Finance"""
    insider_trades = []
    try:
        insiders = stock.insider_transactions
        if insiders is not None and not insiders.empty:
            print(insiders.columns.tolist())
            print(insiders.head(2).to_dict())
            for _, row in insiders.head(10).iterrows():
                value = row.get("Value")
                if value and not (isinstance(value, float) and math.isnan(value)):
                    trade_value = value
                else:
                    trade_value = None
                transaction = row.get("Transaction") or row.get("Text", "")
                if " at price" in transaction:
                    transaction = transaction.split(" at price")[0]
                transaction = TRANSACTION_TRANSLATIONS.get(transaction, transaction)

                insider_trades.append({
                    "name": str(row.get("Insider", "")),
                    "title": str(row.get("Title") or row.get("Position", "")),
                    "transaction": str(transaction),
                    "shares": str(row.get("Shares", "")),
                    "value": trade_value,
                    "date": str(row.get("Start Date", ""))[:10],
                })
    except Exception as e:
        print(f"Insider trades error: {e}")

    print(f"Insider trades: найдено {len(insider_trades)} сделок")
    return insider_trades
    
def get_politician_trades(ticker: str) -> list:
    """Получает данные о сделках сенаторов через Senate Stock Watcher (открытый датасет, без ключа)"""
    politician_trades = []
    try:
        url = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        if int(response.headers.get("Content-Length", 0)) > 5 * 1024 * 1024:
            url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

        all_trades = response.json()
        ticker_upper = ticker.upper()
        trades_for_ticker = [
            t for t in all_trades if str(t.get("ticker", "")).upper() == ticker_upper
        ][:10]

        for t in trades_for_ticker:
            politician_trades.append({
                "senator": t.get("senator", ""),
                "party": t.get("party", ""),
                "transaction_date": t.get("transaction_date", ""),
                "owner": t.get("owner", ""),
                "asset_description": t.get("asset_description", ""),
                "type": t.get("type", ""),
                "amount": t.get("amount", ""),
            })
    except Exception as e:
        print(f"Politician trades error: {e}")

    print(f"Politician trades: найдено {len(politician_trades)} сделок для {ticker}")
    return politician_trades
        
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
