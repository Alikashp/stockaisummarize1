"""
Шаг 2.3 — FastAPI эндпоинт
POST /analyze — принимает тикер, возвращает полный отчёт
GET  /health  — проверка что сервер работает
"""

import math
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data_collector import get_stock_data
from ai_analyzer import generate_report
from earnings_analyzer import analyze_earnings_call


def sanitize(obj):
    """Рекурсивно заменяет nan/inf на None — стандартный JSON их не поддерживает."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj

app = FastAPI(
    title="Stock AI Analyzer",
    description="Анализ акций через ИИ",
    version="0.1.0",
)

# Разрешаем запросы с фронтенда (Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    ticker: str


@app.get("/health")
def health():
    return {"status": "ok", "message": "Stock AI Analyzer is running"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    ticker = request.ticker.upper().strip()

    if not ticker or len(ticker) > 10:
        raise HTTPException(status_code=400, detail="Некорректный тикер")

    try:
        # Шаг 1 — собираем данные
        data = get_stock_data(ticker)

        if not data["key_indicators"].get("price"):
            raise HTTPException(
                status_code=404,
                detail=f"Тикер {ticker} не найден или данные недоступны"
            )

        # Шаг 2 — ИИ-анализ
        report = generate_report(data)

        # Возвращаем всё вместе (sanitize убирает nan/inf, которые не валидны в JSON)
        return sanitize({
            "ticker": ticker,
            "key_indicators": data["key_indicators"],
            "analyst": data["analyst"],
            "analyst_ratings": data.get("analyst_ratings", []),
            "price_history_multi": data.get("price_history_multi", {}),
            "annual_financials": data.get("annual_financials", []),
            "recommendation_trend": data.get("recommendation_trend", {}),
            "news": data["news"],
            "insider_trades": data.get("insider_trades", []),
            "politician_trades": data.get("politician_trades", []),
            "price_history": data.get("price_history", []),
            "revenue_history": data.get("revenue_history", []),
            "report": report,
            "earnings_transcript_available": bool(data.get("earnings_transcript")),
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/earnings-call/{ticker}")
def get_earnings_call_analysis(ticker: str):
    ticker = ticker.upper().strip()
    try:
        data = get_stock_data(ticker)
        transcript = data.get("earnings_transcript")
        if not transcript:
            raise HTTPException(status_code=404, detail="Транскрипт недоступен для этого тикера")
        analysis = analyze_earnings_call(transcript, ticker)
        return {"ticker": ticker, "transcript_date": transcript.get("date"), "analysis": analysis}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
