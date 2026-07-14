import io
import os
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from fpdf import FPDF

FONT_PATH = "/tmp/DejaVuSans.ttf"
FONT_BOLD_PATH = "/tmp/DejaVuSans-Bold.ttf"

FONT_SOURCES = {
    FONT_PATH: [
        "https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans.ttf",
        "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/main/ttf/DejaVuSans.ttf",
    ],
    FONT_BOLD_PATH: [
        "https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans-Bold.ttf",
        "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/main/ttf/DejaVuSans-Bold.ttf",
    ],
}

DARK_BG = "#0f0f0f"
GOLD = "#D4AF37"
GREEN = "#22c55e"
RED = "#ef4444"
TEAL = "#5eead4"


def _ensure_fonts():
    for path, urls in FONT_SOURCES.items():
        if os.path.exists(path):
            continue
        for url in urls:
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                with open(path, "wb") as f:
                    f.write(r.content)
                break
            except Exception as e:
                print(f"Font download failed {url}: {e}")
        else:
            raise RuntimeError(f"Could not download font: {path}")


def _get(d: dict, *keys, default=0):
    for k in keys:
        v = d.get(k)
        if v is not None and v != "" and v != 0:
            return v
    return default


def _chart_price(price_history: list) -> bytes | None:
    if not price_history:
        return None
    try:
        print(f"price_history[0] keys: {list(price_history[0].keys()) if price_history else 'empty'}")
        valid = []
        for p in price_history:
            d = str(_get(p, "date", "Date", "timestamp", default=""))
            c = _get(p, "close", "Close", "price", "Price", "adjClose", default=0)
            try:
                c = float(c)
            except (TypeError, ValueError):
                c = 0
            if c > 0:
                valid.append((d, c))

        if len(valid) < 2:
            print(f"Not enough price data: {len(valid)} points")
            return None

        dates = [v[0] for v in valid]
        closes = [v[1] for v in valid]

        fig, ax = plt.subplots(figsize=(7.5, 2.4))
        fig.patch.set_facecolor(DARK_BG)
        ax.set_facecolor(DARK_BG)
        ax.plot(range(len(closes)), closes, color=GOLD, linewidth=1.5)
        ax.fill_between(range(len(closes)), closes, alpha=0.12, color=GOLD)

        step = max(1, len(dates) // 6)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels([dates[i][:7] for i in range(0, len(dates), step)],
                           color="#888", fontsize=7, rotation=20)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}"))
        ax.tick_params(colors="#888", labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333")
        ax.grid(axis="y", color="#222", linewidth=0.5)
        ax.set_title("История цены", color="#ccc", fontsize=9, pad=6)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        print(f"Price chart error: {e}")
        return None


def _chart_financials(annual_financials: list) -> bytes | None:
    if not annual_financials:
        return None
    try:
        print(f"annual_financials[0] keys: {list(annual_financials[0].keys()) if annual_financials else 'empty'}")
        years, revenues, net_incomes = [], [], []
        for f in annual_financials:
            year = str(_get(f, "year", "Year", "fiscalYear", "date", default=""))[:4]
            # Values already in billions from data_collector
            rev = _get(f, "revenue", "Revenue", "totalRevenue", "Total Revenue", default=0)
            ni = _get(f, "net_income", "netIncome", "Net Income", "NetIncome", default=0)
            try:
                rev = float(rev)
                ni = float(ni)
            except (TypeError, ValueError):
                rev, ni = 0, 0
            if year and rev > 0:
                years.append(year)
                revenues.append(rev)
                net_incomes.append(ni)

        if not years:
            print("No valid financials data")
            return None

        x = range(len(years))
        w = 0.38
        fig, ax = plt.subplots(figsize=(7.5, 2.4))
        fig.patch.set_facecolor(DARK_BG)
        ax.set_facecolor(DARK_BG)
        ax.bar([i - w / 2 for i in x], revenues, width=w, color=GOLD, label="Выручка")
        ax.bar([i + w / 2 for i in x], net_incomes, width=w, color=TEAL, label="Чистая прибыль")
        ax.set_xticks(list(x))
        ax.set_xticklabels(years, color="#888", fontsize=8)
        ax.tick_params(colors="#888", labelsize=7)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}B"))
        for spine in ax.spines.values():
            spine.set_edgecolor("#333")
        ax.grid(axis="y", color="#222", linewidth=0.5)
        ax.set_title("Годовая динамика (млрд $)", color="#ccc", fontsize=9, pad=6)
        ax.legend(fontsize=7, facecolor="#1a1a1a", edgecolor="#444", labelcolor="#ccc")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        print(f"Financials chart error: {e}")
        return None


