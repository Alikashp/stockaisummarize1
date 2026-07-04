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
        "price_to_sales": info.get("priceToSalesTrailing12Months"),
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
        link = (
            content.get("canonicalUrl", {}).get("url")
            or content.get("clickThroughUrl", {}).get("url")
            or item.get("link", "")
        )
        news.append({
            "title": content.get("title", item.get("title", "")),
            "date": content.get("pubDate", ""),
            "summary": content.get("summary", "")[:300],
            "link": link,
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
    price_history, revenue_history = get_price_history(ticker)
    analyst_ratings = get_analyst_ratings(stock)
    calculated_ratings = calculate_financial_ratings(info)
    key_indicators["calculated_ratings"] = calculated_ratings
    annual_financials = get_annual_financials(stock)
    recommendation_trend = get_recommendation_trend(stock)

    return {
        "key_indicators": key_indicators,
        "business": business,
        "financial_health": financial_health,
        "growth": growth,
        "analyst": analyst,
        "analyst_ratings": analyst_ratings,
        "annual_financials": annual_financials,
        "recommendation_trend": recommendation_trend,
        "news": news,
        "guru_data": guru_data,
        "insider_trades": insider_trades,
        "politician_trades": politician_trades,
        "price_history": price_history,
        "revenue_history": revenue_history,
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

def calculate_financial_ratings(info: dict) -> dict:
    """Считает финансовые рейтинги по формулам на основе данных yfinance."""
    def score_metric(value, thresholds):
        if value is None:
            return 5
        for threshold, score in thresholds:
            if value >= threshold:
                return score
        return 1

    revenue_growth = info.get("revenueGrowth", 0) or 0
    earnings_growth = info.get("earningsGrowth", 0) or 0
    profit_margin = info.get("profitMargins", 0) or 0
    roe = info.get("returnOnEquity", 0) or 0
    debt_to_equity = info.get("debtToEquity", 0) or 0

    growth_score = score_metric(revenue_growth, [(0.25, 10), (0.15, 8), (0.08, 6), (0, 4), (-999, 1)])
    earnings_score = score_metric(earnings_growth, [(0.25, 10), (0.15, 8), (0.08, 6), (0, 4), (-999, 1)])
    growth_rating = round(growth_score * 0.6 + earnings_score * 0.4)

    margin_score = score_metric(profit_margin, [(0.25, 10), (0.15, 8), (0.08, 6), (0, 4), (-999, 1)])
    roe_score = score_metric(roe, [(0.25, 10), (0.15, 8), (0.08, 6), (0, 4), (-999, 1)])
    profitability_rating = round(margin_score * 0.6 + roe_score * 0.4)

    debt_score = 10 if debt_to_equity < 30 else 7 if debt_to_equity < 60 else 4 if debt_to_equity < 100 else 2
    cashflow_rating = round(profitability_rating * 0.5 + debt_score * 0.5)

    overall_score = round(growth_rating * 0.3 + profitability_rating * 0.35 + cashflow_rating * 0.35)

    return {
        "score": max(1, min(10, overall_score)),
        "growth_rating": max(1, min(10, growth_rating)),
        "profitability_rating": max(1, min(10, profitability_rating)),
        "cashflow_rating": max(1, min(10, cashflow_rating)),
    }


def get_annual_financials(stock) -> list:
    """Годовая выручка и чистая прибыль из финансовых отчётов yfinance."""
    annual = []
    try:
        financials = stock.financials
        if financials is not None and not financials.empty:
            revenue_row = financials.loc["Total Revenue"] if "Total Revenue" in financials.index else None
            income_row = financials.loc["Net Income"] if "Net Income" in financials.index else None

            def safe_val(row, col):
                if row is None:
                    return None
                try:
                    v = float(row[col])
                    return round(v / 1_000_000_000, 2) if math.isfinite(v) else None
                except (TypeError, ValueError):
                    return None

            for col in financials.columns[:5]:
                year = str(col.year) if hasattr(col, "year") else str(col)[:4]
                revenue = safe_val(revenue_row, col)
                net_income = safe_val(income_row, col)
                if revenue is not None:
                    annual.append({"year": year, "revenue": revenue, "net_income": net_income})
        annual.reverse()
    except Exception as e:
        print(f"Annual financials error: {e}")

    print(f"Annual financials: найдено {len(annual)} лет")
    return annual


def get_recommendation_trend(stock) -> dict:
    """Агрегированные рекомендации аналитиков (strongBuy/buy/hold/sell/strongSell)."""
    try:
        trend = stock.recommendations_summary
        if trend is not None and not trend.empty:
            latest = trend.iloc[0]
            return {
                "strong_buy": int(latest.get("strongBuy", 0)),
                "buy": int(latest.get("buy", 0)),
                "hold": int(latest.get("hold", 0)),
                "sell": int(latest.get("sell", 0)),
                "strong_sell": int(latest.get("strongSell", 0)),
            }
    except Exception as e:
        print(f"Recommendation trend error: {e}")
    return {}


def get_analyst_ratings(stock) -> list:
    """Получает последние рейтинги/действия аналитических банков через Yahoo Finance"""
    analyst_ratings = []
    try:
        upgrades = stock.upgrades_downgrades
        if upgrades is not None and not upgrades.empty:
            recent = upgrades.head(10)
            for date, row in recent.iterrows():
                to_grade = str(row.get("ToGrade") or row.get("To Grade") or "")
                action = str(row.get("Action") or "")
                firm = str(row.get("Firm") or "")
                analyst_ratings.append({
                    "firm": firm,
                    "to_grade": to_grade,
                    "action": action,
                    "date": str(date)[:10],
                })
    except Exception as e:
        print(f"Analyst ratings error: {e}")

    print(f"Analyst ratings: найдено {len(analyst_ratings)} рейтингов")
    return analyst_ratings

def get_politician_trades(ticker: str) -> list:
    """Получает данные о сделках конгрессменов через Quiver Quantitative API"""
    politician_trades = []
    try:
        quiver_key = os.getenv("QUIVER_API_KEY")
        url = f"https://api.quiverquant.com/beta/historical/congresstrading/{ticker.upper()}"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {quiver_key}", "Accept": "application/json"},
            timeout=10,
        )
        response.raise_for_status()

        all_trades = response.json()
        for t in all_trades[:10]:
            politician_trades.append({
                "senator": t.get("Representative", ""),
                "party": t.get("Party", ""),
                "transaction_date": t.get("TransactionDate", ""),
                "owner": t.get("House", ""),
                "asset_description": t.get("Ticker", ticker.upper()),
                "type": t.get("Transaction", ""),
                "amount": t.get("Range") or t.get("Amount", ""),
            })
    except Exception as e:
        print(f"Politician trades error: {e}")

    print(f"Politician trades: найдено {len(politician_trades)} сделок для {ticker}")
    return politician_trades

def get_price_history(ticker: str):
    """Получает историю цены за 1 год и квартальную выручку через yfinance"""
    price_history = []
    revenue_history = []

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y", interval="1wk")
        for date, row in hist.iterrows():
            price_history.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(float(row["Close"]), 2),
            })
    except Exception as e:
        print(f"Price history error: {e}")
        price_history = []

    try:
        stock = yf.Ticker(ticker)
        financials = stock.quarterly_financials
        if financials is not None and not financials.empty and "Total Revenue" in financials.index:
            revenue_row = financials.loc["Total Revenue"].dropna().iloc[:8]
            for date, value in revenue_row.items():
                quarter_label = f"Q{(date.month - 1) // 3 + 1} {date.year}"
                revenue_history.append({
                    "quarter": quarter_label,
                    "revenue": round(float(value) / 1_000_000_000, 2),
                })
            revenue_history = list(reversed(revenue_history))
    except Exception as e:
        print(f"Revenue history error: {e}")
        revenue_history = []

    return price_history, revenue_history


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
