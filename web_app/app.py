import json
import re
import sys
from html import escape as html_escape
from textwrap import dedent
import random
import sqlite3
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="LawgicHub · AI Legal Platform",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# THEME STATE & SIDEBAR SELECTOR
# ══════════════════════════════════════════════════════════════════════════════
if "is_light" not in st.session_state:
    st.session_state["is_light"] = False

# We define variables based on theme
theme = "light" if st.session_state["is_light"] else "dark"

if theme == "light":
    bg = "#f8fafc"
    bg2 = "#ffffff"
    bg3 = "#f1f5f9"
    border = "#cbd5e1"
    hover_border = "#94a3b8"
    text = "#0f172a"
    muted = "#64748b"
    accent = "#00b880"
    accent_gradient = "#009f6b"
    btn_text = "#ffffff"
    accent2 = "#6366f1"
    accent3 = "#d97706"
    danger = "#e11d48"
    info = "#0284c7"
    plotly_bg = "#ffffff"
    plotly_grid = "#f1f5f9"
    accent_rgb = "0, 184, 128"
    accent2_rgb = "99, 102, 241"
    accent3_rgb = "217, 119, 6"
    danger_rgb = "225, 29, 72"
    info_rgb = "2, 132, 199"
else:
    bg = "#07090f"
    bg2 = "#0f1117"
    bg3 = "#161a24"
    border = "#1f2535"
    hover_border = "#2e3650"
    text = "#e8eaf0"
    muted = "#6b7280"
    accent = "#00e5a0"
    accent_gradient = "#00c285"
    btn_text = "#07090f"
    accent2 = "#7c6fef"
    accent3 = "#f7b731"
    danger = "#ff4d6d"
    info = "#38bdf8"
    plotly_bg = "#0f1117"
    plotly_grid = "#1a1e2a"
    accent_rgb = "0, 229, 160"
    accent2_rgb = "124, 111, 239"
    accent3_rgb = "247, 183, 49"
    danger_rgb = "255, 77, 109"
    info_rgb = "56, 189, 248"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

:root {{
    --bg: {bg}; 
    --bg2: {bg2}; 
    --bg3: {bg3}; 
    --border: {border};
    --hover-border: {hover_border};
    --accent: {accent}; 
    --accent-gradient: {accent_gradient};
    --btn-text: {btn_text};
    --accent2: {accent2}; 
    --accent3: {accent3};
    --danger: {danger}; 
    --info: {info}; 
    --text: {text}; 
    --muted: {muted};
    --accent-rgb: {accent_rgb};
    --accent2-rgb: {accent2_rgb};
    --accent3-rgb: {accent3_rgb};
    --danger-rgb: {danger_rgb};
    --info-rgb: {info_rgb};
    --mono: 'Space Mono', monospace; 
    --sans: 'Plus Jakarta Sans', sans-serif;
}}

html, body, [class*="css"] {{
    font-family: var(--sans);
    background: var(--bg);
    color: var(--text);
}}

.stApp {{
    background: var(--bg);
}}

/* Custom Scrollbars */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: var(--bg);
}}
::-webkit-scrollbar-thumb {{
    background: var(--border);
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: var(--muted);
}}

/* Sidebar Customization */
[data-testid="stSidebar"] {{
    background: var(--bg2) !important;
    border-right: 1px solid var(--border);
}}
[data-testid="stSidebar"] * {{
    color: var(--text) !important;
}}

/* Form elements labels and paragraphs */
.stMarkdown p, label, [data-testid="stWidgetLabel"] p, .stCheckbox * {{
    color: var(--text) !important;
}}

/* Inputs, Selectboxes, Textareas styling */
.stTextInput>div>div>input, .stTextArea textarea {{
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 13px !important;
    padding: 10px 14px !important;
    transition: all 0.2s ease !important;
}}
.stTextInput>div>div>input:focus, .stTextArea textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.12) !important;
    outline: none !important;
}}

[data-testid="stSelectbox"]>div>div {{
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    transition: all 0.2s ease-in-out !important;
}}
[data-testid="stSelectbox"]>div>div:focus-within {{
    border-color: var(--accent) !important;
}}

/* Selectbox inner elements and text color */
[data-testid="stSelectbox"] * {{
    color: var(--text) !important;
}}

/* MultiSelect elements color */
[data-testid="stMultiSelect"] * {{
    color: var(--text) !important;
}}

/* Baseweb Popovers & Dropdowns (used by selectboxes and multiselects) */
[data-baseweb="popover"], [data-baseweb="menu"], [id*="bui"] {{
    background-color: var(--bg2) !important;
    border: 1px solid var(--border) !important;
}}
[data-baseweb="popover"] *, [data-baseweb="menu"] *, [id*="bui"] * {{
    color: var(--text) !important;
    background-color: transparent !important;
}}
/* Hover effect on dropdown menu items */
[role="option"]:hover, li[role="option"]:hover, [data-baseweb="menu"] li:hover {{
    background-color: var(--bg3) !important;
    color: var(--accent) !important;
}}

/* Custom Tabs Styling */
div[data-testid="stTabs"] {{
    background: transparent !important;
}}
div[data-testid="stTabs"] button {{
    font-family: var(--sans) !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--muted) !important;
    border: none !important;
    background-color: transparent !important;
    padding: 12px 24px !important;
    transition: all 0.2s ease !important;
}}
div[data-testid="stTabs"] button:hover {{
    color: var(--text) !important;
    background-color: rgba(var(--accent-rgb), 0.04) !important;
}}
div[data-testid="stTabs"] button[aria-selected="true"] {{
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}}

/* Buttons Styling: Primary & Secondary Custom overrides */
.stButton>button[kind="primary"], button[data-testid*="primary"] {{
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-gradient) 100%) !important;
    color: var(--btn-text) !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: var(--mono) !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
    width: 100% !important;
    box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.15) !important;
}}
.stButton>button[kind="primary"]:hover, button[data-testid*="primary"]:hover {{
    opacity: 0.95 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(var(--accent-rgb), 0.3) !important;
}}
.stButton>button[kind="primary"]:active, button[data-testid*="primary"]:active {{
    transform: translateY(1px) !important;
}}

.stButton>button[kind="secondary"], button[data-testid*="secondary"], .stButton>button:not([kind="primary"]), .stDownloadButton>button, div[data-testid="stFormSubmitButton"]>button {{
    background: var(--bg3) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--mono) !important;
    font-weight: 500 !important;
    font-size: 12px !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
    width: 100% !important;
    box-shadow: none !important;
}}
.stButton>button[kind="secondary"]:hover, button[data-testid*="secondary"]:hover, .stButton>button:not([kind="primary"]):hover, .stDownloadButton>button:hover, div[data-testid="stFormSubmitButton"]>button:hover {{
    background: var(--border) !important;
    border-color: var(--muted) !important;
    color: var(--accent) !important;
    transform: translateY(-1px) !important;
}}

/* Cards & Layout */
.card {{
    background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
    transition: border-color 0.25s, box-shadow 0.25s, transform 0.25s;
}}
.card:hover {{
    border-color: var(--hover-border);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
}}
.card-green  {{ border-left: 4px solid var(--accent) !important; }}
.card-purple {{ border-left: 4px solid var(--accent2) !important; }}
.card-yellow {{ border-left: 4px solid var(--accent3) !important; }}
.card-red    {{ border-left: 4px solid var(--danger) !important; }}
.card-blue   {{ border-left: 4px solid var(--info) !important; }}

.pill {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: var(--mono);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
}}
.pill-green  {{ background: rgba(var(--accent-rgb), 0.1); color: var(--accent); border: 1px solid rgba(var(--accent-rgb), 0.25); }}
.pill-purple {{ background: rgba(var(--accent2-rgb), 0.1); color: var(--accent2); border: 1px solid rgba(var(--accent2-rgb), 0.25); }}
.pill-yellow {{ background: rgba(var(--accent3-rgb), 0.1); color: var(--accent3); border: 1px solid rgba(var(--accent3-rgb), 0.25); }}
.pill-red    {{ background: rgba(var(--danger-rgb), 0.1); color: var(--danger); border: 1px solid rgba(var(--danger-rgb), 0.25); }}
.pill-blue   {{ background: rgba(var(--info-rgb), 0.1); color: var(--info); border: 1px solid rgba(var(--info-rgb), 0.25); }}

.sec-head {{
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin: 28px 0 14px;
}}

