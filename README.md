<div align="center">

# ⚖️ LawgicHub

**AI-Powered Legal Analytics & Personalization Platform**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![PySpark](https://img.shields.io/badge/Apache_PySpark-MLlib-E25A1C?style=flat-square&logo=apachespark&logoColor=white)](https://spark.apache.org)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-00b880?style=flat-square)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Streamlit_Cloud-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://recomendation-system.streamlit.app)

<br/>

> *A full end-to-end big data pipeline that segments legal professionals by behavior, generates ALS-powered cross-service recommendations, and surfaces them in a production-grade Streamlit dashboard.*

<br/>

![LawgicHub Dashboard Preview](https://via.placeholder.com/900x420/07090f/00e5a0?text=LawgicHub+·+AI+Legal+Platform)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Live Demo](#-live-demo)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [User Segments](#-user-segments)
- [ML Pipeline](#-ml-pipeline)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Database Schema](#-database-schema)
- [Roadmap](#-roadmap)

---

## 🌐 Overview

LawgicHub is a **legal-tech analytics platform** built to understand how legal professionals interact with AI-powered legal services — and recommend the next best service for each user based on their behavior.

The system ingests raw user activity logs, runs a **PySpark ALS (Alternating Least Squares) collaborative filtering** model in Google Colab, clusters users into behavioral segments via **K-Means (k=3)**, and persists the enriched profiles to a **SQLite database** served by a polished Streamlit frontend.

It mirrors the architecture of platforms like **Amplitude**, **Mixpanel**, and **Segment** — but purpose-built for legal AI workflows.

```
Raw Activity Logs  →  PySpark Feature Engineering  →  ALS + K-Means  →  SQLite  →  Streamlit Dashboard
```

---

## 🚀 Live Demo

**[→ Open LawgicHub on Streamlit Cloud](https://recomendation-system.streamlit.app)**

- Click **⚡ Random User** in the sidebar to load a sample profile instantly
- Browse by **cluster** to explore all users in a segment
- Toggle **☀️ Light Mode** for a bright theme

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GOOGLE COLAB (Pipeline)                       │
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │  Raw Activity │ →  │   PySpark    │ →  │  ALS Collaborative   │   │
│  │     Logs      │    │  Feature Eng │    │  Filter (MLlib)      │   │
│  └──────────────┘    └──────────────┘    └──────────────────────┘   │
│                                                    │                  │
│                                          ┌─────────▼──────────┐     │
│                                          │  K-Means Clustering │     │
│                                          │  k=3, seed=42       │     │
│                                          └─────────────────────┘     │
└──────────────────────────────────────────────────│──────────────────┘
                                                   │ user_clusters.db
                                          ┌────────▼────────────────┐
                                          │     SQLite (WAL Mode)    │
                                          │  ┌─────────────────────┐ │
                                          │  │   user_clusters     │ │
                                          │  │   user_activity     │ │
                                          │  │  user_service_stats │ │
                                          │  └─────────────────────┘ │
                                          └────────────────────────┬─┘
                                                                   │
                                          ┌────────────────────────▼─┐
                                          │    Streamlit Frontend     │
                                          │  ┌──────────────────────┐ │
                                          │  │  My Workspace        │ │
                                          │  │  Analytics           │ │
                                          │  │  Data Explorer       │ │
                                          │  │  DB Inspector        │ │
                                          │  └──────────────────────┘ │
                                          └──────────────────────────┘
```

---

## ✨ Features

### 🏠 My Workspace (User Profile)
- **Hero card** — user segment badge, cluster label, display name, UUID, and last active timestamp
- **Real-time activity summary** — total actions, services used, discovery gaps, top service usage count, recent events
- **Service usage breakdown** — interactive Plotly bar chart + per-service progress bars with completion percentages
- **Profile gap analysis** — surfaces unused core services ranked by ALS-predicted fit
- **AI Recommendation cards** — Rec #1 and Rec #2 with fit score bars, algorithm source labels, and activation dialogs
- **Recommendation outreach** — pre-filled email campaign composer targeting each user's top gap service
- **Recommendation banner** — segment-aware CTA tailored to each cluster's behavior profile

### 📊 Analytics (Platform Overview)
- Cluster distribution donut chart (Plotly)
- Total completions by service (bar chart)
- Cross-recommendation frequency analysis
- Top 20 users by activity (sortable table)
- Service adoption heatmap by cluster
- Cluster summary table with dominant service and top recommendation per segment

### 🗃️ Data Explorer
- Full user table with cluster, service, recommendation, fit score, and source columns
- Multi-filter: cluster, service, free-text search (name or UUID)
- Toggle between human-readable labels and raw pipeline codes
- One-click CSV and JSON export

### 🛠️ DB Inspector
- SQLite PRAGMA diagnostics (WAL mode, cache size, mmap, synchronous)
- Table row counts and index inventory
- Live DB size, journal mode, and optimization status
- Performance index audit (checks for pipeline-created indexes)

### 🎨 UI/UX
- **Dual theme** — dark (deep navy) and light (slate white) with full CSS variable system
- **Space Mono** monospace + **Plus Jakarta Sans** sans-serif typography system
- Custom scrollbars, animated DB status dot, hover micro-animations
- Responsive card grid with colored left-border accents per cluster/service

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **ML Pipeline** | Apache PySpark (Google Colab) | Feature engineering, ALS, K-Means |
| **Recommendation** | MLlib ALS | Collaborative filtering |
| **Clustering** | MLlib K-Means (k=3, seed=42) | User segmentation |
| **Database** | SQLite (WAL mode) | Persistent storage, optimized indexes |
| **Backend** | Python 3.10+ | Data processing, query layer |
| **Frontend** | Streamlit 1.35+ | Interactive web UI |
| **Charts** | Plotly (Express + Graph Objects) | All data visualizations |
| **Data** | Pandas | Dataframe manipulation |
| **Deployment** | Streamlit Community Cloud | Hosted demo |

---

## 👥 User Segments

LawgicHub segments users into three behavioral clusters derived from service interaction patterns:

### ✍️ Cluster 0 — Heavy Draftsman
> *Power users of Application Drafting — high-frequency document creators*

Users in this cluster are prolific document authors. They file petitions, draft applications, and format submissions at high volume. Their discovery gap is typically **Legal Research** — they draft without deeply cross-referencing case law.

- **Primary service:** `APPLICATION_DRAFTING`
- **Top recommendation:** `RESEARCH`
- **Banner message:** "Boost your case preparation with case law validation"

---

### 🔬 Cluster 1 — Heavy Researcher
> *Deep legal research users — case laws, judgments, and court updates*

These users dive into legal databases, pull court judgments, and track precedents obsessively. Their gap is converting research into formatted documents — they have the analysis but not the output.

- **Primary service:** `RESEARCH`
- **Top recommendation:** `APPLICATION_DRAFTING`
- **Banner message:** "Turn your research into formatted petitions instantly"

---

### 💬 Cluster 2 — Query Analyst
> *Frequent Q&A users — legal definitions and quick lookups*

Lighter users who rely on quick answers and definitions. They're explorers rather than deep specialists. Recommendations surface the more powerful tools they haven't yet tried.

- **Primary service:** `QUERY_ANSWER`
- **Top recommendation:** `APPLICATION_DRAFTING` or `RESEARCH`
- **Banner message:** "Ready to go deeper? Turn quick answers into formal documents"

---

## 🤖 ML Pipeline

The pipeline runs in **Google Colab** using **PySpark MLlib**. Here's the end-to-end flow:

### Step 1 — Feature Engineering
```
Raw user_activity table  →  pivot by process_type  →  interaction matrix
```
Each user becomes a vector of interaction counts per service. Sparse entries are zero-filled.

### Step 2 — ALS Collaborative Filtering
```python
from pyspark.ml.recommendation import ALS

als = ALS(
    maxIter=10,
    regParam=0.1,
    userCol="user_index",
    itemCol="item_index",
    ratingCol="interaction_count",
    coldStartStrategy="drop",
    implicitPrefs=True,
)
model = als.fit(training_data)
```
Generates latent factor vectors for every user-service pair. Used to score "unvisited" services per user and rank cross-recommendations.

### Step 3 — K-Means Clustering
```python
from pyspark.ml.clustering import KMeans

kmeans = KMeans(k=3, seed=42, featuresCol="features")
model  = kmeans.fit(feature_df)
```
Groups users by their interaction profiles into 3 behavioral clusters. Cluster centroids determine segment labels.

### Step 4 — Enrichment & Persistence
Recommendation scores, cluster assignments, segment labels, and source tags (`als`, `peer`, `global`, `usage`) are written to `user_clusters.db` via SQLite with WAL mode and optimized indexes.

---

## 📁 Project Structure

```
lawgichub/
│
├── web_app/
│   └── app.py                  # Streamlit frontend (all 4 tabs)
│
├── colab/
│   └── als_pipeline.py         # PySpark ML pipeline (run in Colab)
│
├── data/
│   └── user_clusters.db        # SQLite output from pipeline
│
├── config/
│   └── services.json           # Optional: override service icons/labels/colors
│
├── requirements.txt            # Python dependencies
└── README.md
```

### `config/services.json` (optional)

Override service metadata without touching Python:
```json
{
  "core_services": ["APPLICATION_DRAFTING", "RESEARCH", "QUERY_ANSWER", "SYNOPSIS_GENERATION", "DOCUMENT_EMBEDDING"],
  "services": {
    "APPLICATION_DRAFTING": {
      "icon": "✍️",
      "label": "Application Drafting",
      "color": "var(--accent)",
      "pill": "pill-green"
    }
  }
}
```

---

## 🚦 Getting Started

### Prerequisites

- Python 3.10+
- `user_clusters.db` generated by the Colab pipeline (place in `data/`)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/lawgichub.git
cd lawgichub
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

**`requirements.txt`**
```
streamlit>=1.35.0
pandas>=2.0.0
plotly>=5.18.0
```

### 3. Generate the database

Open `colab/als_pipeline.py` in **Google Colab**, run all cells, and download the resulting `user_clusters.db`. Place it at:

```
data/user_clusters.db
```

### 4. Run the app

```bash
streamlit run web_app/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DB_PATH` | `data/user_clusters.db` | Override database path |

### Database Path Resolution

The app resolves `DB_PATH` relative to `app.py` using:

```python
_APP_DIR = Path(__file__).resolve().parent   # .../web_app/
_ROOT    = _APP_DIR.parent                   # repo root
DB_PATH  = _ROOT / "data" / "user_clusters.db"
```

This works correctly on local, Render, and Streamlit Cloud.

---

## 🌍 Deployment

### Streamlit Community Cloud

1. Push your repo to GitHub (make sure `data/user_clusters.db` is committed)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Set **Main file path** to `web_app/app.py`
4. Deploy

> ⚠️ Streamlit Cloud has a **read-only filesystem**. The app must not write to the DB at runtime. All ML writes happen in Colab, not in `app.py`.

### Render

Create a `render.yaml` at the repo root:

```yaml
services:
  - type: web
    name: lawgichub
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "streamlit run web_app/app.py --server.port $PORT --server.address 0.0.0.0"
```

> ⚠️ Do **not** paste Python code inside YAML values — colons (`:`) break YAML parsing.

---

## 🗄️ Database Schema

### `user_clusters`
| Column | Type | Description |
|---|---|---|
| `user_id` | TEXT | UUID primary key |
| `Name` | TEXT | Display name |
| `cluster_id` | INTEGER | K-Means cluster (0, 1, or 2) |
| `segment_name` | TEXT | Human-readable segment label |
| `active_service` | TEXT | Most-used service key |
| `active_service_name` | TEXT | Human-readable service label |
| `cross_recommend_1` | TEXT | Top recommended service key |
| `rec1_name` | TEXT | Rec #1 display name |
| `rec1_score` | REAL | ALS fit score (0–100) |
| `rec1_source` | TEXT | `als` / `peer` / `global` / `usage` |
| `cross_recommend_2` | TEXT | Second recommended service key |
| `rec2_name` | TEXT | Rec #2 display name |
| `rec2_score` | REAL | ALS fit score (0–100) |
| `rec2_source` | TEXT | Algorithm source tag |
| `last_active_at` | TEXT | ISO timestamp of last event |

### `user_activity`
| Column | Type | Description |
|---|---|---|
| `user_id` | TEXT | Foreign key → user_clusters |
| `process_type` | TEXT | Service key (e.g. `RESEARCH`) |
| `process_name` | TEXT | Human-readable process name |
| `status` | TEXT | Event status (e.g. `COMPLETED`) |
| `created_at` | TEXT | Event timestamp |

### `user_service_stats`
| Column | Type | Description |
|---|---|---|
| `user_id` | TEXT | Foreign key → user_clusters |
| `process_type` | TEXT | Service key |
| `interaction_count` | INTEGER | Total completions for this service |

### Indexes
```sql
CREATE INDEX idx_uc_uid  ON user_clusters(user_id);
CREATE INDEX idx_uc_cid  ON user_clusters(cluster_id);
CREATE INDEX idx_uc_svc  ON user_clusters(active_service);
CREATE INDEX idx_ua_uid  ON user_activity(user_id);
CREATE INDEX idx_ss_uid  ON user_service_stats(user_id);
```

---

## 🗺️ Roadmap

- [ ] **Real-time ALS scoring** — score new users on-the-fly without re-running Colab
- [ ] **Admin write panel** — trigger pipeline re-runs from the UI
- [ ] **User authentication** — JWT-gated personal workspace views
- [ ] **Email campaign integration** — connect outreach composer to SendGrid / Mailchimp
- [ ] **A/B recommendation testing** — track click-through on Rec #1 vs Rec #2
- [ ] **Temporal activity charts** — events over time per user and platform-wide
- [ ] **PostgreSQL migration** — swap SQLite for a production database
- [ ] **Multi-tenant support** — isolate data per law firm or organization

---

## 🧑‍💻 Author

**Sahil**
Legal-tech engineer · Data & ML · Full-stack Streamlit

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ⚖️ for the future of legal AI

**[Live Demo](https://recomendation-system.streamlit.app)** · **[Report a Bug](https://github.com/yourusername/lawgichub/issues)** · **[Request Feature](https://github.com/yourusername/lawgichub/issues)**

</div>