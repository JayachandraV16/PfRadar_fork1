"""
Monte Carlo long-only portfolios on the simplex for efficient frontier visualization.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from models.constants import TRADING_DAYS_PER_YEAR
from services.optimizer import portfolio_mu_sigma_from_daily


@dataclass
class RandomPortfolioCloud:
    """Annualized return and volatility for each random weight vector."""

    returns: np.ndarray  # shape (n_samples,)
    volatilities: np.ndarray
    weights: np.ndarray


def random_portfolio_cloud(
    mu_d: np.ndarray,
    cov_d: np.ndarray,
    *,
    n_samples: int,
    seed: int | None = 42,
) -> RandomPortfolioCloud:
    """
    Sample weights ~ Dirichlet(1,...,1), project to simplex (already), clip & renormalize.
    """
    if n_samples < 1:
        raise ValueError("n_samples must be positive")
    mu_d = np.asarray(mu_d, dtype=float)
    n = len(mu_d)
    rng = np.random.default_rng(seed)
    # Dirichlet with alpha=1 is uniform on simplex
    w = rng.dirichlet(np.ones(n), size=n_samples)
    rets = np.empty(n_samples)
    vols = np.empty(n_samples)
    for i in range(n_samples):
        wi = w[i].astype(float)
        wi = wi / wi.sum()
        mr, sv = portfolio_mu_sigma_from_daily(wi, mu_d, cov_d)
        rets[i] = mr
        vols[i] = sv
    return RandomPortfolioCloud(
        returns=rets,
        volatilities=vols,
        weights=w,
    )


def summarize_cloud(
    cloud: RandomPortfolioCloud,
) -> dict[str, float]:
    """Basic stats for JSON embedding (numeric values only)."""
    return {
        "n_samples": float(int(len(cloud.returns))),
        "return_p50": float(np.median(cloud.returns)),
        "volatility_p50": float(np.median(cloud.volatilities)),
    }


def get_target_risk_portfolio(returns: np.ndarray, cov_matrix: np.ndarray, risk_level: float, risk_free_rate: float = 0.07) -> np.ndarray:
    """
    Interpolate along the efficient frontier based on risk_level [0, 1].
    0 -> min variance portfolio
    1 -> max Sharpe portfolio
    """
    from services.optimizer import min_variance_weights, max_sharpe_weights

    # Clip risk level to [0, 1]
    risk_level = float(np.clip(risk_level, 0.0, 1.0))

    # Compute bounds of the frontier
    min_var_weights = min_variance_weights(cov_matrix)
    max_sharpe_w = max_sharpe_weights(returns, cov_matrix, risk_free_rate)

    # Convex combination
    weights = (1.0 - risk_level) * min_var_weights + risk_level * max_sharpe_w

    # Normalize weights to ensure they sum to exactly 1
    weights = np.clip(weights, 0.0, 1.0)
    weights = weights / weights.sum()

    return weights


def annualized_stats_for_weights(
    weights: np.ndarray,
    mu_d: np.ndarray,
    cov_d: np.ndarray,
) -> tuple[float, float]:
    """
    Returns (annualized_return, annualized_volatility) for a given weight vector.
    Uses the same path as the frontier cloud so all points are comparable.
    """
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    ann_ret, ann_vol = portfolio_mu_sigma_from_daily(w, mu_d, cov_d)
    return float(ann_ret), float(ann_vol)

__all__ = ["RandomPortfolioCloud", "random_portfolio_cloud", "summarize_cloud", "get_target_risk_portfolio","annualized_stats_for_weights"]
