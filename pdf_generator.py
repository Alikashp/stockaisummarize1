from fpdf import FPDF


def generate_pdf_report(analysis_data: dict) -> bytes:
    """Generates PDF report from analysis data without calling GPT again."""

    ki = analysis_data.get("key_indicators", {})
    report = analysis_data.get("report", {})
    insiders = analysis_data.get("insider_trades", [])

    currency = ki.get("currency_symbol", "$")

    def fmt(val, prefix="", suffix=""):
        if val is None:
            return "N/A"
        return f"{prefix}{val}{suffix}"

    fv = report.get("fair_value", {}) or {}
    fh = report.get("financial_health", {}) or {}
    swot = report.get("swot", {}) or {}

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(212, 175, 55)  # gold
    pdf.cell(0, 10, ki.get("ticker", ""), new_x="LMARGIN", new_y="NEXT")

    # Subtitle
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    company = ki.get("company_name", "")
    pdf.cell(0, 7, f"{company} — AI Report by StockAI", new_x="LMARGIN", new_y="NEXT")

    # Interest level badge
    interest = report.get("interest_level", "")
    if interest:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(212, 175, 55)
        pdf.cell(0, 8, f"[ {interest} ]", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    def section_title(title: str):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(26, 26, 26)
        pdf.set_draw_color(212, 175, 55)
        pdf.set_line_width(0.5)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT", border="B")
        pdf.ln(3)

    def body_text(text: str):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)
        if text:
            pdf.multi_cell(0, 5.5, text)
        pdf.ln(3)

    def bullet_list(items, color=(40, 40, 40)):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*color)
        for item in (items or []):
            pdf.cell(6, 5.5, chr(149), new_x="RIGHT", new_y="TOP")
            pdf.multi_cell(0, 5.5, str(item))
        pdf.ln(2)

    # Key Indicators
    section_title("Key Indicators")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)

    indicators = [
        ("Price", fmt(ki.get("price"), currency)),
        ("Market Cap", fmt(ki.get("market_cap"), currency)),
        ("P/E", fmt(ki.get("pe_ratio"))),
        ("Fair Value", fmt(fv.get("estimate"), currency)),
        ("Forward P/E", fmt(ki.get("pe_forward"))),
        ("EPS", fmt(ki.get("eps_actual"), currency)),
        ("Upside", fmt(fv.get("upside_pct"), suffix="%") if fv.get("upside_pct") is not None else "N/A"),
        ("Dividend Yield", fmt(ki.get("dividend_yield"), suffix="%") if ki.get("dividend_yield") is not None else "N/A"),
    ]

    col_w = (pdf.w - 40) / 4
    for i, (label, value) in enumerate(indicators):
        if i % 4 == 0 and i > 0:
            pdf.ln(14)
        x = 20 + (i % 4) * col_w
        pdf.set_xy(x, pdf.get_y())
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(col_w, 5, label.upper())
        pdf.set_xy(x, pdf.get_y() + 5)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(26, 26, 26)
        pdf.cell(col_w, 7, value)

    pdf.ln(22)

    # What is happening
    section_title("What's Happening")
    body_text(report.get("what_is_happening", ""))

    # Main catalyst
    section_title("Main Catalyst")
    body_text(report.get("main_catalyst", ""))

    # Main risk
    section_title("Main Risk")
    body_text(report.get("main_risk", ""))

    # Bull case
    section_title("Bull Case")
    bullet_list(report.get("bull_case", []), color=(26, 122, 26))

    # Bear case
    section_title("Bear Case")
    bullet_list(report.get("bear_case", []), color=(192, 57, 43))

    # SWOT
    if swot:
        section_title("SWOT Analysis")
        half = (pdf.w - 40) / 2

        def swot_block(title, items, color):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*color)
            pdf.cell(half, 6, title, new_x="RIGHT", new_y="TOP")

        pdf.set_xy(20, pdf.get_y())
        swot_block("Strengths", swot.get("strengths"), (26, 122, 26))
        pdf.set_xy(20 + half, pdf.get_y())
        swot_block("Weaknesses", swot.get("weaknesses"), (192, 57, 43))
        pdf.ln(6)

        def swot_items(items, x_start, color):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*color)
            for item in (items or []):
                pdf.set_x(x_start + 2)
                pdf.cell(3, 5, chr(149), new_x="RIGHT", new_y="TOP")
                saved_x = pdf.get_x()
                pdf.multi_cell(half - 8, 5, str(item))
                pdf.set_x(x_start + 2)

        y_start = pdf.get_y()
        swot_items(swot.get("strengths", []), 20, (26, 122, 26))
        y_after_str = pdf.get_y()

        pdf.set_y(y_start)
        swot_items(swot.get("weaknesses", []), 20 + half, (192, 57, 43))
        y_after_weak = pdf.get_y()

        pdf.set_y(max(y_after_str, y_after_weak) + 4)

        pdf.set_x(20)
        swot_block("Opportunities", swot.get("opportunities"), (26, 74, 122))
        pdf.set_x(20 + half)
        swot_block("Threats", swot.get("threats"), (160, 64, 0))
        pdf.ln(6)

        y_start2 = pdf.get_y()
        swot_items(swot.get("opportunities", []), 20, (26, 74, 122))
        y_opp = pdf.get_y()
        pdf.set_y(y_start2)
        swot_items(swot.get("threats", []), 20 + half, (160, 64, 0))
        y_thr = pdf.get_y()
        pdf.set_y(max(y_opp, y_thr) + 4)

    # Financial health
    section_title("Financial Health")
    score_line = (
        f"Overall: {fh.get('score', 'N/A')}/10   "
        f"Growth: {fh.get('growth_rating', 'N/A')}/10   "
        f"Profitability: {fh.get('profitability_rating', 'N/A')}/10   "
        f"Cash Flow: {fh.get('cashflow_rating', 'N/A')}/10"
    )
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(212, 175, 55)
    pdf.cell(0, 7, score_line, new_x="LMARGIN", new_y="NEXT")
    body_text(fh.get("comment", ""))

    # Fair value
    section_title("Fair Value")
    body_text(fv.get("methodology", ""))

    # Insider trades
    if insiders:
        section_title("Insider Trades")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(26, 26, 26)
        pdf.set_fill_color(245, 245, 245)
        col_widths = [55, 55, 40, 30]
        headers = ["Name", "Title", "Transaction", "Date"]
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 7, h, border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
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

    # Footer
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(
        0, 5,
        "This report was generated by artificial intelligence and is for informational purposes only. "
        "It does not constitute financial advice. Always conduct your own research. © StockAI"
    )

    return bytes(pdf.output())
