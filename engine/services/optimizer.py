"""
Long-only Markowitz-style optimization using scipy.optimize (SLSQP).

- Minimum variance
- Maximum Sharpe (annualized excess return / annualized volatility)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from scipy.optimize import minimize

from models.constants import DEFAULT_RISK_FREE_ANNUAL_IN, TRADING_DAYS_PER_YEAR
from models.exceptions import OptimizationFailedError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Annualized portfolio statistics

def _annualized_portfolio_mean(mu_d: np.ndarray, w: np.ndarray) -> float:
    """
    Compound annualized return:
        (1 + daily_mean)^252 - 1
    """
    mu_p = float(mu_d @ w)
    td = float(TRADING_DAYS_PER_YEAR)
    return float((1.0 + mu_p) ** td - 1.0)


def _annualized_portfolio_std(cov_d: np.ndarray, w: np.ndarray) -> float:
    """
    Annualized portfolio volatility.
    """
    var_d = float(w @ cov_d @ w)

    # Numerical stabilization
    if var_d < 0 and var_d > -1e-14:
        var_d = 0.0

    if var_d < 0:
        raise OptimizationFailedError("Negative portfolio variance")

    sigma_d = float(np.sqrt(var_d))

    return float(sigma_d * np.sqrt(float(TRADING_DAYS_PER_YEAR)))


def portfolio_mu_sigma_from_daily(
    weights: np.ndarray,
    mu_d: np.ndarray,
    cov_d: np.ndarray,
) -> tuple[float, float]:
    """
    Returns:
        (annualized_return, annualized_volatility)
    """
    w = np.asarray(weights, dtype=float)

    return (
        _annualized_portfolio_mean(mu_d, w),
        _annualized_portfolio_std(cov_d, w),
    )


# Weight normalization

def _normalize_weights(w: np.ndarray) -> np.ndarray:
    """
    Normalize weights safely.
    """
    s = w.sum()

    if s <= 1e-12:
        raise OptimizationFailedError("Weights collapsed to zero")

    return w / s


# Minimum Variance Portfolio

def min_variance_weights(
    cov_d: np.ndarray,
    *,
    x0: np.ndarray | None = None,
) -> np.ndarray:
    """
    Minimize:
        w^T Σ w

    Subject to:
        sum(w) = 1
        0 <= w <= 0.4
    """

    cov_d = np.asarray(cov_d, dtype=float)

    n = cov_d.shape[0]

    if cov_d.shape != (n, n):
        raise ValueError("cov_d must be square")

    def objective(w: np.ndarray) -> float:
        return float(w @ cov_d @ w)

    constraints = (
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
    )

    max_weight = 0.4

    bounds = tuple((0.0, max_weight) for _ in range(n))

    candidates: list[np.ndarray] = []

    if x0 is not None:
        candidates.append(np.asarray(x0, dtype=float))

    # Equal weight start
    candidates.append(np.ones(n) / n)

    # One-hot starts
    for i in range(n):
        e = np.zeros(n)
        e[i] = 1.0
        candidates.append(e)

    best_x: np.ndarray | None = None
    best_obj = float("inf")
    best_msg = ""

    ok_any = False

    for w0 in candidates:

        res = minimize(
            objective,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={
                "maxiter": 1000,
                "ftol": 1e-10,
                "disp": False,
            },
        )

        if res.x is None:
            continue

        x = _normalize_weights(np.asarray(res.x, dtype=float))

        obj = objective(x)

        if obj < best_obj:
            best_obj = obj
            best_x = x
            best_msg = res.message
            ok_any = ok_any or res.success

    if best_x is None:
        raise OptimizationFailedError(
            "Min variance optimization failed"
        )

    if not ok_any:
        logger.warning(
            "min_variance: optimizer warning: %s",
            best_msg,
        )

    return best_x


# Maximum Sharpe Portfolio

def max_sharpe_weights(
    mu_d: np.ndarray,
    cov_d: np.ndarray,
    risk_free_annual: float | None = None,
    *,
    x0: np.ndarray | None = None,
) -> np.ndarray:
    """
    Maximize Sharpe ratio:

        (mu_ann - rf) / sigma_ann

    Subject to:
        sum(w) = 1
        0 <= w <= 0.4
    """

    rf = float(
        DEFAULT_RISK_FREE_ANNUAL_IN
        if risk_free_annual is None
        else risk_free_annual
    )

    mu_d = np.asarray(mu_d, dtype=float)
    cov_d = np.asarray(cov_d, dtype=float)

    n = len(mu_d)

    # Mild shrinkage toward cross-sectional mean
    mu_mean = np.mean(mu_d)

    alpha = 0.8

    mu_d = alpha * mu_d + (1.0 - alpha) * mu_mean

    def neg_sharpe(w: np.ndarray) -> float:

        try:
            mu_ann, sig_ann = portfolio_mu_sigma_from_daily(
                w,
                mu_d,
                cov_d,
            )

            # Prevent divide-by-zero
            if sig_ann <= 1e-10:
                return 1e6

            sharpe = (mu_ann - rf) / sig_ann

            if not np.isfinite(sharpe):
                return 1e6

            return -float(sharpe)

        except Exception:
            return 1e6

    # Initial guess
    w0 = (
        np.ones(n) / n
        if x0 is None
        else np.asarray(x0, dtype=float)
    )

    constraints = (
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
    )

    max_weight = 0.4

    bounds = tuple((0.0, max_weight) for _ in range(n))

    res = minimize(
        neg_sharpe,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={
            "maxiter": 1500,
            "ftol": 1e-9,
            "disp": False,
        },
    )

    # Fallback instead of crashing API
    if not res.success:

        logger.warning(
            "max_sharpe optimization warning: %s",
            res.message,
        )

        return np.ones(n) / n

    w = np.asarray(res.x, dtype=float)

    return _normalize_weights(w)