/* Metric boxes */
.mbox {{
    background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
    transition: border-color 0.2s, transform 0.2s;
}}
.mbox:hover {{
    border-color: var(--hover-border);
    transform: translateY(-2px);
}}
.mbox .num {{
    font-size: 28px;
    font-weight: 700;
    font-family: var(--mono);
}}
.mbox .lbl {{
    font-size: 10px;
    color: var(--muted);
    font-family: var(--mono);
    letter-spacing: .08em;
    margin-top: 2px;
}}

.empty-state {{
    background: var(--bg2);
    border: 1px dashed var(--border);
    border-radius: 16px;
    padding: 64px 48px;
    text-align: center;
    color: var(--muted);
    font-family: var(--sans);
    font-size: 14px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}}

.cluster-hero {{
    background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 32px;
    display: flex;
    gap: 28px;
    align-items: center;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
}}

.uid {{
    font-family: var(--mono);
    font-size: 12px;
    color: var(--accent);
    word-break: break-all;
}}

.stat-row {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin: 14px 0;
}}
.stat-chip {{
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 18px;
    flex: 1;
    min-width: 120px;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
    transition: border-color 0.2s, transform 0.2s;
}}
.stat-chip:hover {{
    border-color: var(--hover-border);
    transform: translateY(-1px);
}}
.stat-chip .s-val {{
    font-size: 22px;
    font-weight: 700;
    font-family: var(--mono);
}}
.stat-chip .s-lbl {{
    font-size: 10px;
    color: var(--muted);
    font-family: var(--mono);
    letter-spacing: .08em;
    margin-top: 2px;
}}

.activity-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
    transition: background-color 0.2s;
}}
.activity-row:hover {{
    background-color: rgba(255, 255, 255, 0.02);
}}
.activity-row:last-child {{
    border-bottom: none;
}}

.banner {{
    border-radius: 14px;
    padding: 24px 28px;
    margin-top: 24px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s;
}}
.banner:hover {{
    transform: translateY(-2px);
}}
.banner-green  {{ background: linear-gradient(135deg, rgba(var(--accent-rgb), 0.12), rgba(var(--accent-rgb), 0.03)); border: 1px solid rgba(var(--accent-rgb), 0.25); }}
.banner-purple {{ background: linear-gradient(135deg, rgba(var(--accent2-rgb), 0.12), rgba(var(--accent2-rgb), 0.03)); border: 1px solid rgba(var(--accent2-rgb), 0.25); }}

.search-wrap {{ background: var(--bg3); border: 1px solid rgba(var(--accent2-rgb), 0.3); border-radius: 12px; padding: 20px 24px; margin: 10px 0; }}
.qa-wrap     {{ background: var(--bg3); border: 1px solid rgba(var(--accent3-rgb), 0.3); border-radius: 12px; padding: 20px 24px; }}

.logo {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: var(--sans);
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text);
    background: linear-gradient(135deg, var(--text) 0%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 28px;
}}

.db-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(var(--accent-rgb), 0.07);
    border: 1px solid rgba(var(--accent-rgb), 0.18);
    border-radius: 6px;
    padding: 6px 12px;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--accent);
}}
.db-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse 2s infinite;
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 1; box-shadow: 0 0 0 0 rgba(0, 229, 160, 0.4); }}
    50% {{ opacity: .3; box-shadow: 0 0 0 4px rgba(0, 229, 160, 0); }}
}}

.js-plotly-plot {{
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
}}

#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container {{ padding-top: 24px !important; max-width: 1240px; }}

.gap-card {{
    opacity: .8;
    border: 1px dashed var(--border) !important;
    background: var(--bg3) !important;
}}
.gap-pill {{
    background: rgba(107, 114, 128, 0.12);
    color: var(--muted);
    border: 1px solid var(--border);
}}
.fit-bar {{
    height: 6px;
    background: var(--bg3);
    border-radius: 4px;
    margin-top: 10px;
    overflow: hidden;
}}
.fit-fill {{
    height: 100%;
    border-radius: 4px;
}}

/* HTML Table Styling (for st.table) */
table {{
    width: 100% !important;
    border-collapse: collapse !important;
    background-color: var(--bg2) !important;
    color: var(--text) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
    margin: 10px 0 !important;
}}
th {{
    background-color: var(--bg3) !important;
    color: var(--accent) !important;
    font-family: var(--mono) !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 12px 16px !important;
    text-align: left !important;
    border-bottom: 2px solid var(--border) !important;
}}
td {{
    padding: 12px 16px !important;
    font-size: 13px !important;
    border-bottom: 1px solid var(--border) !important;
    color: var(--text) !important;
}}
tr:hover td {{
    background-color: rgba(var(--accent-rgb), 0.03) !important;
}}
tr:last-child td {{
    border-bottom: none !important;
}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════
DB_PATH = Path(__file__).parent.parent / "data" / "user_clusters.db"
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

def h(text):
    """Escape user-controlled strings before embedding in HTML."""
    return html_escape(str(text)) if text is not None else ""

def is_safe_select(sql):
    """Allow only a single read-only SELECT or WITH statement (no writes or multi-statements)."""
    if not sql or not sql.strip():
        return False
    cleaned = re.sub(r"--[^\n]*", "", sql)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip().rstrip(";")
    if ";" in cleaned:
        return False
    lower = cleaned.lower()
    blocked_pattern = re.compile(
        r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|grant|revoke)\b",
        re.IGNORECASE
    )
    if blocked_pattern.search(lower):
        return False
    return lower.startswith("select") or lower.startswith("with")

def _optimize(conn):
    for stmt in [
        "PRAGMA journal_mode=WAL", "PRAGMA synchronous=NORMAL",
        "PRAGMA cache_size=-32000", "PRAGMA temp_store=MEMORY",
        "PRAGMA mmap_size=134217728", "PRAGMA optimize",
        "CREATE INDEX IF NOT EXISTS idx_uc_uid  ON user_clusters(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_uc_cid  ON user_clusters(cluster_id)",
        "CREATE INDEX IF NOT EXISTS idx_uc_svc  ON user_clusters(active_service)",
        "CREATE INDEX IF NOT EXISTS idx_ua_uid  ON user_activity(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_ss_uid  ON user_service_stats(user_id)",
    ]:
        try: conn.cursor().execute(stmt)
        except Exception: pass
    conn.commit()

@st.cache_resource(show_spinner=False)
def get_conn():
    if not DB_PATH.exists():
        st.error(f"⚠️ Database not found at `{DB_PATH}`. Run `als_pipeline.py` first.")
        st.stop()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _optimize(conn)
    return conn

