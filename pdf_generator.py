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
    """Generates PDF report in Russian from analysis data without calling GPT again."""

    _ensure_fonts()

    ki = analysis_data.get("key_indicators", {})
    report = analysis_data.get("report", {})
    insiders = analysis_data.get("insider_trades", [])

    currency = ki.get("currency_symbol", "$")

    def fmt(val, prefix="", suffix=""):
        if val is None:
            return "Н/Д"
        return f"{prefix}{val}{suffix}"

    fv = report.get("fair_value", {}) or {}
    fh = report.get("financial_health", {}) or {}
    swot = report.get("swot", {}) or {}

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    pdf.add_font("DejaVu", "", FONT_PATH)
    pdf.add_font("DejaVu", "B", FONT_BOLD_PATH)

    # Title
    pdf.set_font("DejaVu", "B", 24)
    pdf.set_text_color(212, 175, 55)
    pdf.cell(0, 10, str(ki.get("ticker", "")), new_x="LMARGIN", new_y="NEXT")

    # Subtitle
    pdf.set_font("DejaVu", "", 12)
    pdf.set_text_color(100, 100, 100)
    company = str(ki.get("company_name", ""))
    pdf.cell(0, 7, f"{company} — ИИ-отчёт от StockAI", new_x="LMARGIN", new_y="NEXT")

    # Interest level
    interest = report.get("interest_level", "")
    if interest:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(212, 175, 55)
        pdf.cell(0, 8, f"[ {interest} ]", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    def section_title(title: str):
        pdf.set_font("DejaVu", "B", 13)
        pdf.set_text_color(26, 26, 26)
        pdf.set_draw_color(212, 175, 55)
        pdf.set_line_width(0.5)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT", border="B")
        pdf.ln(3)

    def body_text(text: str):
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(40, 40, 40)
        if text:
            pdf.multi_cell(0, 5.5, str(text))
        pdf.ln(3)

    def bullet_list(items, color=(40, 40, 40)):
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(*color)
        for item in (items or []):
            pdf.cell(5, 5.5, "-", new_x="RIGHT", new_y="TOP")
            pdf.multi_cell(0, 5.5, str(item))
        pdf.ln(2)

    # Key Indicators
    section_title("Ключевые показатели")

    indicators = [
        ("Цена", fmt(ki.get("price"), currency)),
        ("Капитализация", fmt(ki.get("market_cap"), currency)),
        ("P/E", fmt(ki.get("pe_ratio"))),
        ("Fair Value", fmt(fv.get("estimate"), currency)),
        ("Forward P/E", fmt(ki.get("pe_forward"))),
        ("EPS", fmt(ki.get("eps_actual"), currency)),
        ("Потенциал", fmt(fv.get("upside_pct"), suffix="%") if fv.get("upside_pct") is not None else "Н/Д"),
        ("Дивиденды", fmt(ki.get("dividend_yield"), suffix="%") if ki.get("dividend_yield") is not None else "Н/Д"),
    ]

    col_w = (pdf.w - 40) / 4
    y_base = pdf.get_y()
    for i, (label, value) in enumerate(indicators):
        row = i // 4
        col = i % 4
        x = 20 + col * col_w
        y = y_base + row * 16
        pdf.set_xy(x, y)
        pdf.set_font("DejaVu", "", 8)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(col_w, 5, label.upper())
        pdf.set_xy(x, y + 5)
        pdf.set_font("DejaVu", "B", 13)
        pdf.set_text_color(26, 26, 26)
        pdf.cell(col_w, 7, str(value))

    pdf.set_y(y_base + (((len(indicators) - 1) // 4) + 1) * 16 + 4)

    section_title("Что происходит")
    body_text(report.get("what_is_happening", ""))

    section_title("Главный катализатор")
    body_text(report.get("main_catalyst", ""))

    section_title("Главный риск")
    body_text(report.get("main_risk", ""))

    section_title("Бычий сценарий")
    bullet_list(report.get("bull_case", []), color=(26, 122, 26))

    section_title("Медвежий сценарий")
    bullet_list(report.get("bear_case", []), color=(192, 57, 43))

    if swot:
        section_title("SWOT-анализ")
        half = (pdf.w - 40) / 2

        def swot_col(title, items, x_start, color):
            y_cur = pdf.get_y()
            pdf.set_xy(x_start, y_cur)
            pdf.set_font("DejaVu", "B", 10)
            pdf.set_text_color(*color)
            pdf.cell(half, 6, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("DejaVu", "", 9)
            for item in (items or []):
                pdf.set_x(x_start + 2)
                pdf.cell(4, 5, "-", new_x="RIGHT", new_y="TOP")
                pdf.multi_cell(half - 10, 5, str(item))
            return pdf.get_y()

        y0 = pdf.get_y()
        y_str = swot_col("Сильные стороны", swot.get("strengths"), 20, (26, 122, 26))
        pdf.set_y(y0)
        y_weak = swot_col("Слабые стороны", swot.get("weaknesses"), 20 + half, (192, 57, 43))
        pdf.set_y(max(y_str, y_weak) + 4)

        y0 = pdf.get_y()
        y_opp = swot_col("Возможности", swot.get("opportunities"), 20, (26, 74, 122))
        pdf.set_y(y0)
        y_thr = swot_col("Угрозы", swot.get("threats"), 20 + half, (160, 64, 0))
        pdf.set_y(max(y_opp, y_thr) + 4)

    section_title("Финансовое здоровье")
    score_line = (
        f"Общий балл: {fh.get('score', 'Н/Д')}/10   "
        f"Рост: {fh.get('growth_rating', 'Н/Д')}/10   "
        f"Рентабельность: {fh.get('profitability_rating', 'Н/Д')}/10   "
        f"Денежный поток: {fh.get('cashflow_rating', 'Н/Д')}/10"
    )
    pdf.set_font("DejaVu", "B", 11)
    pdf.set_text_color(212, 175, 55)
    pdf.cell(0, 7, score_line, new_x="LMARGIN", new_y="NEXT")
    body_text(fh.get("comment", ""))

    section_title("Справедливая стоимость")
    body_text(fv.get("methodology", ""))

    if insiders:
        section_title("Сделки инсайдеров")
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(26, 26, 26)
        pdf.set_fill_color(245, 245, 245)
        col_widths = [55, 55, 40, 30]
        headers = ["Имя", "Должность", "Тип", "Дата"]
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 7, h, border=1, fill=True)
        pdf.ln()
        pdf.set_font("DejaVu", "", 9)
        for trade in insiders[:8]:
            vals = [
                str(trade.get("name", ""))[:28],
                str(trade.get("title", ""))[:28],
                str(trade.get("transaction", ""))[:18],
                str(trade.get("date", ""))[:12],
            ]
            for i, v in enumerate(vals):
                pdf.cell(col_widths[i], 6, v, border=1)
            pdf.ln()

    pdf.ln(8)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(
        0, 5,
        "Данный отчёт сгенерирован искусственным интеллектом и предназначен только для информационных целей. "
        "Не является финансовой рекомендацией. Всегда проводите собственное исследование. © StockAI"
    )

    return bytes(pdf.output())
