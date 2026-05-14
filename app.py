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
from sector_map import get_sector as _get_sector_from_map 

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#  Sector lookup 

def get_sector_for_ticker(ticker: str) -> str:
    """
    Resolve sector for a single ticker.

    Resolution order (defined in sector_map.py):
      1. Hardcoded map  — instant, covers ~300 common NSE tickers
      2. Session cache  — previous live lookup this process lifetime
      3. yfinance live  — network call, result is cached automatically
      4. Fallback       — "Other"
    """
    return _get_sector_from_map(ticker)


#  Report helpers 

def build_table_rows(report_data, sector_map):
    weights = report_data.get("asset_allocation", {})
    user_weights = report_data.get("user_weights_normalized", {})

    holdings_rows = ""
    allocation_rows = ""

    for ticker, weight in weights.items():
        sector = sector_map.get(ticker, "Other")

        holdings_rows += f"""
        <tr>
            <td>{ticker.replace('.NS', '')}</td>
            <td>{ticker}</td>
            <td>{sector}</td>
            <td>{weight * 100:.2f}%</td>
        </tr>
        """

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


def get_sector_map(tickers: list[str]) -> dict[str, str]:
    """
    Return a {ticker: sector} dict for a list of tickers.
    Uses the same fast resolution order (hardcoded → cache → live).
    """
    return {t: get_sector_for_ticker(t) for t in tickers}


#  API routes 

@app.get("/api/report")
def api_report(tickers: str, weights: str, risk: float | None = None, period: str = "12M"):
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
def api_sector(ticker: str):
    """
    Returns the sector for a single ticker.
    Hits the hardcoded map first — no network round-trip for known tickers.
    """
    try:
        sector = get_sector_for_ticker(ticker)
        return {"ticker": ticker, "sector": sector}
    except Exception:
        return {"ticker": ticker, "sector": "Other"}


@app.get("/api/download_report")
def download_report(
    tickers: str,
    weights: str,
    risk: float | None = None,
    period: str = "12M",
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

        # Sector map — fast because most tickers are hardcoded
        sector_map = get_sector_map(t_list)
        holdings_rows, allocation_rows = build_table_rows(report_data, sector_map)

        cagr   = round(report_data["optimal_portfolio_cagr"] * 100, 2)
        vol_source = (
        report_data["target_risk_volatility"]
        if report_data["target_risk_volatility"] is not None
        else report_data["volatility"]
        )   
        vol = round(vol_source * 100, 2)
        sharpe = round(report_data["sharpe_ratio"], 2)

        #  Health score 
        score = 50
        if cagr >= 15:   score += 20
        elif cagr >= 10: score += 10
        if sharpe >= 1.5:   score += 20
        elif sharpe >= 1:   score += 10
        if vol <= 15:    score += 10
        elif vol >= 25:  score -= 10
        score = max(0, min(100, score))

        #  CAGR status 
        if cagr >= 15:   cagr_status, cagr_badge = "Excellent", "good"
        elif cagr >= 10: cagr_status, cagr_badge = "Good",      "warn"
        else:            cagr_status, cagr_badge = "Weak",       "bad"

        #  Volatility status 
        if vol <= 15:    vol_status, vol_badge = "Low Risk",  "good"
        elif vol <= 22:  vol_status, vol_badge = "Moderate",  "warn"
        else:            vol_status, vol_badge = "High Risk",  "bad"

        #  Sharpe status 
        if sharpe >= 1.5:   sharpe_status, sharpe_badge = "Excellent",  "good"
        elif sharpe >= 1:   sharpe_status, sharpe_badge = "Acceptable", "warn"
        else:               sharpe_status, sharpe_badge = "Poor",       "bad"

        #  Narrative comments 
        return_comment  = ("Strong long-term return potential"  if score >= 80 else
                           "Moderate growth outlook"            if score >= 60 else
                           "Limited growth potential")
        risk_comment    = ("Portfolio risk is well controlled"  if vol <= 15 else
                           "Portfolio carries moderate risk"    if vol <= 22 else
                           "Portfolio risk is elevated")
        suggestion_1    = ("Reduce exposure to high volatility assets." if vol > 25 else
                           "Portfolio volatility is under control.")
        suggestion_2    = ("Improve risk-adjusted returns through diversification." if sharpe < 1 else
                           "Risk-adjusted returns are healthy.")
        suggestion_3    = ("Consider adding higher growth assets." if cagr < 10 else
                           "Current growth allocation appears balanced.")
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
                f"{k}: {round(v * 100, 2)}%"
                for k, v in report_data["asset_allocation"].items()
            ),
            HOLDINGS_ROWS=holdings_rows,
            ALLOCATION_ROWS=allocation_rows,
        )

        pdf_buffer = BytesIO()
        pisa.CreatePDF(html, dest=pdf_buffer)
        pdf_buffer.seek(0)

        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Portfolio_Report.pdf"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)