from weasyprint import HTML


def generate_pdf_report(analysis_data: dict) -> bytes:
    """Генерирует PDF отчёт из уже готовых данных анализа (без повторного вызова GPT)."""

    ki = analysis_data.get("key_indicators", {})
    report = analysis_data.get("report", {})
    insiders = analysis_data.get("insider_trades", [])

    currency = ki.get("currency_symbol", "$")

    def fmt(val, prefix=""):
        if val is None:
            return "Н/Д"
        return f"{prefix}{val}"

    fv = report.get("fair_value", {}) or {}
    fh = report.get("financial_health", {}) or {}

    bull_items = "".join(f"<li>{b}</li>" for b in report.get("bull_case", []))
    bear_items = "".join(f"<li>{b}</li>" for b in report.get("bear_case", []))
    insider_rows = "".join(
        f"<tr><td>{i.get('name','')}</td><td>{i.get('title','')}</td>"
        f"<td>{i.get('transaction','')}</td><td>{i.get('date','')}</td></tr>"
        for i in insiders[:8]
    )

    swot = report.get("swot", {}) or {}
    swot_html = ""
    if swot:
        def swot_list(items, color):
            return "".join(f"<li style='color:{color}'>{item}</li>" for item in (items or []))
        swot_html = f"""
        <h2>SWOT-анализ</h2>
        <table>
          <tr>
            <td style="width:50%;vertical-align:top;padding:8px">
              <b>Сильные стороны</b>
              <ul>{swot_list(swot.get('strengths'), '#1a7a1a')}</ul>
            </td>
            <td style="width:50%;vertical-align:top;padding:8px">
              <b>Слабые стороны</b>
              <ul>{swot_list(swot.get('weaknesses'), '#c0392b')}</ul>
            </td>
          </tr>
          <tr>
            <td style="vertical-align:top;padding:8px">
              <b>Возможности</b>
              <ul>{swot_list(swot.get('opportunities'), '#1a4a7a')}</ul>
            </td>
            <td style="vertical-align:top;padding:8px">
              <b>Угрозы</b>
              <ul>{swot_list(swot.get('threats'), '#a04000')}</ul>
            </td>
          </tr>
        </table>
        """

    html_content = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{ font-family: 'DejaVu Sans', sans-serif; color: #1a1a1a; font-size: 12px; line-height: 1.6; }}
        h1 {{ color: #D4AF37; font-size: 28px; margin-bottom: 4px; }}
        h2 {{ color: #1a1a1a; font-size: 15px; border-bottom: 2px solid #D4AF37; padding-bottom: 5px; margin-top: 22px; margin-bottom: 10px; }}
        .subtitle {{ color: #666; margin-bottom: 16px; font-size: 13px; }}
        .indicators {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 12px 0; }}
        .indicator {{ width: 22%; }}
        .indicator-label {{ font-size: 9px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
        .indicator-value {{ font-size: 17px; font-weight: bold; }}
        .badge {{ display: inline-block; padding: 4px 14px; border-radius: 12px; background: #D4AF37; color: #000; font-weight: bold; font-size: 11px; margin-bottom: 4px; }}
        p {{ margin: 6px 0; }}
        ul {{ padding-left: 18px; margin: 6px 0; }}
        li {{ margin-bottom: 6px; line-height: 1.5; }}
        .bull li {{ color: #1a7a1a; }}
        .bear li {{ color: #c0392b; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 6px; }}
        th, td {{ text-align: left; padding: 5px 6px; border-bottom: 1px solid #e0e0e0; font-size: 10px; }}
        th {{ background: #f5f5f5; font-weight: bold; }}
        .footer {{ margin-top: 28px; font-size: 9px; color: #999; border-top: 1px solid #ddd; padding-top: 8px; }}
        .score {{ font-size: 20px; font-weight: bold; color: #D4AF37; }}
    </style>
    </head>
    <body>
        <h1>{ki.get('ticker', '')}</h1>
        <div class="subtitle">{ki.get('company_name', '')} &mdash; ИИ-отчёт от StockAI</div>
        <span class="badge">{report.get('interest_level', '')}</span>

        <h2>Ключевые показатели</h2>
        <div class="indicators">
            <div class="indicator">
                <div class="indicator-label">Цена</div>
                <div class="indicator-value">{fmt(ki.get('price'), currency)}</div>
            </div>
            <div class="indicator">
                <div class="indicator-label">Капитализация</div>
                <div class="indicator-value">{fmt(ki.get('market_cap'), currency)}</div>
            </div>
            <div class="indicator">
                <div class="indicator-label">P/E</div>
                <div class="indicator-value">{fmt(ki.get('pe_ratio'))}</div>
            </div>
            <div class="indicator">
                <div class="indicator-label">Fair Value</div>
                <div class="indicator-value">{fmt(fv.get('estimate'), currency)}</div>
            </div>
            <div class="indicator">
                <div class="indicator-label">Forward P/E</div>
                <div class="indicator-value">{fmt(ki.get('pe_forward'))}</div>
            </div>
            <div class="indicator">
                <div class="indicator-label">EPS</div>
                <div class="indicator-value">{fmt(ki.get('eps_actual'), currency)}</div>
            </div>
            <div class="indicator">
                <div class="indicator-label">Потенциал</div>
                <div class="indicator-value">{fmt(fv.get('upside_pct'), '')}{'%' if fv.get('upside_pct') is not None else ''}</div>
            </div>
            <div class="indicator">
                <div class="indicator-label">Дивиденды</div>
                <div class="indicator-value">{fmt(ki.get('dividend_yield'), '')}{'%' if ki.get('dividend_yield') is not None else ''}</div>
            </div>
        </div>

        <h2>Что происходит</h2>
        <p>{report.get('what_is_happening', '').replace(chr(10), '<br>')}</p>

        <h2>Главный катализатор</h2>
        <p>{report.get('main_catalyst', '')}</p>

        <h2>Главный риск</h2>
        <p>{report.get('main_risk', '')}</p>

        <h2>Бычий сценарий</h2>
        <ul class="bull">{bull_items}</ul>

        <h2>Медвежий сценарий</h2>
        <ul class="bear">{bear_items}</ul>

        {swot_html}

        <h2>Финансовое здоровье</h2>
        <p>Общий балл: <span class="score">{fh.get('score', 'Н/Д')}/10</span>
        &nbsp;&nbsp; Рост: {fh.get('growth_rating', 'Н/Д')}/10
        &nbsp;&nbsp; Рентабельность: {fh.get('profitability_rating', 'Н/Д')}/10
        &nbsp;&nbsp; Денежный поток: {fh.get('cashflow_rating', 'Н/Д')}/10</p>
        <p>{fh.get('comment', '')}</p>

        <h2>Справедливая стоимость</h2>
        <p>{fv.get('methodology', '')}</p>

        {'<h2>Сделки инсайдеров</h2><table><tr><th>Имя</th><th>Должность</th><th>Тип</th><th>Дата</th></tr>' + insider_rows + '</table>' if insiders else ''}

        <div class="footer">
            Данный отчёт сгенерирован искусственным интеллектом и предназначен только для информационных целей.
            Не является финансовой рекомендацией. Всегда проводите собственное исследование. &copy; StockAI
        </div>
    </body>
    </html>
    """

    return HTML(string=html_content).write_pdf()
