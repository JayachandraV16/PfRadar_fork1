"""
Assemble end-to-end portfolio analytics into a JSON-ready payload.
"""

from __future__ import annotations

import logging
from pathlib import Path
from tracemalloc import start
from typing import Any

from services.capm import capm_expected_returns
import numpy as np
from models.constants import DEFAULT_RISK_FREE_ANNUAL_IN, TRADING_DAYS_PER_YEAR
from models.schemas import FullPortfolioReport
from services.frontier import random_portfolio_cloud, summarize_cloud
from services.market_data import fetch_aligned_prices, fetch_market_returns, normalize_indian_tickers
from services.optimizer import (
    max_sharpe_weights,
    min_variance_weights,
    portfolio_mu_sigma_from_daily,
)
from utils.returns import annualized_return_from_daily_mean, cagr_from_price_series, daily_returns_from_prices
from utils.risk import estimate_daily_mu_cov
from utils.visualization import plot_efficient_frontier_cloud

logger = logging.getLogger(__name__)


def _weights_dict(symbols: list[str], w: np.ndarray) -> dict[str, float]:
    w = np.asarray(w, dtype=float).ravel()
    return {s: float(round(wi, 8)) for s, wi in zip(symbols, w, strict=True)}


def _equal_weights(n: int) -> np.ndarray:
    return np.ones(n, dtype=float) / n

from services.frontier import random_portfolio_cloud, summarize_cloud, get_target_risk_portfolio

