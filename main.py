"""
Шаг 2.3 — FastAPI эндпоинт
POST /analyze — принимает тикер, возвращает полный отчёт
GET  /health  — проверка что сервер работает
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data_collector import get_stock_data
from ai_analyzer import generate_report

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

        # Возвращаем всё вместе
        return {
            "ticker": ticker,
            "key_indicators": data["key_indicators"],
            "analyst": data["analyst"],
            "news": data["news"],
            "insider_trades": data.get("insider_trades", []),
            "politician_trades": data.get("politician_trades", []),
            "price_history": data.get("price_history", []),
            "revenue_history": data.get("revenue_history", []),
            "report": report,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
