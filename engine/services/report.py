"""
Assemble end-to-end portfolio analytics into a JSON-ready payload.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from models.constants import DEFAULT_RISK_FREE_ANNUAL_IN, TRADING_DAYS_PER_YEAR
from models.schemas import FullPortfolioReport
from services.capm import capm_expected_returns
from services.frontier import (
    get_target_risk_portfolio,
    random_portfolio_cloud,
    summarize_cloud,
)
from services.market_data import (
    fetch_aligned_prices,
    fetch_market_returns,
    normalize_indian_tickers,
)
from services.optimizer import (
    max_sharpe_weights,
    min_variance_weights,
    portfolio_mu_sigma_from_daily,
)
from utils.returns import (
    annualized_return_from_daily_mean,
    cagr_from_price_series,
    daily_returns_from_prices,
    portfolio_daily_returns,
)
from utils.risk import estimate_daily_mu_cov
from utils.visualization import plot_efficient_frontier_cloud

logger = logging.getLogger(__name__)

_MAX_ANNUAL_RETURN = 0.40
_MIN_ANNUAL_RETURN = -0.30


def _weights_dict(symbols: list[str], w: np.ndarray) -> dict[str, float]:
    w = np.asarray(w, dtype=float).ravel()
    return {s: float(round(wi, 8)) for s, wi in zip(symbols, w, strict=True)}


def _equal_weights(n: int) -> np.ndarray:
    return np.ones(n, dtype=float) / n


def _annualized_stats(
    w: np.ndarray, mu_d: np.ndarray, cov_d: np.ndarray
) -> tuple[float, float]:
    """Annualized (return, volatility) via portfolio_mu_sigma_from_daily."""
    w = np.asarray(w, dtype=float)
    w = w / w.sum()
    ann_ret, ann_vol = portfolio_mu_sigma_from_daily(w, mu_d, cov_d)
    return float(ann_ret), float(ann_vol)


def _realized_annualized_stats(
    w: np.ndarray,
    rets: pd.DataFrame,
    symbols_order: list[str],
) -> tuple[float, float]:
    """
    Compute realized annualized return and volatility from actual daily returns.

    - Annualized return  = (1 + daily_mean)^252 - 1  (compound)
    - Annualized vol     = daily_std * sqrt(252)

    This is what the metric cards and performance charts reflect, so using
    this for frontier key-points keeps everything consistent.
    """
    w = np.asarray(w, dtype=float)
    w = w / w.sum()
    port_daily = portfolio_daily_returns(rets, w, symbols_order=symbols_order)
    ann_ret = float((1 + port_daily.mean()) ** TRADING_DAYS_PER_YEAR - 1)
    ann_vol = float(port_daily.std() * np.sqrt(TRADING_DAYS_PER_YEAR))
    return ann_ret, ann_vol


def _portfolio_cagr(growth_series: pd.Series) -> float | None:
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


def _clamp_daily_mu(mu_d: np.ndarray) -> np.ndarray:
    T = TRADING_DAYS_PER_YEAR
    annual = (1.0 + mu_d) ** T - 1.0
    annual_clamped = np.clip(annual, _MIN_ANNUAL_RETURN, _MAX_ANNUAL_RETURN)
    return (1.0 + annual_clamped) ** (1.0 / T) - 1.0


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

    #  Market data 
    prices, symbols = fetch_aligned_prices(
        tickers, start=start, end=end,
        min_history_trading_days=min_history_trading_days,
    )
    rets = daily_returns_from_prices(prices, how="any")

    #  Historical mu / covariance 
    mu_d, cov_d, used_syms = estimate_daily_mu_cov(rets, ridge_epsilon=ridge_epsilon)
    rets = rets[used_syms]

    #  CAPM blend → clamp 
    mu_hist = mu_d.copy()
    market_returns = fetch_market_returns(start, end)
    mu_capm = capm_expected_returns(rets, market_returns, rf_annual=rf)
    mu_d = _clamp_daily_mu(0.5 * mu_hist + 0.5 * mu_capm)

    #  User weights 
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
            if w_ref.sum() > 1e-12:
                w_ref = w_ref / w_ref.sum()
        if (w_ref < -1e-9).any():
            raise ValueError("target_weights must be non-negative (long-only)")
        user_weights_normalized = _weights_dict(used_syms, w_ref)
        ref_label = "user"

    #  Key weight vectors 
    w_mv = min_variance_weights(cov_d)
    w_ms = max_sharpe_weights(mu_d, cov_d, rf)

    w_target_risk: np.ndarray | None = None
    if risk_score is not None:
        w_target_risk = get_target_risk_portfolio(mu_d, cov_d, risk_score, risk_free_rate=rf)

    opt_w = w_target_risk if w_target_risk is not None else w_ms

    #  Optimizer-based stats (for Sharpe, report schema fields) 
    mu_ann_ref, sig_ann_ref = _annualized_stats(w_ref, mu_d, cov_d)
    mu_mv_opt,  sig_mv_opt  = _annualized_stats(w_mv,  mu_d, cov_d)
    mu_ms_opt,  sig_ms_opt  = _annualized_stats(w_ms,  mu_d, cov_d)
    mu_opt_fwd, sig_opt_fwd = _annualized_stats(opt_w, mu_d, cov_d)

    #  Realized stats from FULL history 
    # These are computed from actual daily return history — the same source as
    # the performance charts and metric cards — so frontier key-points and
    # metric card values are guaranteed to be in the same coordinate space.
    syms_list = list(used_syms)
    mu_ref_real,  sig_ref_real  = _realized_annualized_stats(w_ref,  rets, syms_list)
    mu_mv_real,   sig_mv_real   = _realized_annualized_stats(w_mv,   rets, syms_list)
    mu_ms_real,   sig_ms_real   = _realized_annualized_stats(w_ms,   rets, syms_list)
    mu_opt_real,  sig_opt_real  = _realized_annualized_stats(opt_w,  rets, syms_list)

    realized_sharpe = (
    float((mu_ref_real - rf) / sig_ref_real)
    if sig_ref_real > 1e-12
    else 0.0
    )
    #  Monte-Carlo cloud — also realized from actual return history 
    # We build it directly from realized daily returns so that cloud points,
    # key-points, and metric cards all live in the same coordinate space.
    #
    # Strategy: draw Dirichlet weights, compute realized annualized return
    # and vol for each sample from actual rets data.
    rng = np.random.default_rng(random_seed)
    cloud_w = rng.dirichlet(np.ones(n), size=random_portfolios)
    cloud_rets_arr  = np.empty(random_portfolios)
    cloud_vols_arr  = np.empty(random_portfolios)
    rets_matrix = rets[syms_list].values  # shape (T, n)

    for i in range(random_portfolios):
        wi = cloud_w[i]
        port = rets_matrix @ wi                              # daily portfolio returns
        cloud_rets_arr[i] = (1 + port.mean()) ** TRADING_DAYS_PER_YEAR - 1
        cloud_vols_arr[i] = port.std() * np.sqrt(TRADING_DAYS_PER_YEAR)

    # Also generate the mu_d-based cloud for optimizer usage (Sharpe etc.)
    cloud = random_portfolio_cloud(mu_d, cov_d, n_samples=random_portfolios, seed=random_seed)
    frontier_stats = summarize_cloud(cloud)

    if plot_path:
        plot_efficient_frontier_cloud(
            cloud.volatilities, cloud.returns,
            min_var_point=(float(sig_mv_opt), float(mu_mv_opt)),
            max_sharpe_point=(float(sig_ms_opt), float(mu_ms_opt)),
            path=plot_path,
        )

    #  Per-symbol analytics 
    cagr_map: dict[str, float | None] = {}
    ann_mean_map: dict[str, float] = {}
    for sym in used_syms:
        cagr_v, _ = cagr_from_price_series(prices[sym])
        cagr_map[sym] = cagr_v if np.isfinite(cagr_v) else None
        ann_mean_map[sym] = annualized_return_from_daily_mean(float(rets[sym].mean()))

    #  Period chart data 
    _period_map = {
        "1M":  pd.DateOffset(months=1),
        "3M":  pd.DateOffset(months=3),
        "6M":  pd.DateOffset(months=6),
        "12M": pd.DateOffset(years=1),
    }
    chart_offset = _period_map.get(chart_period, pd.DateOffset(years=1))
    rets_period  = rets.loc[rets.index >= rets.index[-1] - chart_offset]

    user_returns_period = portfolio_daily_returns(rets_period, w_ref,  symbols_order=syms_list)
    opt_returns_period  = portfolio_daily_returns(rets_period, opt_w,  symbols_order=syms_list)
    market_returns_period = (
        market_returns
        .loc[market_returns.index.isin(rets_period.index)]
        .reindex(rets_period.index)
        .fillna(0.0)
    )

    cum_user  = (1 + user_returns_period).cumprod() - 1
    cum_opt   = (1 + opt_returns_period).cumprod() - 1
    cum_bench = (1 + market_returns_period).cumprod() - 1

    period_return_user      = float(cum_user.iloc[-1])  if len(cum_user)  > 0 else None
    period_return_optimal   = float(cum_opt.iloc[-1])   if len(cum_opt)   > 0 else None
    period_return_benchmark = float(cum_bench.iloc[-1]) if len(cum_bench) > 0 else None
    period_vol_user         = float(user_returns_period.std() * np.sqrt(TRADING_DAYS_PER_YEAR)) if len(user_returns_period) > 1 else None
    period_vol_optimal      = float(opt_returns_period.std()  * np.sqrt(TRADING_DAYS_PER_YEAR)) if len(opt_returns_period)  > 1 else None

    historical_chart_data = {
        "dates":                     [d.strftime("%Y-%m-%d") for d in rets_period.index],
        "user_portfolio":            [float(x) for x in cum_user],
        "optimal_portfolio":         [float(x) for x in cum_opt],
        "benchmark_nifty50":         [float(x) for x in cum_bench],
        "assets": {
            sym: [float(x) for x in ((1 + rets_period[sym]).cumprod() - 1)]
            for sym in used_syms
        },
        "period":                    chart_period,
        "period_return_user":        period_return_user,
        "period_return_optimal":     period_return_optimal,
        "period_return_benchmark":   period_return_benchmark,
        "period_volatility_user":    period_vol_user,
        "period_volatility_optimal": period_vol_optimal,
    }

    #  Portfolio-level CAGR (full history) 
    full_rets       = rets[syms_list]
    user_daily_full = portfolio_daily_returns(full_rets, w_ref, symbols_order=syms_list)
    opt_daily_full  = portfolio_daily_returns(full_rets, opt_w, symbols_order=syms_list)
    user_cagr = _portfolio_cagr((1 + user_daily_full).cumprod())
    opt_cagr  = _portfolio_cagr((1 + opt_daily_full).cumprod())

    #  Efficient frontier data 
    # Cloud AND key points all use REALIZED returns from actual rets history.
    # This is the same source as the metric cards (period_return_*) and CAGR
    # cards, so the numbers users see on the chart match what they read in the
    # metric cards. No more forward-looking vs realized mismatch.
    efficient_frontier_data = {
        "cloud_volatilities": [float(v) for v in cloud_vols_arr],
        "cloud_returns":      [float(r) for r in cloud_rets_arr],
        "user_portfolio":     {"volatility": sig_ref_real,  "return": mu_ref_real},
        "optimal_portfolio":  {"volatility": sig_opt_real,  "return": mu_opt_real},
        "min_variance":       {"volatility": sig_mv_real,   "return": mu_mv_real},
        "max_sharpe":         {"volatility": sig_ms_real,   "return": mu_ms_real},
    }

    cov_list = np.asarray(cov_d, dtype=float).tolist()
    
    realized_sharpe = (
    float((mu_ref_real - rf) / sig_ref_real)
    if sig_ref_real > 1e-12
    else 0.0
)
    report = FullPortfolioReport(
        expected_return=float(mu_ref_real),
        volatility=float(sig_ref_real),
        sharpe_ratio=float(realized_sharpe),
        optimal_weights=_weights_dict(used_syms, w_ms),
        covariance_matrix=cov_list,
        symbols=syms_list,
        reference_portfolio=ref_label,
        min_variance_weights=_weights_dict(used_syms, w_mv),
        max_sharpe_weights=_weights_dict(used_syms, w_ms),
        user_weights_raw=user_weights_raw,
        user_weights_normalized=user_weights_normalized,
        target_risk_portfolio=(
            _weights_dict(used_syms, w_target_risk) if w_target_risk is not None else None
        ),
        target_risk_expected_return=float(mu_opt_real) if w_target_risk is not None else None,
        target_risk_volatility=float(sig_opt_real)     if w_target_risk is not None else None,
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
            "price_rows":                     int(len(prices)),
            "return_rows":                    int(len(rets)),
            "max_sharpe_annual_return":       float(mu_ms_opt),
            "max_sharpe_annual_volatility":   float(sig_ms_opt),
            "min_variance_annual_return":     float(mu_mv_opt),
            "min_variance_annual_volatility": float(sig_mv_opt),
        },
    )

    report_dict = report.to_json_dict()

    final_weights = (
        report_dict["target_risk_portfolio"]
        if report_dict["target_risk_portfolio"] is not None
        else report_dict["optimal_weights"]
    )
    report_dict["asset_allocation"] = final_weights

    individual_risk = rets[used_syms].std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
    report_dict["risk_weightage"] = {
        sym: float(round(individual_risk[sym], 2)) for sym in used_syms
    }

    return report_dict