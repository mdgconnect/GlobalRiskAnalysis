
# Dealer & Financial Dashboard

An interactive Plotly Dash app for dealer-level analysis, car model analysis by fuel type, seasonal patterns, and fiscal KPIs.

## Files
- `dashboard_app.py` — main Dash app.
- `requirements.txt` — Python dependencies.
- **Place your data files** `data_desudo_france.csv` and `data_desudo_italy.csv` in the same folder before running.

## Quick Start
1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python dashboard_app.py
   ```
4. Open your browser at `http://127.0.0.1:8050`.

## Notes
- The app expects the CSVs to contain columns such as `contractstartdate`, `contractenddate`, `dealerbpid`, `modeldescription`, `fueltypecode`, `contract_status`, and `totalcapitalamount`.
- For production hosting (Azure App Service, Docker, etc.), the `server = app.server` line is included.
