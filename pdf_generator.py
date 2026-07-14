import os
import requests
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


def _ensure_fonts():
    for path, urls in FONT_SOURCES.items():
        if os.path.exists(path):
            continue
        for url in urls:
            try:
                print(f"Downloading font: {url}")
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                with open(path, "wb") as f:
                    f.write(r.content)
                print(f"Font saved: {path}")
                break
            except Exception as e:
                print(f"Failed {url}: {e}")
        else:
            raise RuntimeError(f"Could not download font: {path}")


def generate_pdf_report(analysis_data: dict) -> bytes:
    _ensure_fonts()

    ki = analysis_data.get("key_indicators", {})
    report = analysis_data.get("report", {})
    insiders = analysis_data.get("insider_trades", [])
    analyst_ratings = analysis_data.get("analyst_ratings", [])
    news = analysis_data.get("news", [])

    currency = ki.get("currency_symbol", "$")

    def fmt(val, prefix="", suffix=""):
        if val is None:
            return "Н/Д"
        return f"{prefix}{val}{suffix}"

    fv = report.get("fair_value", {}) or {}
    fh = report.get("financial_health", {}) or {}
    swot = report.get("swot", {}) or {}

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)

    pdf.add_font("DejaVu", "", FONT_PATH)
    pdf.add_font("DejaVu", "B", FONT_BOLD_PATH)

    W = pdf.w - 36  # content width

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
        pdf.set_x(18)
        pdf.set_font("DejaVu", "", 9.5)
        pdf.set_text_color(40, 40, 40)
        if text:
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
        style = "B" if bold else ""
        pdf.set_font("DejaVu", style, 8.5)
        pdf.set_text_color(26, 26, 26)
        for i, (col, w) in enumerate(zip(cols, widths)):
            pdf.cell(w, 6, str(col)[:40], border=1, fill=fill)
        pdf.ln()

    # ── Key Indicators (2×4 grid) ────────────────────────────
    section("Ключевые показатели")

    indicators = [
        ("Цена", fmt(ki.get("price"), currency)),
        ("Капитализация", fmt(ki.get("market_cap"), currency)),
        ("P/E", fmt(ki.get("pe_ratio"))),
        ("Fair Value", fmt(fv.get("estimate"), currency)),
        ("Forward P/E", fmt(ki.get("pe_forward"))),
        ("EPS", fmt(ki.get("eps_actual"), currency)),
        ("Потенциал роста", fmt(fv.get("upside_pct"), suffix="%") if fv.get("upside_pct") is not None else "Н/Д"),
        ("Дивиденды", fmt(ki.get("dividend_yield"), suffix="%") if ki.get("dividend_yield") is not None else "Н/Д"),
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

    # ── AI Analysis ──────────────────────────────────────────
    section("Что происходит")
    body(report.get("what_is_happening", ""))

    section("Главный катализатор")
    body(report.get("main_catalyst", ""))

    section("Главный риск")
    body(report.get("main_risk", ""))

    section("Бычий сценарий")
    bullets(report.get("bull_case", []), color=(26, 110, 26))

    section("Медвежий сценарий")
    bullets(report.get("bear_case", []), color=(180, 40, 40))

    # ── SWOT ─────────────────────────────────────────────────
    if swot:
        section("SWOT-анализ")
        half = W / 2

        def swot_col(title, items, x_start, color):
            y0 = pdf.get_y()
            pdf.set_xy(x_start, y0)
            pdf.set_font("DejaVu", "B", 9)
            pdf.set_text_color(*color)
            pdf.cell(half, 5.5, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("DejaVu", "", 8.5)
            for item in (items or []):
                pdf.set_x(x_start + 2)
                pdf.cell(4, 5, "-", new_x="RIGHT", new_y="TOP")
                w = max(1.0, x_start + half - pdf.get_x() - 2)
                pdf.multi_cell(w, 5, str(item))
            return pdf.get_y()

        y0 = pdf.get_y()
        y1 = swot_col("Сильные стороны", swot.get("strengths"), 18, (26, 110, 26))
        pdf.set_y(y0)
        y2 = swot_col("Слабые стороны", swot.get("weaknesses"), 18 + half, (180, 40, 40))
        pdf.set_y(max(y1, y2) + 3)

        y0 = pdf.get_y()
        y1 = swot_col("Возможности", swot.get("opportunities"), 18, (26, 74, 160))
        pdf.set_y(y0)
        y2 = swot_col("Угрозы", swot.get("threats"), 18 + half, (160, 80, 0))
        pdf.set_y(max(y1, y2) + 3)

    # ── Financial Health ─────────────────────────────────────
    section("Финансовое здоровье")
    score_line = (
        f"Общий балл: {fh.get('score', 'Н/Д')}/10    "
        f"Рост: {fh.get('growth_rating', 'Н/Д')}/10    "
        f"Рентабельность: {fh.get('profitability_rating', 'Н/Д')}/10    "
        f"Денежный поток: {fh.get('cashflow_rating', 'Н/Д')}/10"
    )
    pdf.set_x(18)
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(212, 175, 55)
    pdf.multi_cell(W, 6, score_line)
    body(fh.get("comment", ""))

    # ── Fair Value ───────────────────────────────────────────
    section("Справедливая стоимость")
    body(fv.get("methodology", ""))

    # ── Analyst Ratings ──────────────────────────────────────
    if analyst_ratings:
        section("Рейтинги аналитиков")
        widths = [28, 55, 45, 28, 18]
        table_row(["Дата", "Банк", "Рейтинг", "Действие", "Цель"], widths, bold=True, fill=True)
        for r in analyst_ratings[:12]:
            date = str(r.get("date", "") or r.get("Date", ""))[:10]
            firm = str(r.get("firm", "") or r.get("Firm", ""))
            rating = str(r.get("toGrade", "") or r.get("rating", "") or r.get("Rating", ""))
            action = str(r.get("action", "") or r.get("Action", ""))
            pt = str(r.get("priceTarget", "") or "")
            table_row([date, firm, rating, action, pt], widths)
        pdf.ln(2)

    # ── News ─────────────────────────────────────────────────
    if news:
        section("Последние новости")
        pdf.set_font("DejaVu", "", 8.5)
        pdf.set_text_color(40, 40, 40)
        for item in news[:8]:
            title = str(item.get("title", "") or item.get("Title", ""))
            date = str(item.get("providerPublishTime", "") or item.get("date", "") or "")
            if date and len(date) > 10:
                date = date[:10]
            pdf.set_x(18)
            pdf.set_font("DejaVu", "B", 8.5)
            pdf.multi_cell(W, 5, title)
            pdf.set_x(18)
            pdf.set_font("DejaVu", "", 7.5)
            pdf.set_text_color(130, 130, 130)
            pdf.cell(0, 4, date, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(40, 40, 40)
            pdf.ln(1)
        pdf.ln(1)

    # ── Insider Trades ───────────────────────────────────────
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
