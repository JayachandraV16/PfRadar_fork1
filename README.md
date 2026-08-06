# PfRadar

Portfolio analytics and optimization project focused on Indian equities (NSE/BSE).
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Deployment](https://img.shields.io/badge/Deployed-Vercel-black)
## Tech stack

- Python
- pandas, numpy, scipy
- yfinance
- matplotlib
- pydantic
- pytest

## Folder structure

```text
PfRadar/
├─ README.md
├─ .gitignore
└─ engine/
   ├─ README.md
   ├─ requirements.txt
   ├─ main.py
   ├─ pytest.ini
   ├─ conftest.py
   ├─ data/
   │  └─ .gitkeep
   ├─ models/
   │  ├─ __init__.py
   │  ├─ constants.py
   │  ├─ exceptions.py
   │  └─ schemas.py
   ├─ services/
   │  ├─ __init__.py
   │  ├─ market_data.py
   │  ├─ optimizer.py
   │  ├─ frontier.py
   │  ├─ report.py
   │  └─ capm.py
   ├─ utils/
   │  ├─ __init__.py
   │  ├─ logging_config.py
   │  ├─ returns.py
   │  ├─ risk.py
   │  └─ visualization.py
   └─ tests/
      ├─ __init__.py
      ├─ test_returns.py
      ├─ test_risk.py
      ├─ test_optimizer.py
      └─ test_integration_nse.py
```

## Quick start

```bash
cd engine
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py demo RELIANCE.NS TCS.NS INFY.NS --plot frontier.png
```

## Testing

```bash
cd engine
pytest -m "not integration"
pytest -m integration
```

For engine-specific details, see [`engine/README.md`](engine/README.md).
