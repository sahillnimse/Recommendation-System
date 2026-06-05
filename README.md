# LawgicHub Analytics

User segmentation and cross-service recommendations for the LawgicHub legal platform. Built with PySpark ALS (Colab) and a Streamlit dashboard.

## Quick start

### 1. Build the database (Google Colab)

1. Upload `colab/process_tracking_2026-06-02.csv` and `config/services.json` to Colab.
2. Run `colab/als_pipeline.py` cell-by-cell (or as a notebook).
3. Output is written to `data/user_clusters.db` (auto-download in Colab).

### 2. Run the dashboard (local)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
streamlit run web_app/app.py
```

Open http://localhost:8501

### Refresh labels & recommendations (existing DB)

```bash
python scripts/enrich_db.py
```

Adds display names, service labels, dual recommendations (Rec #1 / #2), and fills users with full profiles.

## Project layout

| Path | Purpose |
|------|---------|
| `config/services.json` | Core services, cluster mapping, ALS gap settings |
| `colab/als_pipeline.py` | Spark ALS pipeline → SQLite |
| `data/user_clusters.db` | `user_clusters`, `user_activity`, `user_service_stats` |
| `web_app/app.py` | Streamlit UI |

## Configuration

Edit `config/services.json` to add services or change cluster assignments. Re-run the Colab pipeline, then restart Streamlit (cached data TTL is 5 minutes).

## Production notes

- The DB Inspector SQL runner allows **read-only SELECT** queries only.
- User IDs and timestamps are HTML-escaped in the UI.
- Place `user_clusters.db` on persistent storage; point `DB_PATH` in `web_app/app.py` if needed.
- Do not commit `.env` files or production databases with PII.