@st.cache_resource(show_spinner=False)
def get_readonly_conn():
    if not DB_PATH.exists():
        st.error(f"⚠️ Database not found at `{DB_PATH}`. Run `als_pipeline.py` first.")
        st.stop()
    # Connect using read-only URI mode for additional protection
    conn = sqlite3.connect(f"file:{str(DB_PATH)}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def query_user(uid):
    try:
        return get_conn().execute(
            "SELECT * FROM user_clusters WHERE user_id=?", (uid.strip(),)
        ).fetchone()
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def query_user_service_stats(uid):
    """Per-service interaction counts for one user — real data from pipeline."""
    try:
        return pd.read_sql(
            "SELECT process_type, interaction_count FROM user_service_stats "
            "WHERE user_id=? ORDER BY interaction_count DESC",
            get_conn(), params=(uid,)
        )
    except Exception:
        return pd.DataFrame(columns=["process_type","interaction_count"])

@st.cache_data(ttl=300, show_spinner=False)
def query_user_activity(uid, limit=20):
    """Recent COMPLETED events for one user — real data from pipeline."""
    try:
        return pd.read_sql(
            "SELECT * FROM user_activity WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
            get_conn(), params=(uid, limit)
        )
    except Exception:
        return pd.DataFrame(columns=["process_type", "status"])

@st.cache_data(ttl=300, show_spinner=False)
def query_users_by_cluster(cid):
    try:
        rows = get_conn().execute(
            "SELECT user_id, Name FROM user_clusters WHERE cluster_id=? ORDER BY user_id", (int(cid),)
        ).fetchall()
        return [(r[0], r[1]) for r in rows]
    except Exception:
        try:
            # Fallback if Name column doesn't exist
            rows = get_conn().execute(
                "SELECT user_id FROM user_clusters WHERE cluster_id=? ORDER BY user_id", (int(cid),)
            ).fetchall()
            return [(r[0], None) for r in rows]
        except Exception:
            return []

@st.cache_data(ttl=300, show_spinner=False)
def load_all():
    return pd.read_sql("SELECT * FROM user_clusters", get_conn())

@st.cache_data(ttl=300, show_spinner=False)
def cluster_dist():
    return pd.read_sql(
        "SELECT cluster_id, COUNT(*) AS users FROM user_clusters "
        "GROUP BY cluster_id ORDER BY cluster_id", get_conn()
    )

@st.cache_data(ttl=300, show_spinner=False)
def platform_stats():
    """Aggregate stats across all users — like a Mixpanel overview."""
    conn = get_conn()
    try:
        total_events = conn.execute("SELECT COUNT(*) FROM user_activity").fetchone()[0]
    except Exception:
        total_events = 0
    try:
        svc_dist = pd.read_sql(
            "SELECT process_type, SUM(interaction_count) AS total "
            "FROM user_service_stats GROUP BY process_type ORDER BY total DESC",
            conn
        )
    except Exception:
        svc_dist = pd.DataFrame(columns=["process_type","total"])
    try:
        top_users = pd.read_sql(
            "SELECT uc.user_id, uc.Name, uc.cluster_id, uc.active_service, "
            "SUM(ss.interaction_count) AS total_actions "
            "FROM user_clusters uc "
            "JOIN user_service_stats ss ON uc.user_id = ss.user_id "
            "GROUP BY uc.user_id ORDER BY total_actions DESC LIMIT 20",
            conn
        )
    except Exception:
        top_users = pd.DataFrame()
    return {"total_events": total_events, "svc_dist": svc_dist, "top_users": top_users}

@st.cache_data(ttl=300, show_spinner=False)
def rec_frequency():
    return pd.read_sql("""
        SELECT cross_recommend_1 AS service, COUNT(*) AS freq
        FROM user_clusters
        WHERE cross_recommend_1 IS NOT NULL
        GROUP BY cross_recommend_1
        ORDER BY freq DESC
    """, get_conn())

@st.cache_data(ttl=300, show_spinner=False)
def service_by_cluster():
    return pd.read_sql("""
        SELECT cluster_id, active_service, COUNT(*) AS cnt
        FROM user_clusters WHERE active_service IS NOT NULL
        GROUP BY cluster_id, active_service
    """, get_conn())

@st.cache_data(ttl=300, show_spinner=False)
def rec_coverage_pct():
    try:
        conn = get_conn()
        total = conn.execute("SELECT COUNT(*) FROM user_clusters").fetchone()[0]
        if not total:
            return 0
        covered = conn.execute(
            "SELECT COUNT(*) FROM user_clusters "
            "WHERE cross_recommend_1 IS NOT NULL AND TRIM(cross_recommend_1) != ''"
        ).fetchone()[0]
        return round(100 * covered / total)
    except Exception:
        return 0

@st.cache_data(ttl=600, show_spinner=False)
def db_stats():
    conn    = get_conn()
    cur     = conn.cursor()
    total   = cur.execute("SELECT COUNT(*) FROM user_clusters").fetchone()[0]
    page_sz = cur.execute("PRAGMA page_size").fetchone()[0]
    pages   = cur.execute("PRAGMA page_count").fetchone()[0]
    wal     = cur.execute("PRAGMA journal_mode").fetchone()[0].upper()
    indexes = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()]
    tables  = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    return {"total":total,"size_kb":round(page_sz*pages/1024),"wal":wal,"indexes":indexes,"tables":tables}


# ══════════════════════════════════════════════════════════════════════════════
# METADATA (UI clusters + shared service config)
# ══════════════════════════════════════════════════════════════════════════════
_CONFIG_PATH = Path(__file__).parent.parent / "config" / "services.json"

@st.cache_data(show_spinner=False)
def load_service_config():
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON in `{_CONFIG_PATH.name}`: {exc}")
            st.stop()
    return {
        "core_services": [
            "APPLICATION_DRAFTING", "RESEARCH", "QUERY_ANSWER",
            "SYNOPSIS_GENERATION", "DOCUMENT_EMBEDDING",
        ],
        "services": {},
    }

_SVC_CFG = load_service_config()
CORE_SERVICES = _SVC_CFG["core_services"]

_DEFAULT_SERVICE_UI = {
    "APPLICATION_DRAFTING": {"icon":"✍️","label":"Application Drafting","color":"var(--accent)","pill":"pill-green"},
    "RESEARCH":            {"icon":"🔬","label":"Legal Research",       "color":"var(--accent2)","pill":"pill-purple"},
    "QUERY_ANSWER":        {"icon":"💬","label":"Query Answer",         "color":"var(--accent3)","pill":"pill-yellow"},
    "SYNOPSIS_GENERATION": {"icon":"📑","label":"Synopsis Generation",  "color":"var(--info)","pill":"pill-blue"},
    "DOCUMENT_EMBEDDING":  {"icon":"🗂️","label":"Document Embedding",  "color":"var(--danger)","pill":"pill-red"},
}

SERVICE_META = {}
for _key in CORE_SERVICES:
    _cfg = _SVC_CFG.get("services", {}).get(_key, {})
    _base = _DEFAULT_SERVICE_UI.get(_key, {})
    SERVICE_META[_key] = {
        "icon":  _cfg.get("icon",  _base.get("icon", "⚙️")),
        "label": _cfg.get("label", _base.get("label", _key.replace("_", " ").title())),
        "color": _cfg.get("color", _base.get("color", "var(--muted)")),
        "pill":  _cfg.get("pill",  _base.get("pill", "pill-blue")),
    }

CLUSTER_META = {
    0: {"label":"Heavy Draftsman","pill":"pill-green","accent":"var(--accent)","color":"green","icon":"✍️",
        "accent_rgb":"var(--accent-rgb)","desc":"Power user of Application Drafting — high-frequency document creator"},
    1: {"label":"Heavy Researcher","pill":"pill-purple","accent":"var(--accent2)","color":"purple","icon":"🔬",
        "accent_rgb":"var(--accent2-rgb)","desc":"Deep legal research user — case laws, judgments, and court updates"},
    2: {"label":"Query Analyst","pill":"pill-yellow","accent":"var(--accent3)","color":"yellow","icon":"💬",
        "accent_rgb":"var(--accent3-rgb)","desc":"Frequent Q&A user — legal definitions and quick lookups"},
}

REC_SOURCE_LABEL = {
    "als":    "ALS collaborative filter",
    "peer":   "Popular with similar users",
    "global": "Platform-wide trend",
    "usage":  "Grow lowest-usage service (full profile)",
}

def row_get(row, key, default=None):
    try:
        val = row[key]
        return default if val is None else val
    except (KeyError, IndexError):
        return default

def svc(k):
    if not k or not isinstance(k, str):
        return {"icon":"⚙️","label":"Unknown","color":"var(--muted)","pill":"pill-blue"}
    return SERVICE_META.get(k, {"icon":"⚙️","label":k.replace("_"," ").title(),"color":"var(--muted)","pill":"pill-blue"})

def svc_chart_color(k):
    """Return theme-specific raw hex color strings for Plotly (which doesn't support var(--accent))."""
    # Mapping using Python local variables that dynamically contain hex strings
    mapping = {
        "APPLICATION_DRAFTING": accent,
        "RESEARCH":            accent2,
        "QUERY_ANSWER":        accent3,
        "SYNOPSIS_GENERATION": info,
        "DOCUMENT_EMBEDDING":  danger,
    }
    return mapping.get(k, muted)

def _get_name_column():
    """Return the actual name column in user_clusters, or None if not present."""
    try:
        cols = [c[1] for c in get_conn().execute("PRAGMA table_info(user_clusters)").fetchall()]
        if "Name" in cols:
            return "Name"
    except Exception:
        pass
    return None

def build_user_directory(df):
    """Map user_id → real full name. Only works when the Name column exists in the DB."""
    directory = {}
    name_col = _get_name_column()
    if not name_col or df is None or df.empty:
        return directory
    for _, r in df.iterrows():
        uid = str(r.get("user_id", "") or "").strip()
        name = str(r.get(name_col, "") or "").strip()
        if uid and name and name.lower() != "nan":
            directory[uid] = name
    return directory

def fmt_user(uid, directory=None):
    """Return real name from directory, or a clean short UUID fallback."""
    if directory:
        name = directory.get(str(uid))
        if name:
            return name
    return str(uid)[:8] + "…"

def profile_gaps(used_services):
    used = set(used_services or [])
    gaps, filled = [], []
    for key in CORE_SERVICES:
        meta = {**svc(key), "key": key}
        (gaps if key not in used else filled).append(meta)
    return gaps, filled

