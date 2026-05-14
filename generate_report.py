import json
import os
import sys

# Add engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

from engine.services.report import build_full_report

print(" Generating demo report...")

try:
    report_data = build_full_report(
        tickers=['RELIANCE.NS', 'TCS.NS', 'INFY.NS'],
        target_weights={'RELIANCE.NS': 0.4, 'TCS.NS': 0.3, 'INFY.NS': 0.3}
    )
    
    with open('report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
        
    print("Successfully generated report.json")
except Exception as e:
    print(f"Error generating report: {e}")