def generate_pdf_report(analysis_data: dict) -> bytes:
    _ensure_fonts()

    ki = analysis_data.get("key_indicators", {})
    report = analysis_data.get("report", {})
    insiders = analysis_data.get("insider_trades", [])
    analyst_ratings = analysis_data.get("analyst_ratings", [])
    news = analysis_data.get("news", [])
    price_history = analysis_data.get("price_history", [])
    annual_financials = analysis_data.get("annual_financials", [])
    recommendation_trend = analysis_data.get("recommendation_trend", {}) or {}

    currency = ki.get("currency_symbol", "$")

    fv = report.get("fair_value", {}) or {}
    if not isinstance(fv, dict):
        fv = {}
    fh = report.get("financial_health", {}) or {}
    if not isinstance(fh, dict):
        fh = {}
    swot = report.get("swot", {}) or {}
    if not isinstance(swot, dict):
        swot = {}

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)
    pdf.add_font("DejaVu", "", FONT_PATH)
    pdf.add_font("DejaVu", "B", FONT_BOLD_PATH)

    W = pdf.w - 36

    # ── Helpers ──────────────────────────────────────────────
    def section(title: str):
        pdf.set_x(18)
        pdf.set_font("DejaVu", "B", 12)
        pdf.set_text_color(26, 26, 26)
        pdf.set_draw_color(212, 175, 55)
        pdf.set_line_width(0.4)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT", border="B")
        pdf.ln(2)

    def body(text: str):
        if not text:
            return
        pdf.set_x(18)
        pdf.set_font("DejaVu", "", 9.5)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(W, 5, str(text))
        pdf.ln(2)

    def bullets(items, color=(40, 40, 40)):
        pdf.set_font("DejaVu", "", 9.5)
        pdf.set_text_color(*color)
        for item in (items or []):
            pdf.set_x(18)
            pdf.cell(5, 5, "-", new_x="RIGHT", new_y="TOP")
            pdf.multi_cell(W - 5, 5, str(item))
        pdf.ln(1)

    def table_row(cols, widths, bold=False, fill=False):
        pdf.set_x(18)
        if fill:
            pdf.set_fill_color(240, 240, 240)
        pdf.set_font("DejaVu", "B" if bold else "", 8.5)
        pdf.set_text_color(26, 26, 26)
        for col, w in zip(cols, widths):
            pdf.cell(w, 6, str(col)[:40], border=1, fill=fill)
        pdf.ln()

    def embed_chart(png_bytes: bytes, tmp_path: str, title: str):
        if not png_bytes:
            return
        with open(tmp_path, "wb") as f:
            f.write(png_bytes)
        section(title)
        pdf.set_x(18)
        pdf.image(tmp_path, x=18, w=W)
        pdf.ln(3)

    # ── Header ──────────────────────────────────────────────
    pdf.set_font("DejaVu", "B", 26)
    pdf.set_text_color(212, 175, 55)
    pdf.cell(0, 12, str(ki.get("ticker", "")), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", "", 11)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 6, f"{ki.get('company_name', '')} — ИИ-отчёт StockAI", new_x="LMARGIN", new_y="NEXT")

    interest = report.get("interest_level", "")
    if interest:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(212, 175, 55)
        pdf.cell(0, 7, f"[ {interest} ]", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)

    # ── 1. Key Indicators ────────────────────────────────────
    try:
        section("Ключевые показатели")
        indicators = [
            ("Цена", f"{currency}{ki.get('price', 'Н/Д')}"),
            ("Капитализация", f"{currency}{ki.get('market_cap', 'Н/Д')}"),
            ("P/E", str(ki.get("pe_ratio", "Н/Д"))),
            ("Fair Value", f"{currency}{fv.get('estimate', 'Н/Д')}"),
            ("Forward P/E", str(ki.get("pe_forward", "Н/Д"))),
            ("EPS", f"{currency}{ki.get('eps_actual', 'Н/Д')}"),
            ("Потенциал роста", f"{fv.get('upside_pct', 'Н/Д')}%"),
            ("Дивиденды", f"{ki.get('dividend_yield', 'Н/Д')}%"),
        ]
        col_w = W / 4
        y_base = pdf.get_y()
        for i, (label, value) in enumerate(indicators):
            row, col = i // 4, i % 4
            x = 18 + col * col_w
            y = y_base + row * 15
            pdf.set_xy(x, y)
            pdf.set_font("DejaVu", "", 7.5)
            pdf.set_text_color(130, 130, 130)
            pdf.cell(col_w, 4.5, label.upper())
            pdf.set_xy(x, y + 4.5)
            pdf.set_font("DejaVu", "B", 12)
            pdf.set_text_color(26, 26, 26)
            pdf.cell(col_w, 7, str(value))
        pdf.set_y(y_base + 32)
        pdf.set_x(18)
        pdf.ln(3)
    except Exception as e:
        print(f"Key indicators error: {e}")
        pdf.set_x(18)

    # ── 2. Financial Health ──────────────────────────────────
    try:
        section("Финансовое здоровье")
        score = fh.get("score", "Н/Д")
        growth_r = fh.get("growth_rating", "Н/Д")
        profit_r = fh.get("profitability_rating", "Н/Д")
        cash_r = fh.get("cashflow_rating", "Н/Д")
        score_line = f"Общий балл: {score}/10    Рост: {growth_r}/10    Рентабельность: {profit_r}/10    Денежный поток: {cash_r}/10"
        pdf.set_x(18)
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(212, 175, 55)
        pdf.multi_cell(W, 6, score_line)
        comment = fh.get("comment", "")
        if comment:
            body(str(comment))
        else:
            pdf.ln(2)
    except Exception as e:
        print(f"Financial health error: {e}")
        pdf.set_x(18)
        pdf.ln(3)

    # ── 3. Fair Value ────────────────────────────────────────
    try:
        section("Справедливая стоимость")
        lines = []
        if fv.get("estimate") is not None:
            lines.append(f"Оценка справедливой цены: {currency}{fv['estimate']}")
        if fv.get("upside_pct") is not None:
            lines.append(f"Потенциал роста от текущей цены: {fv['upside_pct']}%")
        if fv.get("methodology"):
            lines.append(str(fv["methodology"]))
        if lines:
            body("\n".join(lines))
        else:
            body("Данные недоступны")
    except Exception as e:
        print(f"Fair value error: {e}")
        pdf.set_x(18)
        pdf.ln(3)

    # ── 4. Analyst Consensus ─────────────────────────────────
    try:
        strong_buy = int(recommendation_trend.get("strong_buy", 0) or 0)
        buy = int(recommendation_trend.get("buy", 0) or 0)
        hold = int(recommendation_trend.get("hold", 0) or 0)
        sell = int(recommendation_trend.get("sell", 0) or 0)
        strong_sell = int(recommendation_trend.get("strong_sell", 0) or 0)
        total = strong_buy + buy + hold + sell + strong_sell
        if total > 0:
            section("Консенсус аналитиков")
            pdf.set_x(18)
            pdf.set_font("DejaVu", "", 9.5)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(W, 6,
                f"Strong Buy: {strong_buy}   Buy: {buy}   Hold: {hold}   "
                f"Sell: {sell}   Strong Sell: {strong_sell}   Всего: {total} аналитиков"
            )
            pdf.ln(2)
    except Exception as e:
        print(f"Analyst consensus error: {e}")
        pdf.set_x(18)
        pdf.ln(3)

    # ── 5. Charts ────────────────────────────────────────────
    try:
        price_png = _chart_price(price_history)
        embed_chart(price_png, "/tmp/_chart_price.png", "История цены")
    except Exception as e:
        print(f"Price chart embed error: {e}")

    try:
        fin_png = _chart_financials(annual_financials)
        embed_chart(fin_png, "/tmp/_chart_fin.png", "Годовая динамика")
    except Exception as e:
        print(f"Financials chart embed error: {e}")

    # ── 6. AI Analysis ───────────────────────────────────────
    try:
        section("Что происходит")
        body(str(report.get("what_is_happening", "") or ""))
    except Exception as e:
        print(f"What is happening error: {e}")

    try:
        section("Главный катализатор")
        body(str(report.get("main_catalyst", "") or ""))
    except Exception as e:
        print(f"Main catalyst error: {e}")

    try:
        section("Главный риск")
        body(str(report.get("main_risk", "") or ""))
    except Exception as e:
        print(f"Main risk error: {e}")

    try:
        section("Бычий сценарий")
        bullets(report.get("bull_case", []), color=(26, 110, 26))
    except Exception as e:
        print(f"Bull case error: {e}")

    try:
        section("Медвежий сценарий")
        bullets(report.get("bear_case", []), color=(180, 40, 40))
    except Exception as e:
        print(f"Bear case error: {e}")

    # ── 7. SWOT (simplified linear layout) ──────────────────
    try:
        if swot:
            section("SWOT-анализ")
            swot_items = [
                ("Сильные стороны", swot.get("strengths", []), (26, 110, 26)),
                ("Слабые стороны", swot.get("weaknesses", []), (180, 40, 40)),
                ("Возможности", swot.get("opportunities", []), (26, 74, 160)),
                ("Угрозы", swot.get("threats", []), (160, 80, 0)),
            ]
            for title, items, color in swot_items:
                pdf.set_x(18)
                pdf.set_font("DejaVu", "B", 9)
                pdf.set_text_color(*color)
                pdf.cell(0, 5.5, title, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("DejaVu", "", 8.5)
                pdf.set_text_color(40, 40, 40)
                for item in (items or []):
                    pdf.set_x(20)
                    pdf.cell(5, 5, "-", new_x="RIGHT", new_y="TOP")
                    pdf.multi_cell(W - 7, 5, str(item))
                pdf.ln(2)
    except Exception as e:
        print(f"SWOT error: {e}")
        pdf.set_x(18)
        pdf.ln(3)

    # ── 8. Analyst Ratings ───────────────────────────────────
    try:
        if analyst_ratings:
            section("Рейтинги аналитиков")
            widths = [28, 58, 44, 28, 16]
            table_row(["Дата", "Банк", "Рейтинг", "Действие", "Цель"], widths, bold=True, fill=True)
            for r in analyst_ratings[:12]:
                date = str(r.get("date", "") or "")[:10]
                firm = str(r.get("firm", "") or "")
                rating = str(r.get("to_grade", "") or r.get("toGrade", "") or r.get("rating", "") or "")
                action = str(r.get("action", "") or r.get("Action", "") or "")
                pt = str(r.get("priceTarget", "") or r.get("price_target", "") or "")
                table_row([date, firm, rating, action, pt], widths)
            pdf.ln(2)
    except Exception as e:
        print(f"Analyst ratings error: {e}")

    # ── 9. News ──────────────────────────────────────────────
    try:
        if news:
            section("Последние новости")
            for item in news[:8]:
                title = str(item.get("title", "") or item.get("Title", ""))
                date = str(item.get("providerPublishTime", "") or item.get("date", "") or "")
                if date and len(date) > 10:
                    date = date[:10]
                pdf.set_x(18)
                pdf.set_font("DejaVu", "B", 8.5)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(W, 5, title)
                pdf.set_x(18)
                pdf.set_font("DejaVu", "", 7.5)
                pdf.set_text_color(130, 130, 130)
                pdf.cell(0, 4, date, new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(40, 40, 40)
                pdf.ln(1)
            pdf.ln(1)
    except Exception as e:
        print(f"News error: {e}")

    # ── 10. Insider Trades ───────────────────────────────────
    try:
        if insiders:
            section("Сделки инсайдеров")
            widths = [52, 50, 36, 28]
            table_row(["Имя", "Должность", "Тип", "Дата"], widths, bold=True, fill=True)
            for trade in insiders[:8]:
                table_row([
                    str(trade.get("name", ""))[:28],
                    str(trade.get("title", ""))[:28],
                    str(trade.get("transaction", ""))[:18],
                    str(trade.get("date", ""))[:10],
                ], widths)
            pdf.ln(2)
    except Exception as e:
        print(f"Insider trades error: {e}")

    # ── Footer ───────────────────────────────────────────────
    pdf.ln(4)
    pdf.set_x(18)
    pdf.set_font("DejaVu", "", 7.5)
    pdf.set_text_color(160, 160, 160)
    pdf.multi_cell(W, 4.5,
        "Данный отчёт сгенерирован искусственным интеллектом и предназначен только для информационных целей. "
        "Не является финансовой рекомендацией. Всегда проводите собственное исследование. © StockAI"
    )

    return bytes(pdf.output())