def rec_source_label(source):
    return REC_SOURCE_LABEL.get(source or "als", "Recommended for you")

def render_html(html):
    """Render HTML using st.markdown — always, so custom CSS classes apply correctly."""
    st.markdown(html, unsafe_allow_html=True)

def cluster_ids_for_ui(df):
    from_db = set(df["cluster_id"].dropna().astype(int).tolist()) if not df.empty else set()
    return sorted(set(CLUSTER_META.keys()) | from_db)

def format_score(value):
    if pd.isna(value):
        return ""
    try:
        return f"{float(value):.0f}"
    except (TypeError, ValueError):
        return str(value)

def explorer_view(df, raw=False):
    """Build a readable Data Explorer table without duplicating raw service codes."""
    if df is None or df.empty:
        return pd.DataFrame()
    if raw:
        return df.copy()

    out = pd.DataFrame()
    _name_col = _get_name_column()
    if _name_col and _name_col in df.columns:
        out["User"] = df[_name_col].astype(str).str.strip().replace("nan", "").where(
            df[_name_col].notna() & df[_name_col].astype(str).str.strip().ne("nan"),
            df["user_id"].astype(str).str[:8] + "…"
        )
    else:
        out["User"] = df["user_id"].astype(str).str[:8] + "…"
    out["User ID"] = df["user_id"]
    out["Segment"] = (
        df["segment_name"] if "segment_name" in df.columns and df["segment_name"].notna().any()
        else df["cluster_id"].map(lambda x: CLUSTER_META.get(x, {}).get("label", f"Cluster {x}"))
    )
    out["Cluster"] = df["cluster_id"]
    out["Active Service"] = (
        df["active_service_name"] if "active_service_name" in df.columns and df["active_service_name"].notna().any()
        else df["active_service"].map(lambda x: svc(x)["label"])
    )
    out["Primary Recommendation"] = (
        df["rec1_name"] if "rec1_name" in df.columns and df["rec1_name"].notna().any()
        else df["cross_recommend_1"].map(lambda x: svc(x)["label"] if pd.notna(x) else "")
    )
    if "rec1_score" in df.columns:
        out["Primary Fit Score"] = df["rec1_score"].map(format_score)
    if "rec1_source" in df.columns:
        out["Primary Source"] = df["rec1_source"].fillna("").str.title()
    out["Secondary Recommendation"] = df.get(
        "rec2_name",
        df["cross_recommend_2"].map(lambda x: svc(x)["label"] if pd.notna(x) else ""),
    )
    if "rec2_score" in df.columns:
        out["Secondary Fit Score"] = df["rec2_score"].map(format_score)
    if "rec2_source" in df.columns:
        out["Secondary Source"] = df["rec2_source"].fillna("").str.title()
    if "last_active_at" in df.columns:
        out["Last Active"] = df["last_active_at"]
    return out

def style_df(df):
    """Apply active theme colors (background and text) to st.dataframe cells using Pandas Styler."""
    if df is None or df.empty:
        return df
    return df.style.set_properties(**{
        'background-color': bg2,
        'color': text
    })

CHART_COLORS = [accent, accent2, accent3, danger, info]
PLOT_BASE    = dict(
    paper_bgcolor=plotly_bg,
    plot_bgcolor=plotly_bg,
    font=dict(color=text, family="Plus Jakarta Sans"),
    xaxis=dict(gridcolor=plotly_grid, zerolinecolor=plotly_grid),
    yaxis=dict(gridcolor=plotly_grid, zerolinecolor=plotly_grid),
)



# ══════════════════════════════════════════════════════════════════════════════
# MODAL DIALOGS
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("Activate Service")
def show_recommendation_dialog(key, label, icon):
    st.markdown(f"### {icon} Welcome to {label}")
    st.write("This personalized recommended tool is optimized for your legal workflow profile.")
    st.divider()
    
    st.write("Configure and activate this service for your workspace:")
    enable_notifs = st.checkbox("Receive notifications and email updates", value=True)
    auto_import = st.checkbox("Automatically link related active case files", value=True)
    
    if st.button("Activate and Launch", type="primary"):
        st.success(f"Service '{label}' successfully activated!")
        if enable_notifs:
            st.caption("✔️ Notifications enabled for this service.")
        if auto_import:
            st.caption("✔️ Related case files automatically linked.")

# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATION BANNER
# ══════════════════════════════════════════════════════════════════════════════
def render_banner(cid, rec1):
    if not rec1:
        st.info("No cross-service recommendations yet — complete more actions to unlock discovery.")
        return
    r1 = svc(rec1)
    if cid == 0:
        cls = "banner-green"
        headline = "Boost Your Case Preparation"
        body = f"80% of draftsmen also use our <strong style='color:var(--accent2)'>{r1['icon']} {r1['label']}</strong> engine to validate case laws before filing."
    elif cid == 1:
        cls = "banner-purple"
        headline = "Tired of Manual Typing?"
        body = f"Turn your research into formatted petitions instantly with <strong style='color:var(--accent)'>{r1['icon']} {r1['label']}</strong>."
    else:
        cls = ""
        headline = "Ready to Go Deeper?"
        body = f"Try <strong style='color:var(--accent)'>{r1['icon']} {r1['label']}</strong> to turn quick answers into formal documents."

    st.markdown(f"""
    <div class="banner {cls}" style="{'background:linear-gradient(135deg,rgba(var(--accent3-rgb),.12),rgba(var(--accent3-rgb),.03));border:1px solid rgba(var(--accent3-rgb),.25)' if cid==2 else ''}">
      <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:6px">{headline}</div>
      <div style="font-size:13px;color:var(--text);opacity:0.8;line-height:1.6;margin-bottom:12px">{body}</div>
    </div>""", unsafe_allow_html=True)
    if st.button(f"→ Try {r1['label']}", key=f"banner_btn_{cid}", type="primary"):
        show_recommendation_dialog(rec1, r1['label'], r1['icon'])


# ══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════════
df_all = load_all()
stats  = db_stats()
pstats = platform_stats()

if df_all.empty:
    st.error(
        f"No users found in `{DB_PATH}`. "
        "Run `colab/als_pipeline.py`, then place `user_clusters.db` in the `data/` folder."
    )
    st.stop()

USER_DIR = build_user_directory(df_all)

