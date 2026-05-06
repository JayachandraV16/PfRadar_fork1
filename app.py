import json
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime
import yfinance as yf
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

from engine.services.report import build_full_report

app = FastAPI()
templates = Jinja2Templates(directory="templates")
sector_cache = {}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_table_rows(report_data, sector_map):
    weights = report_data.get("asset_allocation", {})
    user_weights = report_data.get("user_weights_normalized", {})

    holdings_rows = ""
    allocation_rows = ""

    for ticker, weight in weights.items():
        sector = sector_map.get(ticker, "Other")
        # Holdings table
        holdings_rows += f"""
        <tr>
            <td>{ticker.replace('.NS', '')}</td>
            <td>{ticker}</td>
            <td>{sector}</td>
            <td>{weight * 100:.2f}%</td>
        </tr>
        """

        # Allocation comparison table
        cur = user_weights.get(ticker, 0)
        opt = weight
        delta = opt - cur

        delta_class = "good" if delta > 0 else "bad"

        allocation_rows += f"""
        <tr>
            <td>{ticker}</td>
            <td>{cur * 100:.2f}%</td>
            <td>{opt * 100:.2f}%</td>
            <td class="{delta_class}">{delta * 100:+.2f}%</td>
        </tr>
        """

    return holdings_rows, allocation_rows

# Get stocks by sector
def get_sector_map(tickers):
    sector_map = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            sector = info.get("sector", "Other")

            if not sector:
                sector = "Other"

            sector_map[ticker] = sector
            if ticker in sector_cache:
                sector_map[ticker] = sector_cache[ticker]
                continue
        except Exception:
            sector_map[ticker] = "Other"

    return sector_map

@app.get("/api/report")
def get_report(tickers: str, weights: str, risk: float | None = None, period: str = "12M"):
    try:
        t_list = [t.strip() for t in tickers.split(",") if t.strip()]
        w_list = [float(w.strip()) for w in weights.split(",") if w.strip()]

        if len(t_list) != len(w_list):
            raise HTTPException(status_code=400, detail="Number of tickers must match weights")

        target_weights = dict(zip(t_list, w_list))

        report_data = build_full_report(
            tickers=t_list,
            target_weights=target_weights,
            risk_score=risk,
            chart_period=period,
        )

        return report_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sector")
def get_sector(ticker: str):

    try:
        stock = yf.Ticker(ticker)

        info = stock.info

        return {
            "ticker": ticker,
            "sector": info.get("sector", "Other")
        }

    except Exception:
        return {
            "ticker": ticker,
            "sector": "Other"
        }

@app.get("/api/download_report")
def download_report(
    tickers: str,
    weights: str,
    risk: float | None = None,
    period: str = "12M"
):
    try:
        t_list = [t.strip() for t in tickers.split(",") if t.strip()]
        w_list = [float(w.strip()) for w in weights.split(",") if w.strip()]

        if len(t_list) != len(w_list):
            raise HTTPException(status_code=400, detail="Mismatch in inputs")

        target_weights = dict(zip(t_list, w_list))

        report_data = build_full_report(
            tickers=t_list,
            target_weights=target_weights,
            risk_score=risk,
            chart_period=period,
        )
        sector_map = get_sector_map(t_list)
        holdings_rows, allocation_rows = build_table_rows(report_data, sector_map)

        cagr = round(report_data["optimal_portfolio_cagr"] * 100, 2)
        vol = round(report_data["target_risk_volatility"] * 100, 2)
        sharpe = round(report_data["sharpe_ratio"], 2)
        # ================= SCORE =================

        score = 50

        # CAGR contribution
        if cagr >= 15:
            score += 20
        elif cagr >= 10:
            score += 10

        # Sharpe contribution
        if sharpe >= 1.5:
            score += 20
        elif sharpe >= 1:
            score += 10

        # Volatility adjustment
        if vol <= 15:
            score += 10
        elif vol >= 25:
            score -= 10

        score = max(0, min(100, score))

        # ================= CAGR STATUS =================

        if cagr >= 15:
            cagr_status = "Excellent"
            cagr_badge = "good"
        elif cagr >= 10:
            cagr_status = "Good"
            cagr_badge = "warn"
        else:
            cagr_status = "Weak"
            cagr_badge = "bad"

        # ================= VOL STATUS =================

        if vol <= 15:
            vol_status = "Low Risk"
            vol_badge = "good"
        elif vol <= 22:
            vol_status = "Moderate"
            vol_badge = "warn"
        else:
            vol_status = "High Risk"
            vol_badge = "bad"

        # ================= SHARPE STATUS =================

        if sharpe >= 1.5:
            sharpe_status = "Excellent"
            sharpe_badge = "good"
        elif sharpe >= 1:
            sharpe_status = "Acceptable"
            sharpe_badge = "warn"
        else:
            sharpe_status = "Poor"
            sharpe_badge = "bad"

        # ================= COMMENTS =================

        if score >= 80:
            return_comment = "Strong long-term return potential"
        elif score >= 60:
            return_comment = "Moderate growth outlook"
        else:
            return_comment = "Limited growth potential"

        if vol <= 15:
            risk_comment = "Portfolio risk is well controlled"
        elif vol <= 22:
            risk_comment = "Portfolio carries moderate risk"
        else:
            risk_comment = "Portfolio risk is elevated"

        if vol > 25:
            suggestion_1 = "Reduce exposure to high volatility assets."
        else:
            suggestion_1 = "Portfolio volatility is under control."

        if sharpe < 1:
            suggestion_2 = "Improve risk-adjusted returns through diversification."
        else:
            suggestion_2 = "Risk-adjusted returns are healthy."

        if cagr < 10:
            suggestion_3 = "Consider adding higher growth assets."
        else:
            suggestion_3 = "Current growth allocation appears balanced."

        portfolio_summary = (
            f"Portfolio targets {cagr}% CAGR "
            f"with {vol}% volatility "
            f"and Sharpe ratio of {sharpe}."
        )

        html = templates.get_template("report_template.html").render(

        USER_NAME="Investor",
        DATE=datetime.today().strftime("%d %b %Y"),
        PERIOD=period,
        STOCK_COUNT=len(t_list),

        HEALTH_SCORE=score,

        RETURN_COMMENT=return_comment,
        RISK_COMMENT=risk_comment,
        PORTFOLIO_SUMMARY=portfolio_summary,
        CAGR=cagr,
        VOL=vol,
        SHARPE=sharpe,

        CAGR_STATUS=cagr_status,
        VOL_STATUS=vol_status,
        SHARPE_STATUS=sharpe_status,

        CAGR_BADGE=cagr_badge,
        VOL_BADGE=vol_badge,
        SHARPE_BADGE=sharpe_badge,

        SUGGESTION_1=suggestion_1,
        SUGGESTION_2=suggestion_2,
        SUGGESTION_3=suggestion_3,

        ALLOCATION_TEXT=", ".join(
            [
                f"{k}: {round(v * 100, 2)}%"
                for k, v in report_data["asset_allocation"].items()
            ]
        ),

        HOLDINGS_ROWS=holdings_rows,
        ALLOCATION_ROWS=allocation_rows
        )

        pdf_buffer = BytesIO()

        pisa.CreatePDF(html, dest=pdf_buffer)

        pdf_buffer.seek(0)

        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=Portfolio_Report.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
app.mount("/", StaticFiles(directory=".", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)