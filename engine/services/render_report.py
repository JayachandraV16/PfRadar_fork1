def build_all_rows(report_data):
    weights = report_data.get("asset_allocation", {})
    user_weights = report_data.get("user_weights_normalized", {})
    tickers = list(weights.keys())

    # ================= HOLDINGS =================
    holdings_rows = ""
    for t in tickers:
        w = weights[t]

        holdings_rows += f"""
        <tr>
            <td>{t}</td>
            <td>{t}</td>
            <td>{w*100:.2f}%</td>
            <td>—</td>
            <td>—</td>
            <td>—</td>
            <td>—</td>
        </tr>
        """

    # ================= SECTOR =================
    sector_rows = ""
    sectors = report_data.get("sector_exposure", {})

    for s, val in sectors.items():
        sector_rows += f"""
        <tr>
            <td>{s}</td>
            <td>{val*100:.2f}%</td>
        </tr>
        """

    # ================= STOCK DETAILS =================
    stock_rows = ""
    for t in tickers:
        stock_rows += f"""
        <tr>
            <td>{t}</td>
            <td>—</td>
            <td>—</td>
            <td>—</td>
            <td>{weights[t]*100:.2f}%</td>
        </tr>
        """

    # ================= ALLOCATION =================
    allocation_rows = ""
    for t in tickers:
        cur = user_weights.get(t, 0)
        opt = weights.get(t, 0)
        delta = opt - cur

        cls = "good" if delta > 0 else "bad"

        allocation_rows += f"""
        <tr>
            <td>{t}</td>
            <td>{cur*100:.2f}%</td>
            <td>{opt*100:.2f}%</td>
            <td class="{cls}">{delta*100:+.2f}%</td>
        </tr>
        """

    return holdings_rows, sector_rows, stock_rows, allocation_rows