for _k, _v in [("active_uid",""),("browse_cid",None),("cluster_users",[])]:
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="logo">⚖️ LawgicHub</div>', unsafe_allow_html=True)
    
    # Theme toggle
    theme_val = st.toggle("☀️ Light Mode", value=st.session_state["is_light"], key="theme_toggle_widget")
    if theme_val != st.session_state["is_light"]:
        st.session_state["is_light"] = theme_val
        st.rerun()

    st.markdown('<div class="sec-head">User Lookup</div>', unsafe_allow_html=True)
    uid_typed = st.text_input("uid", placeholder="Paste UUID here…",
                               label_visibility="collapsed", key="uid_text_input")
    if uid_typed and uid_typed.strip() != st.session_state["active_uid"]:
        _uid = uid_typed.strip()
        if _UUID_RE.match(_uid):
            st.session_state.update({"active_uid": _uid, "browse_cid": None, "cluster_users": []})
            st.rerun()

    if st.button("⚡ Random User"):
        _uids = df_all["user_id"].dropna().astype(str).tolist()
        if not _uids:
            st.warning("No users in the database.")
        else:
            st.session_state.update({
                "active_uid": random.choice(_uids),
                "browse_cid": None, "cluster_users": [],
            })
            st.rerun()

    # ── Browse by Cluster ─────────────────────────────────────────────────────
    st.markdown('<div class="sec-head">Browse by Cluster</div>', unsafe_allow_html=True)
    _ph = "— Select a cluster —"
    _opts = [_ph] + [
        f"{CLUSTER_META.get(i, CLUSTER_META[0])['icon']}  Cluster {i}  —  "
        f"{CLUSTER_META.get(i, CLUSTER_META[0])['label']}"
        for i in cluster_ids_for_ui(df_all)
    ]
    _cur_idx = 0
    if st.session_state["browse_cid"] is not None:
        _cluster_ids_list = cluster_ids_for_ui(df_all)
        try:
            _cur_idx = _cluster_ids_list.index(st.session_state["browse_cid"]) + 1
        except ValueError:
            _cur_idx = 0

    browse_sel = st.selectbox("cluster_sel", options=_opts, index=_cur_idx,
                               label_visibility="collapsed", key="browse_cluster_select")

    _sel_cid = None
    if browse_sel != _ph:
        _m = re.search(r"Cluster\s+(\d+)", browse_sel)
        if _m: _sel_cid = int(_m.group(1))

    if _sel_cid is not None and _sel_cid != st.session_state["browse_cid"]:
        _users = query_users_by_cluster(_sel_cid)
        if _users:
            st.session_state.update({
                "browse_cid": _sel_cid, "cluster_users": _users, "active_uid": _users[0][0]
            })
            st.rerun()
        else:
            st.warning(f"No users found for Cluster {_sel_cid}.")
    elif _sel_cid is None and st.session_state["browse_cid"] is not None:
        st.session_state.update({"browse_cid":None,"cluster_users":[],"active_uid":""})
        st.rerun()

    if st.session_state["browse_cid"] is not None:
        _bm  = CLUSTER_META.get(st.session_state["browse_cid"], CLUSTER_META[0])
        _n   = len(st.session_state["cluster_users"])
        st.markdown(
            f'<div style="margin-top:8px;padding:9px 13px;border-radius:8px;'
            f'background:rgba({_bm["accent_rgb"]},.1);border:1px solid rgba({_bm["accent_rgb"]},.25);'
            f'font-family:\'Space Mono\',monospace;font-size:10px;color:{_bm["accent"]};">'
            f'{_bm["icon"]} {_bm["label"]} &nbsp;·&nbsp; {_n:,} users</div>',
            unsafe_allow_html=True,
        )

    # ── DB Status ─────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-head">DB Status</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="db-badge"><span class="db-dot"></span>'
        f' SQLite · WAL · {stats["size_kb"]} KB</div>', unsafe_allow_html=True
    )
    st.markdown(f"""
    <div style="margin-top:10px;font-family:var(--mono);font-size:10px;color:var(--muted);line-height:2.2">
      Rows &nbsp;&nbsp;: <span style="color:var(--text)">{stats['total']:,}</span><br>
      Tables : <span style="color:var(--text)">{len(stats['tables'])}</span><br>
      Indexes: <span style="color:var(--text)">{len(stats['indexes'])}</span><br>
      Mode &nbsp;: <span style="color:var(--accent)">{stats['wal']}</span>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HEADER + KPI
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="margin-bottom:4px">
  <span style="font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.14em;text-transform:uppercase">
    AI-Powered Legal Platform · PySpark MLlib Segmentation
  </span>
</div>
<h1 style="font-family:'DM Sans',sans-serif;font-size:30px;font-weight:700;color:var(--text);margin:0 0 20px;letter-spacing:-.02em">
  Personalized Legal Workspace
</h1>""", unsafe_allow_html=True)

cdf   = cluster_dist()
total = int(cdf["users"].sum())
_total_events = pstats["total_events"]