def build_full_report(
    tickers: list[str],
    *,
    target_weights: dict[str, float] | None = None,
    start: str | None = None,
    end: str | None = None,
    risk_free_annual: float | None = None,
    random_portfolios: int = 2500,
    ridge_epsilon: float = 1e-10,
    plot_path: str | Path | None = None,
    random_seed: int = 42,
    min_history_trading_days: int = 60,
    risk_score: float | None = None,
    chart_period: str = "12M",
) -> dict[str, Any]:

    rf = float(DEFAULT_RISK_FREE_ANNUAL_IN if risk_free_annual is None else risk_free_annual)

    if risk_score is not None:
        risk_score = float(np.clip(risk_score, 0.0, 1.0))

    if target_weights:
        merged: dict[str, float] = {}
        for k, v in target_weights.items():
            nk = normalize_indian_tickers([k])[0]
            merged[nk] = merged.get(nk, 0.0) + float(v)
        target_weights = merged

    prices, symbols = fetch_aligned_prices(
        tickers,
        start=start,
        end=end,
        min_history_trading_days=min_history_trading_days,
    )

    rets = daily_returns_from_prices(prices, how="any")

    # 🔹 Estimate historical mu and covariance
    mu_d, cov_d, used_syms = estimate_daily_mu_cov(
        rets, ridge_epsilon=ridge_epsilon
    )

    # ===================== CAPM BLOCK =====================

    from services.capm import capm_expected_returns
    from services.market_data import fetch_market_returns

    # Ensure correct column ordering
    rets = rets[used_syms]

    # Historical expected returns
    mu_hist = mu_d.copy()

    # Fetch market returns
    market_returns = fetch_market_returns(start, end)

    # CAPM expected returns
    mu_capm = capm_expected_returns(
        rets,
        market_returns,
        rf_annual=rf,
    )

    # 50-50 blend
    alpha = 0.5
    mu_d = alpha * mu_hist + (1 - alpha) * mu_capm

    # ======================================================



    n = len(used_syms)

    user_weights_raw = None
    user_weights_normalized = None

    if target_weights is None:
        w_ref = _equal_weights(n)
        ref_label = "equal_weight"
    else:
        w_raw = np.array([target_weights[s] for s in used_syms], dtype=float)
        user_weights_raw = _weights_dict(used_syms, w_raw)
        
        w_ref = w_raw.copy()
        if not np.isclose(w_ref.sum(), 1.0, atol=1e-6):
            logger.info("Normalizing user weights to sum to 1.0 for metrics comparison.")
            if w_ref.sum() > 1e-12:
                w_ref = w_ref / w_ref.sum()
            elif len(w_ref) > 0 and (w_ref < -1e-9).any():
                 raise ValueError("target_weights must be non-negative (long-only)")
        if (w_ref < -1e-9).any():
            raise ValueError("target_weights must be non-negative (long-only)")
        
        user_weights_normalized = _weights_dict(used_syms, w_ref)
        ref_label = "user"

    mu_ann_ref, sig_ann_ref = portfolio_mu_sigma_from_daily(w_ref, mu_d, cov_d)

    sharpe_ref = (
        float((mu_ann_ref - rf) / sig_ann_ref)
        if sig_ann_ref > 1e-12
        else float("nan")
    )

    if not np.isfinite(sharpe_ref):
        sharpe_ref = 0.0

    w_mv = min_variance_weights(cov_d)
    w_ms = max_sharpe_weights(mu_d, cov_d, rf)

    cloud = random_portfolio_cloud(
        mu_d, cov_d, n_samples=random_portfolios, seed=random_seed
    )
    frontier_stats = summarize_cloud(cloud)

    # ================= USER RISK PORTFOLIO =================

    w_target_risk = None
    mu_target_risk = None
    sig_target_risk = None

    mu_mv, sig_mv = portfolio_mu_sigma_from_daily(w_mv, mu_d, cov_d)
    mu_ms, sig_ms = portfolio_mu_sigma_from_daily(w_ms, mu_d, cov_d)    

    if risk_score is not None:
        risk_score = float(np.clip(risk_score, 0.0, 1.0))
        w_target_risk = get_target_risk_portfolio(mu_d, cov_d, risk_score, risk_free_rate=rf)
        mu_target_risk, sig_target_risk = portfolio_mu_sigma_from_daily(w_target_risk, mu_d, cov_d)

    if plot_path:
        plot_efficient_frontier_cloud(
            cloud.volatilities,
            cloud.returns,
            min_var_point=(float(sig_mv), float(mu_mv)),
            max_sharpe_point=(float(sig_ms), float(mu_ms)),
            path=plot_path,
        )

    cov_list = np.asarray(cov_d, dtype=float).tolist()

    cagr_map: dict[str, float | None] = {}
    ann_mean_map: dict[str, float] = {}

    for sym in used_syms:
        cagr_v, _years = cagr_from_price_series(prices[sym])
        cagr_map[sym] = cagr_v if np.isfinite(cagr_v) else None

        md = float(rets[sym].mean())
        ann_mean_map[sym] = annualized_return_from_daily_mean(md)

    import pandas as pd
    from utils.returns import portfolio_daily_returns

    # Map chart_period string to a DateOffset
    _period_map = {
        "1M": pd.DateOffset(months=1),
        "3M": pd.DateOffset(months=3),
        "6M": pd.DateOffset(months=6),
        "12M": pd.DateOffset(years=1),
    }
    chart_offset = _period_map.get(chart_period, pd.DateOffset(years=1))

    last_date = rets.index[-1]
    start_chart = last_date - chart_offset
    
    mask_chart = rets.index >= start_chart
    rets_period = rets.loc[mask_chart]
    
    user_returns_period = portfolio_daily_returns(rets_period, w_ref, symbols_order=list(used_syms))
    
    opt_w = w_target_risk if risk_score is not None else w_ms
    opt_returns_period = portfolio_daily_returns(rets_period, opt_w, symbols_order=list(used_syms))

    market_returns_period = market_returns.loc[market_returns.index.isin(rets_period.index)]
    market_returns_aligned = market_returns_period.reindex(rets_period.index).fillna(0.0)

    cum_user = (1 + user_returns_period).cumprod() - 1
    cum_opt = (1 + opt_returns_period).cumprod() - 1
    cum_bench = (1 + market_returns_aligned).cumprod() - 1

    # Period-specific total returns (last value of cumulative series)
    period_return_user = float(cum_user.iloc[-1]) if len(cum_user) > 0 else None
    period_return_optimal = float(cum_opt.iloc[-1]) if len(cum_opt) > 0 else None
    period_return_benchmark = float(cum_bench.iloc[-1]) if len(cum_bench) > 0 else None

    # Period-specific volatility (annualized from the period's daily returns)
    period_vol_user = float(user_returns_period.std() * np.sqrt(TRADING_DAYS_PER_YEAR)) if len(user_returns_period) > 1 else None
    period_vol_optimal = float(opt_returns_period.std() * np.sqrt(TRADING_DAYS_PER_YEAR)) if len(opt_returns_period) > 1 else None

    historical_chart_data = {
        "dates": [d.strftime("%Y-%m-%d") for d in rets_period.index],
        "user_portfolio": [float(x) for x in cum_user],
        "optimal_portfolio": [float(x) for x in cum_opt],
        "benchmark_nifty50": [float(x) for x in cum_bench],
        "assets": {sym: [float(x) for x in ((1 + rets_period[sym]).cumprod() - 1)] for sym in used_syms},
        "period": chart_period,
        "period_return_user": period_return_user,
        "period_return_optimal": period_return_optimal,
        "period_return_benchmark": period_return_benchmark,
        "period_volatility_user": period_vol_user,
        "period_volatility_optimal": period_vol_optimal,
    }

    # ================= PORTFOLIO-LEVEL CAGR =================
    # Use the full price history to compute portfolio-level CAGR
    full_rets = rets[list(used_syms)]
    user_daily_full = portfolio_daily_returns(full_rets, w_ref, symbols_order=list(used_syms))
    opt_daily_full = portfolio_daily_returns(full_rets, opt_w, symbols_order=list(used_syms))

    # Build cumulative growth factor series (like a price series starting at 1.0)
    user_growth = (1 + user_daily_full).cumprod()
    opt_growth = (1 + opt_daily_full).cumprod()

    def _portfolio_cagr(growth_series: pd.Series) -> float | None:
        """CAGR from a cumulative growth-factor series (starts ~1.0)."""
        s = growth_series.dropna()
        if len(s) < 2:
            return None
        p0, p1 = float(s.iloc[0]), float(s.iloc[-1])
        if p0 <= 0 or p1 <= 0:
            return None
        days = (s.index[-1] - s.index[0]).days
        years = days / 365.25
        if years <= 0:
            return None
        return float((p1 / p0) ** (1.0 / years) - 1.0)

    user_cagr = _portfolio_cagr(user_growth)
    opt_cagr = _portfolio_cagr(opt_growth)

    # =============== EFFICIENT FRONTIER DATA ================
    # Package the Monte-Carlo cloud + key portfolio points for the frontend chart
    efficient_frontier_data = {
        "cloud_volatilities": [float(v) for v in cloud.volatilities],
        "cloud_returns": [float(r) for r in cloud.returns],
        "user_portfolio": {"volatility": float(sig_ann_ref), "return": float(mu_ann_ref)},
        "optimal_portfolio": {
            "volatility": float(sig_target_risk) if risk_score is not None else float(sig_ms),
            "return": float(mu_target_risk) if risk_score is not None else float(mu_ms),
        },
        "min_variance": {"volatility": float(sig_mv), "return": float(mu_mv)},
        "max_sharpe": {"volatility": float(sig_ms), "return": float(mu_ms)},
    }

    report = FullPortfolioReport(
        expected_return=float(mu_ann_ref),
        volatility=float(sig_ann_ref),
        sharpe_ratio=float(sharpe_ref),
        optimal_weights=_weights_dict(used_syms, w_ms),
        covariance_matrix=cov_list,
        symbols=list(used_syms),
        reference_portfolio=ref_label,
        min_variance_weights=_weights_dict(used_syms, w_mv),
        max_sharpe_weights=_weights_dict(used_syms, w_ms),
        user_weights_raw=user_weights_raw,
        user_weights_normalized=user_weights_normalized,
        target_risk_portfolio=_weights_dict(used_syms, w_target_risk) if risk_score is not None else None,
        target_risk_expected_return=float(mu_target_risk) if risk_score is not None else None,
        target_risk_volatility=float(sig_target_risk) if risk_score is not None else None,
        user_risk_score=risk_score,
        risk_free_annual=rf,
        trading_days_per_year=TRADING_DAYS_PER_YEAR,
        cagr_by_symbol=cagr_map,
        annualized_mean_return_by_symbol=ann_mean_map,
        frontier_random_stats=frontier_stats,
        historical_chart_data=historical_chart_data,
        user_portfolio_cagr=user_cagr,
        optimal_portfolio_cagr=opt_cagr,
        efficient_frontier_data=efficient_frontier_data,
        meta={
            "price_rows": int(len(prices)),
            "return_rows": int(len(rets)),
            "max_sharpe_annual_return": float(mu_ms),
            "max_sharpe_annual_volatility": float(sig_ms),
            "min_variance_annual_return": float(mu_mv),
            "min_variance_annual_volatility": float(sig_mv),
        },
    )

    report_dict = report.to_json_dict()
    # Final portfolio weights being used
    final_weights = (
            report_dict["target_risk_portfolio"]
            if report_dict["target_risk_portfolio"] is not None
            else report_dict["optimal_weights"]
        )

        # Asset allocation = actual portfolio weights
    report_dict["asset_allocation"] = final_weights

        # ---------- INDIVIDUAL STOCK VOLATILITY ----------

    individual_risk = (
            rets[used_syms].std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
        )

    report_dict["risk_weightage"] = {
            sym: float(round(individual_risk[sym], 2))
            for sym in used_syms
        }
    return report_dict