for col, (lbl, val, color) in zip(st.columns(4), [
    ("Total Users",    f"{total:,}",          "var(--accent)"),
    ("Clusters",       f"{len(cdf)}",          "var(--accent2)"),
    ("Total Events",   f"{_total_events:,}",   "var(--accent3)"),
    ("Rec. Coverage",  f"{rec_coverage_pct()}%", "var(--danger)"),
]):
    with col:
        st.markdown(f'<div class="mbox"><div class="num" style="color:{color}">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏠  My Workspace", "📊  Analytics", "🗃️  Data Explorer", "🛠️  DB Inspector",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MY WORKSPACE
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    active_uid = st.session_state.get("active_uid", "").strip()

    # ── Cluster browse user-picker ────────────────────────────────────────────
    if st.session_state["browse_cid"] is not None and st.session_state["cluster_users"]:
        _bcid, _cuids = st.session_state["browse_cid"], st.session_state["cluster_users"]
        _bm = CLUSTER_META.get(_bcid, CLUSTER_META[0])
        # cluster_users is list of (uid, name) tuples
        _uid_list  = [u for u, _ in _cuids]
        _name_map  = {u: (str(n).strip() if n and str(n).strip() not in ("", "nan") else u[:8] + "…") for u, n in _cuids}
        st.markdown(f"""
        <div style="background:rgba({_bm['accent_rgb']},.07);border:1px solid rgba({_bm['accent_rgb']},.22);
             border-radius:10px;padding:12px 16px;margin-bottom:14px;display:flex;align-items:center;gap:12px;">
          <span style="font-size:24px">{_bm['icon']}</span>
          <div>
            <div style="font-size:13px;font-weight:600;color:var(--text)">
              Browsing {_bm['label']}
              <span style="font-family:var(--mono);font-size:10px;color:var(--muted);margin-left:8px">
                Cluster #{_bcid} · {len(_uid_list):,} users
              </span>
            </div>
            <div style="font-size:11px;color:var(--muted);font-family:var(--mono)">{_bm['desc']}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        _cur = _uid_list.index(active_uid) if active_uid in _uid_list else 0
        _chosen = st.selectbox(
            "Select user", options=_uid_list, index=_cur,
            format_func=lambda u, _nm=_name_map: f"👤  {_nm.get(u, fmt_user(u, USER_DIR))}",
            label_visibility="collapsed", key="cluster_uid_picker",
        )
        if _chosen != active_uid:
            st.session_state["active_uid"] = _chosen
            active_uid = _chosen
            st.rerun()
        st.divider()

    # ── Empty state ───────────────────────────────────────────────────────────
    if not active_uid:
        st.markdown("""
        <div class="empty-state">
          <div style="font-size:48px;margin-bottom:16px">⚖️</div>
          <div style="font-size:16px;font-weight:600;color:var(--text);margin-bottom:10px">Welcome to LawgicHub</div>
          <div style="line-height:1.8">
            Paste a <strong style="color:var(--accent)">User ID</strong> in the sidebar,<br>
            click <strong style="color:var(--accent)">⚡ Random User</strong> to load a sample profile,<br>
            or select a <strong style="color:var(--accent2)">cluster</strong> to browse users by segment.
          </div>
        </div>""", unsafe_allow_html=True)

    else:
        row = query_user(active_uid)

        if row is None:
            st.markdown(f"""
            <div class="empty-state">
              <div style="font-size:32px;margin-bottom:10px">⚠️</div>
              No record found for<br>
              <span class="uid" style="display:inline-block;margin-top:8px">{h(active_uid)}</span>
            </div>""", unsafe_allow_html=True)

        else:
            # ── Safe extraction ───────────────────────────────────────────────
            cid  = int(row["cluster_id"])   if row["cluster_id"]        is not None else 0
            asvc = row["active_service"]    or "APPLICATION_DRAFTING"
            rec1 = row_get(row, "cross_recommend_1")
            rec2 = row_get(row, "cross_recommend_2")
            rec1_score = row_get(row, "rec1_score")
            rec2_score = row_get(row, "rec2_score")
            rec1_src = row_get(row, "rec1_source", "als")
            rec2_src = row_get(row, "rec2_source", "als")
            last_active = row_get(row, "last_active_at")
            _name_val = row_get(row, "Name") if _get_name_column() == "Name" else None
            display_name = str(_name_val).strip() if _name_val and str(_name_val).strip() not in ("", "nan", "None") else active_uid[:8] + "…"
            active_name = row_get(row, "active_service_name") or svc(asvc)["label"]
            rec1_name = row_get(row, "rec1_name") or (svc(rec1)["label"] if rec1 else None)
            rec2_name = row_get(row, "rec2_name") or (svc(rec2)["label"] if rec2 else None)
            segment_name = row_get(row, "segment_name") or CLUSTER_META.get(cid, CLUSTER_META[0])["label"]
            meta = CLUSTER_META.get(cid, CLUSTER_META[0])
            s    = svc(asvc)

            # ── Real user data from DB ────────────────────────────────────────
            svc_stats    = query_user_service_stats(active_uid)
            activity_log = query_user_activity(active_uid)
            used_keys    = svc_stats["process_type"].tolist() if not svc_stats.empty else []
            gaps, filled = profile_gaps(used_keys)

            # Runtime gap-fill when DB predates pipeline scores (re-run Colab for full ALS)
            if not rec1 and gaps:
                _pop = (
                    pstats["svc_dist"]["process_type"].tolist()
                    if not pstats["svc_dist"].empty else CORE_SERVICES
                )
                _used = set(used_keys)
                for _svc in _pop + [g["key"] for g in gaps]:
                    if _svc not in _used:
                        rec1, rec1_src, rec1_score = _svc, "global", 65.0
                        break

            total_actions   = int(svc_stats["interaction_count"].sum()) if not svc_stats.empty else 0
            services_used   = len(svc_stats)
            gaps_count      = len(gaps)
            top_svc_count   = int(svc_stats["interaction_count"].iloc[0]) if not svc_stats.empty else 0
            activity_count  = len(activity_log)

            # ── Hero card ─────────────────────────────────────────────────────
            _last_active_html = (
                f'<div style="font-size:10px;color:var(--muted);font-family:\'Space Mono\',monospace;margin-top:6px">'
                f"Last active: {h(last_active)}</div>"
                if last_active else ""
            )
            def _rec_span(key, name):
                if not key:
                    return '<span style="color:var(--muted)">—</span>'
                m = svc(key)
                lbl = name or m["label"]
                return f'<span style="color:{m["color"]}">{m["icon"]} {h(lbl)}</span>'

            render_html(dedent(f"""
            <div class="cluster-hero">
              <div style="display:flex;align-items:center;justify-content:center;width:72px;height:72px;border-radius:16px;background:rgba({meta['accent_rgb']},0.12);border:1px solid rgba({meta['accent_rgb']},0.3);font-size:36px;box-shadow: 0 4px 12px rgba(0,0,0,0.05)">{meta['icon']}</div>
              <div style="flex:1">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap">
                  <span class="pill pill-{meta['color']}">{h(segment_name)}</span>
                  <span style="font-family:var(--mono);font-size:10px;color:var(--muted)">Cluster #{cid}</span>
                </div>
                <div style="font-size:20px;font-weight:700;color:var(--text);margin-bottom:4px;letter-spacing:-0.01em">{h(display_name)}</div>
                <div class="uid">{h(active_uid)}</div>
                <div style="font-size:12px;color:var(--text);opacity:0.8;margin-top:6px;line-height:1.4">{meta['desc']}</div>{_last_active_html}
                <div style="margin-top:14px;display:flex;gap:16px;font-family:var(--mono);font-size:11px;flex-wrap:wrap;color:var(--muted)">
                  <span>Active: <span style="color:{s['color']}">{s['icon']} {h(active_name)}</span></span>
                  <span style="color:var(--border)">|</span>
                  <span>Profile gaps: <span style="color:var(--danger);font-weight:700">{gaps_count}</span> / {len(CORE_SERVICES)} services</span>
                  <span style="color:var(--border)">|</span>
                  <span>Rec #1: {_rec_span(rec1, rec1_name)}</span>
                  <span style="color:var(--border)">|</span>
                  <span>Rec #2: {_rec_span(rec2, rec2_name)}</span>
                </div>
              </div>
            </div>
            """).strip())

            # ── Real stats row (like Mixpanel user profile) ───────────────────
            st.markdown('<div class="sec-head">User Activity Summary</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="stat-row">
              <div class="stat-chip">
                <div class="s-val" style="color:var(--accent)">{total_actions:,}</div>
                <div class="s-lbl">Total Actions</div>
              </div>
              <div class="stat-chip">
                <div class="s-val" style="color:var(--accent2)">{services_used}</div>
                <div class="s-lbl">Services Used</div>
              </div>
              <div class="stat-chip">
                <div class="s-val" style="color:var(--danger)">{gaps_count}</div>
                <div class="s-lbl">Discovery Gaps</div>
              </div>
              <div class="stat-chip">
                <div class="s-val" style="color:var(--accent3)">{top_svc_count:,}</div>
                <div class="s-lbl">Top Service Uses</div>
              </div>
              <div class="stat-chip">
                <div class="s-val" style="color:var(--info)">{activity_count}</div>
                <div class="s-lbl">Recent Events</div>
              </div>
            </div>""", unsafe_allow_html=True)


            # ── Two column layout ─────────────────────────────────────────────
            left, right = st.columns([3, 2])

            with left:
                # ── Service usage breakdown (real data) ───────────────────────
                st.markdown('<div class="sec-head">Service Usage Breakdown</div>', unsafe_allow_html=True)
                if not svc_stats.empty:
                    fig_svc = go.Figure(go.Bar(
                        x=svc_stats["process_type"].apply(lambda x: svc(x)["label"]),
                        y=svc_stats["interaction_count"],
                        marker=dict(
                            color=[svc_chart_color(x) for x in svc_stats["process_type"]],
                            line=dict(color=plotly_bg, width=1),
                        ),
                        text=svc_stats["interaction_count"],
                        textposition="outside",
                        textfont=dict(family="Space Mono", size=11, color=text),
                    ))
                    fig_svc.update_layout(PLOT_BASE)
                    fig_svc.update_layout(
                        xaxis=dict(showgrid=False, tickfont=dict(family="Space Mono", size=10, color=text)),
                        yaxis=dict(showgrid=True, gridcolor=plotly_grid,
                                   tickfont=dict(family="Space Mono", size=10, color=text)),
                        margin=dict(t=10, b=10, l=10, r=10), height=220,
                    )
                    st.plotly_chart(fig_svc, use_container_width=True)

                    # Service cards
                    MONO = "Space Mono, monospace"
                    for _, srv_row in svc_stats.iterrows():
                        _sm = svc(srv_row["process_type"])
                        _pct = round(srv_row["interaction_count"] / total_actions * 100) if total_actions else 0
                        is_active = srv_row["process_type"] == asvc
                        _color = _sm["color"]
                        _icon  = _sm["icon"]
                        _label = _sm["label"]
                        _count = int(srv_row["interaction_count"])
                        if is_active:
                            _border = (
                                "border-top:1px solid var(--border);"
                                "border-right:1px solid var(--border);"
                                "border-bottom:1px solid var(--border);"
                                "border-left:3px solid " + _color + ";"
                            )
                            _badge = (
                                "&nbsp;<span style=\"color:" + _color + "\">&#9679; PRIMARY</span>"
                            )
                        else:
                            _border = ""
                            _badge  = ""
                        _html = (
                            "<div class=\"card\" style=\"padding:12px 16px;margin-bottom:6px;" + _border + "\">"
                            "<div style=\"display:flex;justify-content:space-between;align-items:center\">"
                            "<div style=\"display:flex;align-items:center;gap:10px\">"
                            "<span style=\"font-size:18px\">" + _icon + "</span>"
                            "<div>"
                            "<div style=\"font-size:12px;font-weight:600;color:var(--text)\">" + _label + "</div>"
                            "<div style=\"font-size:10px;color:var(--muted);font-family:" + MONO + "\">"
                            + str(_count) + " completions &nbsp;·&nbsp; " + str(_pct) + "% of activity"
                            + _badge +
                            "</div>"
                            "</div>"
                            "</div>"
                            "<div style=\"text-align:right;font-family:" + MONO + ";"
                            "font-size:18px;font-weight:700;color:" + _color + "\">"
                            + str(_count) +
                            "</div>"
                            "</div>"
                            "<div style=\"margin-top:8px;height:4px;background:var(--border);border-radius:4px;\">"
                            "<div style=\"height:4px;width:" + str(_pct) + "%;background:" + _color + ";border-radius:4px;\"></div>"
                            "</div>"
                            "</div>"
                        )
                        st.markdown(_html, unsafe_allow_html=True)
                else:
                    st.info("No service usage data found for this user.")

                # ── Profile gaps (services not yet used) ─────────────────────
                st.markdown('<div class="sec-head">Profile Gaps — Discovery Targets</div>', unsafe_allow_html=True)
                if gaps:
                    st.caption("ALS ranks these unused services by predicted fit with similar users.")
                    for g in gaps:
                        is_rec = g["key"] in (rec1, rec2)
                        st.markdown(f"""
                        <div class="card gap-card" style="padding:12px 16px;margin-bottom:6px;
                             {'border-left:3px solid ' + g['color'] + ';opacity:1' if is_rec else ''}">
                          <div style="display:flex;justify-content:space-between;align-items:center">
                            <div style="display:flex;align-items:center;gap:10px">
                              <span style="font-size:18px;filter:grayscale(.35)">{g['icon']}</span>
                              <div>
                                <div style="font-size:12px;font-weight:600;color:var(--text);opacity:0.8">{g['label']}</div>
                                <div style="font-size:10px;color:var(--muted);font-family:var(--mono)">
                                  Not used yet · {('Rec #1' if g['key']==rec1 else 'Rec #2' if g['key']==rec2 else 'Open gap') if is_rec else 'Open gap'}
                                </div>
                              </div>
                            </div>
                            <span class="pill gap-pill">GAP</span>
                          </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.success("Full platform profile — this user has used all core services.")

            with right:
                # ── Recent activity feed (real data) ──────────────────────────
                st.markdown('<div class="sec-head">Recent Activity</div>', unsafe_allow_html=True)
                if not activity_log.empty:
                    _activity_rows_html = ""
                    for _, evt in activity_log.head(15).iterrows():
                        _em = svc(evt.get("process_type", ""))
                        _ts = evt.get("created_at") or evt.get("timestamp") or evt.get("event_time") or "—"
                        _pn = evt.get("process_name")
                        _subtitle = h(_pn) if _pn and str(_pn) != "nan" else _em["label"]
                        _activity_rows_html += f"""
                        <div class="activity-row">
                          <div style="display:flex;align-items:center;gap:10px">
                            <span style="font-size:16px">{_em['icon']}</span>
                            <div>
                              <div style="font-size:12px;font-weight:500;color:var(--text)">{_em['label']}</div>
                              <div style="font-size:10px;color:var(--text);opacity:0.8;line-height:1.35;max-width:280px">{_subtitle}</div>
                              <div style="font-size:10px;color:var(--muted);font-family:var(--mono)">{h(_ts)}</div>
                            </div>
                          </div>
                          <span class="pill pill-green" style="font-size:9px">DONE</span>
                        </div>"""
                    st.markdown(
                        f'<div class="card" style="padding:0;overflow:hidden;">{_activity_rows_html}</div>',
                        unsafe_allow_html=True)
                else:
                    st.info("No recent activity found.")

                # ── Cross-recommendation cards ────────────────────────────────
                st.markdown('<div class="sec-head">AI Recommendations</div>', unsafe_allow_html=True)

                def _render_rec_card(rank, rkey, rname, score, source):
                    if not rkey:
                        return
                    _rm = svc(rkey)
                    _lbl = rname or _rm["label"]
                    _fit = min(100, max(0, int(float(score)))) if score is not None else None
                    _fit_txt = f"{_fit}% fit" if _fit is not None else "Ranked by platform trends"
                    _src = rec_source_label(source)
                    st.markdown(f"""
                    <div class="card" style="padding:14px 16px;margin-bottom:8px;
                         border-left:3px solid {_rm['color']}">
                      <div style="font-size:9px;color:var(--muted);font-family:var(--mono);
                           letter-spacing:.1em;margin-bottom:6px">REC #{rank}</div>
                      <div style="display:flex;align-items:center;gap:10px">
                        <span style="font-size:22px">{_rm['icon']}</span>
                        <div style="flex:1">
                          <div style="font-size:12px;font-weight:600;color:var(--text)">{h(_lbl)}</div>
                          <div style="font-size:10px;color:var(--muted);font-family:var(--mono)">{_src}</div>
                          <div style="font-size:10px;color:{_rm['color']};font-family:var(--mono);margin-top:4px">
                            {_fit_txt}
                          </div>
                        </div>
                      </div>
                      {f'<div class="fit-bar"><div class="fit-fill" style="width:{_fit}%;background:{_rm["color"]}"></div></div>' if _fit is not None else ''}
                    </div>""", unsafe_allow_html=True)

                if rec1:
                    _render_rec_card(1, rec1, rec1_name, rec1_score, rec1_src)
                if rec2:
                    _render_rec_card(2, rec2, rec2_name, rec2_score, rec2_src)
                if not rec1 and not rec2:
                    st.info("No recommendations yet — re-run the ALS pipeline or enrich script.")

            # ── Recommendation Outreach & Email Campaign ──────────────────────
            st.markdown('<div class="sec-head">✉️ Recommendation Outreach & Email Campaign</div>', unsafe_allow_html=True)

            if rec1:
                r1 = svc(rec1)
                rec_label = rec1_name or r1["label"]
                # Clean name to use as email username
                username_clean = "".join(c for c in display_name if c.isalnum()).lower()
                if len(username_clean) < 3 or username_clean == "nan":
                    username_clean = f"user_{active_uid[:8]}"
                mock_email = f"{username_clean}@example.com"
                
                default_subject = f"⚡ Discover {rec_label} on LawgicHub"
                
                default_body = f"Dear {display_name},\n\nWe noticed you've been actively using our {active_name} service on LawgicHub. To streamline your workflow even further, we highly recommend trying out {rec_label}.\n\nBased on your service usage profile, similar practitioners who use {active_name} found {rec_label} to be extremely valuable for their practice.\n\nTry {rec_label} today: http://lawgichub.ai/services/{rec1.lower()}\n\nBest regards,\nThe LawgicHub Team"

                st.markdown(f"""
                <div class="card card-purple" style="padding:18px 20px;margin-bottom:14px;">
                  <div style="font-size:13px;font-weight:600;color:var(--accent2);margin-bottom:4px">📧 Share Recommendation with {h(display_name)}</div>
                  <div style="font-size:11px;color:var(--text);opacity:0.8;line-height:1.45">
                    This user's profile shows a gap for <strong>{h(rec_label)}</strong>. Send them an email campaign invitation to discover this service.
                  </div>
                </div>
                """, unsafe_allow_html=True)

                ec1, ec2 = st.columns([1, 1])
                with ec1:
                    to_addr = st.text_input("Recipient Address", value=mock_email, key="email_to_addr")
                with ec2:
                    subject = st.text_input("Subject Line", value=default_subject, key="email_subject")

                email_body = st.text_area("Message Body", value=default_body, height=150, key="email_body_text")

                if st.button("📧 Send Recommendation Email", key="send_outreach_email_btn", type="primary"):
                    st.success(f"🎉 Recommendation outreach email successfully queued and sent to {to_addr}!")
            else:
                st.info("No cross-service recommendations available to send outreach emails for this user.")

            # ── Recommendation banner ─────────────────────────────────────────
            st.markdown('<div class="sec-head">💡 Recommended for You</div>', unsafe_allow_html=True)
            render_banner(cid, rec1)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANALYTICS (platform-wide, like Amplitude/Mixpanel overview)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="sec-head">Platform Overview</div>', unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        cdf2 = cluster_dist().copy()
        cdf2["label"] = cdf2["cluster_id"].map(lambda x: CLUSTER_META.get(x,{}).get("label",f"Cluster {x}"))
        fig1 = go.Figure(go.Pie(
            labels=cdf2["label"], values=cdf2["users"], hole=.58,
            marker=dict(colors=CHART_COLORS, line=dict(color=plotly_bg,width=2)),
            textinfo="percent",
            textfont=dict(family="Space Mono",size=11,color=text),
        ))
        fig1.update_layout(PLOT_BASE)
        fig1.update_layout(
            title=dict(text="User Distribution by Cluster",font=dict(family="Plus Jakarta Sans",size=14,color=text)),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(family="Space Mono",size=10,color=text)
            ),
            margin=dict(t=40,b=80,l=20,r=20),height=340)
        st.plotly_chart(fig1, use_container_width=True)

    with a2:
        # Real service volume from user_service_stats
        if not pstats["svc_dist"].empty:
            _sd = pstats["svc_dist"].copy()
            _sd["label"] = _sd["process_type"].apply(lambda x: svc(x)["label"])
            fig_vol = go.Figure(go.Bar(
                x=_sd["label"], y=_sd["total"],
                marker=dict(color=[svc_chart_color(x) for x in _sd["process_type"]],
                            line=dict(color=plotly_bg,width=1)),
                text=_sd["total"], textposition="outside",
                textfont=dict(family="Space Mono",size=11,color=text),
            ))
            fig_vol.update_layout(PLOT_BASE)
            fig_vol.update_layout(
                title=dict(text="Total Completions by Service",font=dict(family="Plus Jakarta Sans",size=14,color=text)),
                xaxis=dict(showgrid=False,tickfont=dict(family="Space Mono",size=11,color=text)),
                yaxis=dict(showgrid=True,gridcolor=plotly_grid,tickfont=dict(family="Space Mono",size=10,color=text)),
                margin=dict(t=40,b=40,l=20,r=20),height=340)
            st.plotly_chart(fig_vol, use_container_width=True)

    st.markdown('<div class="sec-head">Cross-Recommendation Frequency</div>', unsafe_allow_html=True)
    rdf = rec_frequency()
    if not rdf.empty:
        rdf["label"] = rdf["service"].apply(lambda x: svc(x)["label"])
        fig2 = go.Figure(go.Bar(
            x=rdf["label"], y=rdf["freq"],
            marker=dict(color=CHART_COLORS[:len(rdf)],line=dict(color=plotly_bg,width=1)),
            text=rdf["freq"], textposition="outside",
            textfont=dict(family="Space Mono",size=11,color=text),
        ))
        fig2.update_layout(PLOT_BASE)
        fig2.update_layout(
            xaxis=dict(showgrid=False,tickfont=dict(family="Space Mono",size=11,color=text)),
            yaxis=dict(showgrid=True,gridcolor=plotly_grid,tickfont=dict(family="Space Mono",size=10,color=text)),
            margin=dict(t=16,b=36,l=16,r=16),height=260)
        st.plotly_chart(fig2, use_container_width=True)

    # Top active users table (like Mixpanel "Top Users")
    if not pstats["top_users"].empty:
        st.markdown('<div class="sec-head">Top Users by Activity</div>', unsafe_allow_html=True)
        _tu = pstats["top_users"].copy()
        _tu["Name"] = _tu["Name"].fillna(_tu["user_id"].map(lambda u: fmt_user(u, USER_DIR))) if "Name" in _tu.columns else _tu["user_id"].map(lambda u: fmt_user(u, USER_DIR))
        _tu["Cluster"] = _tu["cluster_id"].map(lambda x: f"{CLUSTER_META.get(x,{}).get('icon','?')} {CLUSTER_META.get(x,{}).get('label',f'Cluster {x}')}")
        _tu["Service"] = _tu["active_service"].apply(lambda x: svc(x)["label"])
        _tu = _tu.rename(columns={"user_id":"User ID","total_actions":"Total Actions"})
        st.dataframe(
            _tu[["Name","User ID","Cluster","Service","Total Actions"]],
            use_container_width=True, hide_index=True, height=400,
        )

    st.markdown('<div class="sec-head">Service Adoption by Cluster</div>', unsafe_allow_html=True)
    sdf = service_by_cluster()
    if not sdf.empty:
        sdf["Service"] = sdf["active_service"].apply(lambda x: svc(x)["label"] if x else "Unknown")
        sdf["Cluster"] = sdf["cluster_id"].map(lambda x: CLUSTER_META.get(x,{}).get("label",f"Cluster {x}"))
        fig3 = px.bar(sdf, x="Cluster", y="cnt", color="Service", barmode="group",
                      color_discrete_sequence=CHART_COLORS,
                      labels={"cnt":"Users","Cluster":"User Segment"})
        fig3.update_layout(PLOT_BASE)
        fig3.update_layout(
            legend=dict(font=dict(family="Space Mono",size=10,color=text)),
            xaxis=dict(showgrid=False,tickfont=dict(family="Space Mono",size=11,color=text)),
            yaxis=dict(showgrid=True,gridcolor=plotly_grid,tickfont=dict(family="Space Mono",size=10,color=text)),
            margin=dict(t=16,b=36,l=16,r=16),height=290)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="sec-head">Cluster Summary</div>', unsafe_allow_html=True)
    try:
        summary = df_all.groupby("cluster_id").agg(
            Users   =("user_id",           "count"),
            Act_Svc =("active_service",    lambda x: x.dropna().value_counts().index[0] if not x.dropna().empty else "—"),
            Top_Rec=("cross_recommend_1", lambda x: x.dropna().value_counts().index[0] if x.dropna().any() else "—"),
        ).reset_index()
        summary["Segment"] = summary["cluster_id"].map(lambda x: CLUSTER_META.get(x,{}).get("label","—"))
        summary.columns    = ["Cluster ID","Users","Top Active Service","Top Recommendation","Segment"]
        st.dataframe(summary[["Cluster ID","Segment","Users","Top Active Service","Top Recommendation"]],
                     use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"Summary unavailable: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — DATA EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="sec-head">User Recommendation Explorer</div>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns([1, 2, 1, 1])
    with fc1:
        cluster_filter = st.multiselect("Filter by Cluster",
            options=sorted(df_all["cluster_id"].unique()),
            default=sorted(df_all["cluster_id"].unique()),
            format_func=lambda x: f"Cluster {x} — {CLUSTER_META.get(x,{}).get('label','?')}")
    with fc2:
        search_str = st.text_input(
            "Search", placeholder="Name or partial UUID…", key="explorer_search"
        )
    with fc3:
        svc_filter = st.multiselect("Filter by Service",
            options=sorted(df_all["active_service"].dropna().unique()),
            default=sorted(df_all["active_service"].dropna().unique()),
            format_func=lambda x: svc(x)["label"])
    with fc4:
        show_raw_cols = st.checkbox("Raw columns", value=False, help="Show pipeline service codes and database column names.")

    filtered = df_all[df_all["cluster_id"].isin(cluster_filter)]
    if svc_filter:
        filtered = filtered[
            filtered["active_service"].isin(svc_filter) | filtered["active_service"].isna()
        ]
    if search_str:
        _q = search_str.strip()
        _mask = filtered["user_id"].str.contains(_q, case=False, na=False)
        if "Name" in filtered.columns:
            _mask = _mask | filtered["Name"].str.contains(_q, case=False, na=False)
        elif "user_display_name" in filtered.columns:
            _mask = _mask | filtered["user_display_name"].str.contains(_q, case=False, na=False)
        filtered = filtered[_mask]

    explorer_df = explorer_view(filtered, raw=show_raw_cols)
    st.caption(f"Showing {len(filtered):,} of {len(df_all):,} records")
    st.dataframe(style_df(explorer_df),
                 use_container_width=True, hide_index=True, height=440)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Export CSV",
            data=explorer_df.to_csv(index=False).encode(),
            file_name="user_clusters_export.csv", mime="text/csv")
    with c2:
        st.download_button("⬇️ Export JSON",
            data=explorer_df.to_json(orient="records", indent=2).encode(),
            file_name="user_clusters_export.json", mime="application/json")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DB INSPECTOR
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="sec-head">SQLite Diagnostics</div>', unsafe_allow_html=True)
    for col, (lbl, val, clr) in zip(st.columns(4), [
        ("File Size",    f"{stats['size_kb']} KB",  "var(--accent)"),
        ("Journal Mode", stats["wal"],               "var(--accent2)"),
        ("Total Rows",   f"{stats['total']:,}",      "var(--accent3)"),
        ("Indexes",      str(len(stats["indexes"])), "var(--danger)"),
    ]):
        with col:
            st.markdown(f'<div class="mbox"><div class="num" style="color:{clr}">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("")
    i1, i2 = st.columns(2)

    with i1:
        st.markdown('<div class="sec-head">Tables</div>', unsafe_allow_html=True)
        _allowed_tables = {t for t in stats["tables"] if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", t)}
        for tbl in stats["tables"]:
            try:
                if tbl not in _allowed_tables:
                    raise ValueError("invalid table name")
                n = get_conn().execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
                n_display = f"{n:,}"
            except Exception:
                n_display = "?"
            st.markdown(
                f'<div class="card" style="padding:11px 16px;margin-bottom:6px">'
                f'<span style="font-family:\'Space Mono\',monospace;font-size:11px;color:var(--accent2)">🗄 {tbl}</span>'
                f'<span style="font-family:\'Space Mono\',monospace;font-size:10px;color:var(--muted);margin-left:12px">{n_display} rows</span></div>',
                unsafe_allow_html=True)

        st.markdown('<div class="sec-head">Active Indexes</div>', unsafe_allow_html=True)
        if stats["indexes"]:
            for idx in stats["indexes"]:
                st.markdown(
                    f'<div class="card" style="padding:11px 16px;margin-bottom:6px">'
                    f'<span style="font-family:\'Space Mono\',monospace;font-size:11px;color:var(--accent)">⚡ {idx}</span></div>',
                    unsafe_allow_html=True)
        else:
            st.warning("No indexes — re-run the pipeline with the fixed Cell 8.")

    with i2:
        st.markdown('<div class="sec-head">PRAGMA Settings</div>', unsafe_allow_html=True)
        _conn = get_conn()
        for p in ["journal_mode","synchronous","cache_size","temp_store","mmap_size","page_size"]:
            try: _val = _conn.execute(f"PRAGMA {p}").fetchone()[0]
            except Exception: _val = "n/a"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;font-family:var(--mono);
                        font-size:11px;padding:7px 0;border-bottom:1px solid var(--border)">
              <span style="color:var(--muted)">{p}</span>
              <span style="color:var(--accent)">{_val}</span>
            </div>""", unsafe_allow_html=True)
