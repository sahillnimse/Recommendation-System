# ╔══════════════════════════════════════════════════════════════════╗
# ║   LawgicHub — ALS Collaborative Filtering Pipeline              ║
# ║   Run on: Google Colab (GPU not required)                       ║
# ║   Output: user_clusters.db                                      ║
# ║     → table: user_clusters      (recs + affinity scores)        ║
# ║     → table: user_activity      (all COMPLETED events per user) ║
# ║     → table: user_service_stats (per-user per-service counts)   ║
# ║   Rec logic: ALS ranks profile gaps; peer/global fill any nulls ║
# ╚══════════════════════════════════════════════════════════════════╝

# ─────────────────────────────────────────────────────────────────
# CELL 1 — Prerequisites
# ─────────────────────────────────────────────────────────────────
# !apt-get install -y openjdk-11-jdk-headless -qq > /dev/null
# !pip install pyspark findspark --quiet

import os
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-11-openjdk-amd64"

import findspark
findspark.init()
print("✅ PySpark environment ready")


# ─────────────────────────────────────────────────────────────────
# CELL 2 — SparkSession
# ─────────────────────────────────────────────────────────────────
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("LawgicHub-ALS-Recommendations")
    .config("spark.driver.memory", "4g")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")
print("✅ SparkSession started:", spark.version)


# ─────────────────────────────────────────────────────────────────
# CELL 3 — Ingest CSV
# ─────────────────────────────────────────────────────────────────
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType

RAW_CSV = "process_tracking_2026-06-02.csv"

tracking_df = (
    spark.read
    .option("header",      "true")
    .option("inferSchema", "true")
    .option("multiLine",   "true")
    .option("escape",      '"')
    .csv(RAW_CSV)
)

print(f"✅ Loaded {tracking_df.count():,} rows  |  Columns: {tracking_df.columns}")
tracking_df.printSchema()
tracking_df.show(5, truncate=False)


# ─────────────────────────────────────────────────────────────────
# CELL 3B — Service config (upload config/services.json to Colab)
#            Single source of truth — add new services here only
# ─────────────────────────────────────────────────────────────────
import json
from pathlib import Path

def _load_service_config():
    for path in ("services.json", "config/services.json", "../config/services.json"):
        p = Path(path)
        if p.exists():
            print(f"✅ Loaded service config: {p}")
            return json.loads(p.read_text(encoding="utf-8"))
    print("⚠️  services.json not found — using inline defaults (upload config/services.json)")
    return {
        "core_services": [
            "APPLICATION_DRAFTING", "RESEARCH", "QUERY_ANSWER",
            "SYNOPSIS_GENERATION", "DOCUMENT_EMBEDDING",
        ],
        "service_priority": [
            "APPLICATION_DRAFTING", "RESEARCH", "QUERY_ANSWER",
            "SYNOPSIS_GENERATION", "DOCUMENT_EMBEDDING",
        ],
        "services": {
            "APPLICATION_DRAFTING": {"cluster_id": 0},
            "RESEARCH": {"cluster_id": 1},
            "QUERY_ANSWER": {"cluster_id": 2},
            "SYNOPSIS_GENERATION": {"cluster_id": 0},
            "DOCUMENT_EMBEDDING": {"cluster_id": 0},
        },
        "recommendation": {"gap_usage_percentile": 25, "use_percentile_gaps": False},
        "cluster_analysis": {"run_on_build": True, "k_min": 2, "k_max": 8, "sample_users": 2000},
        "user_metadata": {
            "timestamp_columns": ["created_at", "timestamp", "event_time", "completed_at", "updated_at"],
            "pass_through_columns": [],
        },
    }

CFG = _load_service_config()
CORE_SERVICES = CFG["core_services"]
SERVICE_PRIORITY = CFG["service_priority"]
SERVICE_CLUSTER = {k: v.get("cluster_id", 0) for k, v in CFG["services"].items()}
USE_PERCENTILE_GAPS = CFG["recommendation"]["use_percentile_gaps"]
GAP_PERCENTILE = CFG["recommendation"]["gap_usage_percentile"] / 100.0
PRIORITY_RANK = {svc: i for i, svc in enumerate(SERVICE_PRIORITY)}

from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

def _priority_col():
    expr = F.lit(len(SERVICE_PRIORITY))
    for svc, rank in PRIORITY_RANK.items():
        expr = F.when(F.col("process_type") == svc, rank).otherwise(expr)
    return expr

def _cluster_id_col(col_name="active_service"):
    expr = None
    for svc, cid in SERVICE_CLUSTER.items():
        clause = F.when(F.col(col_name) == svc, int(cid))
        expr = clause if expr is None else expr.when(F.col(col_name) == svc, int(cid))
    return (expr.otherwise(0).cast(IntegerType()) if expr is not None else F.lit(0))

def _pick_active_service(df):
    """Highest interaction_count; ties broken by service_priority (first wins)."""
    w = Window.partitionBy("user_idx", "user_id").orderBy(
        F.col("interaction_count").desc(),
        F.col("_pri").asc(),
    )
    return (
        df.withColumn("_pri", _priority_col())
        .withColumn("_rn", row_number().over(w))
        .filter(F.col("_rn") == 1)
        .select("user_idx", "user_id", F.col("process_type").alias("active_service"))
    )


# ─────────────────────────────────────────────────────────────────
# CELL 4 — Normalize + filter + build affinity matrix
# ─────────────────────────────────────────────────────────────────

# CORE_SERVICES loaded from config/services.json (CELL 3B)

# Normalize case on both columns before filtering
normalized_df = (
    tracking_df
    .withColumn("status",       F.upper(F.col("status")))        # completed → COMPLETED
    .withColumn("process_type", F.upper(F.col("process_type")))  # application_drafting → APPLICATION_DRAFTING
)

# Filter: COMPLETED status + core services only
completed_df = normalized_df.filter(
    (F.col("status") == "COMPLETED") &
    (F.col("process_type").isin(CORE_SERVICES))
)

print(f"✅ Raw rows          : {tracking_df.count():,}")
print(f"✅ After normalize+filter: {completed_df.count():,}")
print(f"   (was {tracking_df.filter(F.col('status') == 'COMPLETED').count():,} with old strict filter)")

# Count interactions per user per service
affinity_df = (
    completed_df
    .groupBy("user_id", "process_type")
    .agg(F.count("*").alias("interaction_count"))
    .filter(F.col("interaction_count") > 0)
)

print("\n✅ Affinity matrix:")
affinity_df.show(10, truncate=False)
print(f"   Unique users         : {affinity_df.select('user_id').distinct().count():,}")
print(f"   Unique process types : {affinity_df.select('process_type').distinct().count()}")
affinity_df.groupBy("process_type").agg(F.sum("interaction_count").alias("total")).orderBy("total", ascending=False).show()


# ─────────────────────────────────────────────────────────────────
# CELL 4B — Save per-user activity tables (for analytics in app.py)
# ─────────────────────────────────────────────────────────────────

# Table 1: user_activity — every COMPLETED event row per user
# Keeps: user_id, process_type, status, created_at (or timestamp col if exists)
# We pick whatever columns are available
available_cols = tracking_df.columns
activity_cols  = ["user_id", "process_type", "status"]
if "process_name" in available_cols:
    activity_cols.append("process_name")

# Add timestamp column if it exists under any common name
for ts_col in ["created_at", "timestamp", "event_time", "date", "updated_at", "completed_at"]:
    if ts_col in available_cols:
        activity_cols.append(ts_col)
        break

user_activity_df = (
    completed_df
    .select(*[c for c in activity_cols if c in available_cols])
)
print(f"✅ user_activity table: {user_activity_df.count():,} rows, cols: {user_activity_df.columns}")
user_activity_df.show(5, truncate=False)

# Table 2: user_service_stats — per-user per-service interaction counts + first/last seen
# This powers the per-user analytics panel in app.py
user_stats_df = (
    affinity_df
    .select("user_id", "process_type", "interaction_count")
)
print(f"✅ user_service_stats table: {user_stats_df.count():,} rows")
user_stats_df.show(10, truncate=False)


# ─────────────────────────────────────────────────────────────────
# CELL 5 — String indexing
# ─────────────────────────────────────────────────────────────────
from pyspark.ml.feature import StringIndexer

user_indexer = (
    StringIndexer(inputCol="user_id", outputCol="user_idx")
    .setHandleInvalid("keep")
    .fit(affinity_df)
)
process_indexer = (
    StringIndexer(inputCol="process_type", outputCol="process_idx")
    .setHandleInvalid("keep")
    .fit(affinity_df)
)

user_labels    = user_indexer.labels
process_labels = process_indexer.labels

print("✅ User index size  :", len(user_labels))
print("✅ Process types    :", process_labels)

indexed_df = user_indexer.transform(affinity_df)
indexed_df = process_indexer.transform(indexed_df)
indexed_df = (
    indexed_df
    .withColumn("user_idx",    F.col("user_idx").cast(IntegerType()))
    .withColumn("process_idx", F.col("process_idx").cast(IntegerType()))
    .select("user_idx", "process_idx", "interaction_count", "user_id", "process_type")
)
indexed_df.show(10)


# ─────────────────────────────────────────────────────────────────
# CELL 6 — Train ALS model
# ─────────────────────────────────────────────────────────────────
from pyspark.ml.recommendation import ALS

als = ALS(
    userCol          = "user_idx",
    itemCol          = "process_idx",
    ratingCol        = "interaction_count",
    rank             = 10,
    maxIter          = 15,
    regParam         = 0.1,
    implicitPrefs    = True,
    alpha            = 40.0,
    coldStartStrategy= "drop",
    seed             = 42,
    nonnegative      = True,
)
als_model = als.fit(indexed_df)
print(f"✅ ALS model trained  |  rank={als_model.rank}")


# ─────────────────────────────────────────────────────────────────
# CELL 6B — Cluster diagnostics (Elbow + Silhouette on usage vectors)
#            Segments are service-based (not KMeans); this validates K
# ─────────────────────────────────────────────────────────────────
_ca = CFG.get("cluster_analysis", {})
if _ca.get("run_on_build", False):
    try:
        # !pip install scikit-learn --quiet
        import numpy as np
        import pandas as pd
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        _piv = (
            affinity_df.groupBy("user_id", "process_type")
            .agg(F.sum("interaction_count").alias("cnt"))
            .groupBy("user_id")
            .pivot("process_type", CORE_SERVICES)
            .sum("cnt")
            .fillna(0)
        )
        _sample_n = min(_ca.get("sample_users", 2000), _piv.count())
        _pdf = _piv.orderBy(F.rand()).limit(_sample_n).toPandas()
        _feat = [c for c in _pdf.columns if c != "user_id"]
        _X = np.log1p(_pdf[_feat].astype(float).values)
        _k_min, _k_max = _ca.get("k_min", 2), min(_ca.get("k_max", 8), len(_pdf) - 1)
        print(f"\n── Cluster diagnostics (sample={len(_pdf):,} users, features={len(_feat)}) ──")
        _rows = []
        for k in range(_k_min, _k_max + 1):
            if k >= len(_pdf):
                break
            _km = KMeans(n_clusters=k, random_state=42, n_init=10)
            _labels = _km.fit_predict(_X)
            _sil = silhouette_score(_X, _labels) if k > 1 else float("nan")
            _rows.append({"K": k, "inertia": round(_km.inertia_, 1), "silhouette": round(_sil, 3)})
        _diag = pd.DataFrame(_rows)
        print(_diag.to_string(index=False))
        if len(_diag) > 1:
            _best = _diag.loc[_diag["silhouette"].idxmax(), "K"]
            print(f"→ Best silhouette K={int(_best)} (current UI segments: {len(set(SERVICE_CLUSTER.values()))})")
    except Exception as e:
        print(f"⚠️  Cluster diagnostics skipped: {e}")


# ─────────────────────────────────────────────────────────────────
# CELL 7 — Cross-recommendations: ALS scores only on profile gaps
# ─────────────────────────────────────────────────────────────────
from pyspark.sql.functions import col, explode, udf

NUM_RECS = 2
# Request every service so filtering "already used" still leaves enough candidates
raw_recs = als_model.recommendForAllUsers(numItems=len(CORE_SERVICES))

recs_exploded = (
    raw_recs
    .select("user_idx", explode("recommendations").alias("rec"))
    .select(
        "user_idx",
        col("rec.process_idx").alias("rec_process_idx"),
        col("rec.rating").alias("rec_score"),
    )
)

decode_process = udf(lambda idx: process_labels[idx] if idx < len(process_labels) else "UNKNOWN", StringType())
decode_user    = udf(lambda idx: user_labels[idx]    if idx < len(user_labels)    else "UNKNOWN", StringType())

recs_decoded = (
    recs_exploded
    .withColumn("rec_process_type", decode_process(col("rec_process_idx")))
    .withColumn("user_id",          decode_user(col("user_idx")))
)

# Primary active service — tie-break via service_priority when counts equal
active_service = _pick_active_service(indexed_df)

# Profile gaps: unused services, or bottom-percentile usage when enabled
if USE_PERCENTILE_GAPS:
    _gap_thresholds = (
        affinity_df.groupBy("process_type")
        .agg(F.expr(f"percentile_approx(interaction_count, {GAP_PERCENTILE})").alias("gap_threshold"))
    )
    _meaningful = (
        indexed_df.join(_gap_thresholds, on="process_type")
        .filter(F.col("interaction_count") > F.col("gap_threshold"))
    )
    already_uses = (
        _meaningful.select("user_idx", "process_type")
        .distinct()
        .withColumnRenamed("process_type", "existing_service")
    )
    print(f"✅ Gap mode: percentile (>{GAP_PERCENTILE:.0%} usage counts as 'adopted')")
else:
    already_uses = (
        indexed_df.select("user_idx", "process_type")
        .distinct()
        .withColumnRenamed("process_type", "existing_service")
    )

cross_recs = (
    recs_decoded
    .join(
        already_uses,
        (recs_decoded.user_idx == already_uses.user_idx) &
        (recs_decoded.rec_process_type == already_uses.existing_service),
        how="left_anti",
    )
)

w = Window.partitionBy("user_idx").orderBy(col("rec_score").desc())
cross_recs_ranked = (
    cross_recs
    .withColumn("rank", row_number().over(w))
    .filter(col("rank") <= NUM_RECS)
)

rec1_df = cross_recs_ranked.filter(col("rank") == 1).select(
    "user_idx",
    col("rec_process_type").alias("cross_recommend_1"),
    col("rec_score").alias("rec1_score"),
)
rec2_df = cross_recs_ranked.filter(col("rank") == 2).select(
    "user_idx",
    col("rec_process_type").alias("cross_recommend_2"),
    col("rec_score").alias("rec2_score"),
)

final_recs = (
    active_service
    .join(rec1_df, on="user_idx", how="left")
    .join(rec2_df, on="user_idx", how="left")
    .select(
        "user_idx", "user_id", "active_service",
        "cross_recommend_1", "rec1_score",
        "cross_recommend_2", "rec2_score",
    )
)

print(f"✅ ALS gap recommendations for {final_recs.count():,} users")
final_recs.show(15, truncate=False)


# ─────────────────────────────────────────────────────────────────
# CELL 7B — Derive cluster_id from active_service (config-driven)
# ─────────────────────────────────────────────────────────────────

final_recs = final_recs.withColumn("cluster_id", _cluster_id_col("active_service"))

# Drop user_idx — not needed by app.py
final_recs = final_recs.select(
    "user_id",
    "cluster_id",
    "active_service",
    "cross_recommend_1",
    "rec1_score",
    "cross_recommend_2",
    "rec2_score",
)

print("✅ cluster_id derived from active_service:")
final_recs.groupBy("cluster_id", "active_service").count().orderBy("cluster_id").show()
final_recs.show(10, truncate=False)


# ─────────────────────────────────────────────────────────────────
# CELL 7C — Ensure every user has 1 gap-filling rec (peer → global)
# ─────────────────────────────────────────────────────────────────
import pandas as pd


def _cluster_id(active_service):
    return SERVICE_CLUSTER.get(active_service, 0)


def _pick_gap(candidates, used, already_chosen):
    for svc in candidates:
        if svc in CORE_SERVICES and svc not in used and svc not in already_chosen:
            return svc
    return None


def _usage_growth(uid, affinity_pd, active_service):
    u = affinity_pd[affinity_pd["user_id"] == uid].sort_values("interaction_count")
    cands = [s for s in u["process_type"].tolist() if s != active_service]
    if not cands:
        cands = u["process_type"].tolist()
    return (cands[0] if len(cands) > 0 else None, cands[1] if len(cands) > 1 else None)


def _fill_recommendations(rec_df, affinity_pd):
    """Fill null recs: ALS gaps → peer/global → lowest-usage upsell when profile is full."""
    global_rank = (
        affinity_pd.groupby("process_type")["interaction_count"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    user_active = rec_df[["user_id", "active_service"]].drop_duplicates()
    aff_peer = affinity_pd.merge(user_active, on="user_id")
    peer_totals = (
        aff_peer.groupby(["active_service", "process_type"])["interaction_count"]
        .sum()
        .reset_index(name="peer_total")
    )

    used_by_user = (
        affinity_pd.groupby("user_id")["process_type"]
        .apply(lambda s: set(s.tolist()))
        .to_dict()
    )

    peer_lists = {}
    for asvc, grp in peer_totals.groupby("active_service"):
        peer_lists[asvc] = (
            grp.sort_values("peer_total", ascending=False)["process_type"].tolist()
        )

    rows = []
    for _, row in rec_df.iterrows():
        uid = row["user_id"]
        asvc = row["active_service"]
        used = used_by_user.get(uid, set())
        peer_list = peer_lists.get(asvc, global_rank)

        r1 = row.get("cross_recommend_1")
        s1 = row.get("rec1_score")
        src1 = "als" if pd.notna(r1) else None
        r2 = row.get("cross_recommend_2")
        s2 = row.get("rec2_score")
        src2 = "als" if pd.notna(r2) else None

        if src1 == "als" and pd.notna(s1):
            s1 = 88.0
        if src2 == "als" and pd.notna(s2):
            s2 = 58.0

        chosen = {x for x in (r1, r2) if pd.notna(x) and x}

        def _fallback_source(svc):
            top_peer = peer_list[: max(3, len(CORE_SERVICES) - 1)]
            return "peer" if svc in top_peer else "global"

        if not r1 or pd.isna(r1):
            r1 = _pick_gap(peer_list, used, chosen) or _pick_gap(global_rank, used, chosen)
            if r1:
                s1, src1 = 72.0, _fallback_source(r1)
                chosen.add(r1)

        if not r2 or pd.isna(r2):
            r2 = _pick_gap(peer_list, used, chosen) or _pick_gap(global_rank, used, chosen)
            if r2:
                s2, src2 = 58.0, _fallback_source(r2)

        if (not r1 or pd.isna(r1)) and len(used) >= len(CORE_SERVICES):
            r1, r2 = _usage_growth(uid, affinity_pd, asvc)
            if r1:
                s1, src1 = 65.0, "usage"
            if r2:
                s2, src2 = 52.0, "usage"

        rows.append({
            "user_id": uid,
            "cluster_id": int(row["cluster_id"]),
            "active_service": asvc,
            "cross_recommend_1": r1,
            "rec1_score": float(s1) if pd.notna(s1) else None,
            "rec1_source": src1,
            "cross_recommend_2": r2,
            "rec2_score": float(s2) if pd.notna(s2) else None,
            "rec2_source": src2,
        })

    return pd.DataFrame(rows)


# Users in affinity but missing from ALS output (sparse / dropped)
all_users = affinity_df.select("user_id").distinct()
als_users = final_recs.select("user_id")
missing_users = all_users.join(als_users, on="user_id", how="left_anti")

if missing_users.count() > 0:
    print(f"Users missing ALS row: {missing_users.count():,} — building from affinity")
    missing_indexed = indexed_df.join(missing_users, on="user_id")
    missing_active = _pick_active_service(missing_indexed)
    missing_pd = missing_active.toPandas()
    missing_pd["cluster_id"] = missing_pd["active_service"].map(_cluster_id)
    for c in ("cross_recommend_1", "rec1_score", "rec1_source",
              "cross_recommend_2", "rec2_score", "rec2_source"):
        missing_pd[c] = None
    final_pd_partial = final_recs.toPandas()
    final_pd = pd.concat([final_pd_partial, missing_pd], ignore_index=True)
else:
    final_pd = final_recs.toPandas()

affinity_pd = affinity_df.toPandas()
final_pd = _fill_recommendations(final_pd, affinity_pd)

# ── Restore User Names (if reference or existing DB exists) ──
name_map = {}
import sqlite3
# 1. Try to load from user_clusters_new.db reference database
for path_ref in ("user_clusters_new.db", "data/user_clusters_new.db", "../data/user_clusters_new.db"):
    p_ref = Path(path_ref)
    if p_ref.exists():
        try:
            with sqlite3.connect(str(p_ref)) as conn_ref:
                for uid, name in conn_ref.execute("SELECT user_id, Name FROM user_clusters").fetchall():
                    if name and str(name).strip() not in ("", "nan", "None"):
                        name_map[str(uid).strip()] = str(name).strip()
            print(f"✅ Loaded {len(name_map)} name mappings from {p_ref}")
            break
        except Exception:
            pass

# 2. Try to load from old user_clusters.db if not already found in reference database
if not name_map:
    for path_old in ("user_clusters.db", "data/user_clusters.db", "../data/user_clusters.db"):
        p_old = Path(path_old)
        if p_old.exists():
            try:
                with sqlite3.connect(str(p_old)) as conn_old:
                    cols = [r[1] for r in conn_old.execute("PRAGMA table_info(user_clusters)").fetchall()]
                    if "Name" in cols:
                        for uid, name in conn_old.execute("SELECT user_id, Name FROM user_clusters").fetchall():
                            if name and str(name).strip() not in ("", "nan", "None"):
                                name_map[str(uid).strip()] = str(name).strip()
                if name_map:
                    print(f"✅ Loaded {len(name_map)} name mappings from existing {p_old}")
                    break
            except Exception:
                pass

if name_map:
    final_pd["Name"] = final_pd["user_id"].map(name_map)
    print(f"✅ Merged user names for {final_pd['Name'].notna().sum()} users")
else:
    final_pd["Name"] = None
    print("⚠️  No user name reference database found — 'Name' column will be populated as NULL (run enrich_db.py locally to restore)")

# ── User metadata (last_active_at + optional pass-through columns) ──
_ts_cols = CFG["user_metadata"]["timestamp_columns"]
_ts_col = next((c for c in _ts_cols if c in available_cols), None)
if _ts_col:
    _last = (
        completed_df.groupBy("user_id")
        .agg(F.max(F.col(_ts_col)).alias("last_active_at"))
        .toPandas()
    )
    final_pd = final_pd.merge(_last, on="user_id", how="left")
    print(f"✅ last_active_at from {_ts_col}")

for _extra in CFG["user_metadata"].get("pass_through_columns", []):
    if _extra in tracking_df.columns:
        _extra_pd = (
            tracking_df.groupBy("user_id")
            .agg(F.first(F.col(_extra), ignorenulls=True).alias(_extra))
            .toPandas()
        )
        final_pd = final_pd.merge(_extra_pd, on="user_id", how="left")
        print(f"✅ pass-through column: {_extra}")

# Human-readable labels for dashboard
def _svc_label(key):
    if not key or (isinstance(key, float) and pd.isna(key)):
        return None
    return CFG.get("services", {}).get(key, {}).get("label", str(key).replace("_", " ").title())

def _seg_label(cid):
    c = CFG.get("clusters", {}).get(str(int(cid))) or CFG.get("clusters", {}).get(int(cid), {})
    return c.get("label", f"Cluster {cid}")

def _clean_title(name):
    if not name or (isinstance(name, float) and pd.isna(name)):
        return None
    t = str(name).strip()
    for p in ("Async Research: ", "Async Query: ", "Async Synopsis: ", "Async Draft: ", "Async "):
        if t.startswith(p):
            return t[len(p):][:56]
    return t[:56]

_name_src = CFG["user_metadata"].get("display_name_from", "process_name")
if _name_src in final_pd.columns:
    final_pd["user_display_name"] = final_pd[_name_src].map(_clean_title)
else:
    final_pd["user_display_name"] = None
final_pd["user_display_name"] = final_pd.apply(
    lambda r: r["user_display_name"] or f"User · {str(r['user_id'])[:8]}…", axis=1
)
final_pd["active_service_name"] = final_pd["active_service"].map(_svc_label)
final_pd["rec1_name"] = final_pd["cross_recommend_1"].map(_svc_label)
final_pd["rec2_name"] = final_pd["cross_recommend_2"].map(_svc_label)
final_pd["segment_name"] = final_pd["cluster_id"].map(_seg_label)

null_rec1 = final_pd["cross_recommend_1"].isna().sum()
print(f"✅ After gap-fill: {len(final_pd):,} users | null rec={null_rec1}")
print(final_pd["rec1_source"].value_counts().to_string())


# ─────────────────────────────────────────────────────────────────
# CELL 8 — Save ALL tables to SQLite
# ─────────────────────────────────────────────────────────────────
import sqlite3
import pandas as pd

# final_pd built in CELL 7C (ALS + gap-fill)
activity_pd = user_activity_df.toPandas()
stats_pd    = user_stats_df.toPandas()

print(f"✅ user_clusters      : {len(final_pd):,} rows")
print(f"✅ user_activity      : {len(activity_pd):,} rows")
print(f"✅ user_service_stats : {len(stats_pd):,} rows")

_db_dir = Path("data")
_db_dir.mkdir(parents=True, exist_ok=True)
db_path = str(_db_dir / "user_clusters.db")
conn    = sqlite3.connect(db_path)

# ── Table 1: user_clusters (main recommendation + cluster table) ──
_uc_dtypes = {
    "user_id":              "TEXT",
    "Name":                 "TEXT",
    "cluster_id":           "INTEGER",
    "active_service":       "TEXT",
    "cross_recommend_1":    "TEXT",
    "cross_recommend_2":    "TEXT",
    "rec1_score":           "REAL",
    "rec2_score":           "REAL",
    "rec1_source":          "TEXT",
    "rec2_source":          "TEXT",
    "user_display_name":    "TEXT",
    "active_service_name":  "TEXT",
    "rec1_name":            "TEXT",
    "rec2_name":            "TEXT",
    "segment_name":         "TEXT",
}
if "last_active_at" in final_pd.columns:
    _uc_dtypes["last_active_at"] = "TEXT"
for _extra in CFG["user_metadata"].get("pass_through_columns", []):
    if _extra in final_pd.columns:
        _uc_dtypes[_extra] = "TEXT"

final_pd.to_sql(
    "user_clusters", conn, if_exists="replace", index=False,
    dtype=_uc_dtypes,
)

# ── Table 2: user_activity (every COMPLETED event — powers activity feed) ──
activity_pd.to_sql(
    "user_activity", conn, if_exists="replace", index=False,
)

# ── Table 3: user_service_stats (per-user per-service counts — powers stats panel) ──
stats_pd.to_sql(
    "user_service_stats", conn, if_exists="replace", index=False,
    dtype={
        "user_id":           "TEXT",
        "process_type":      "TEXT",
        "interaction_count": "INTEGER",
    },
)

# ── Indexes ──────────────────────────────────────────────────────
index_stmts = [
    "CREATE INDEX IF NOT EXISTS idx_uc_uid  ON user_clusters(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_uc_cid  ON user_clusters(cluster_id)",
    "CREATE INDEX IF NOT EXISTS idx_uc_svc  ON user_clusters(active_service)",
    "CREATE INDEX IF NOT EXISTS idx_uc_rec1 ON user_clusters(cross_recommend_1)",
    "CREATE INDEX IF NOT EXISTS idx_uc_rec2 ON user_clusters(cross_recommend_2)",
    "CREATE INDEX IF NOT EXISTS idx_ua_uid  ON user_activity(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_ua_svc  ON user_activity(process_type)",
    "CREATE INDEX IF NOT EXISTS idx_ss_uid  ON user_service_stats(user_id)",
]
for stmt in index_stmts:
    conn.execute(stmt)
conn.commit()

# ── Verification ─────────────────────────────────────────────────
print("\n── Table row counts ──")
for tbl in ["user_clusters", "user_activity", "user_service_stats"]:
    n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"  {tbl:<24}: {n:,} rows")

print("\n── Cluster distribution ──")
dist = pd.read_sql_query(
    "SELECT cluster_id, COUNT(*) AS users FROM user_clusters GROUP BY cluster_id ORDER BY cluster_id",
    conn
)
print(dist.to_string())

print("\n── Null check (user_clusters) ──")
nulls = pd.read_sql_query("""
    SELECT
        SUM(CASE WHEN cluster_id        IS NULL THEN 1 ELSE 0 END) AS null_cluster,
        SUM(CASE WHEN active_service    IS NULL THEN 1 ELSE 0 END) AS null_active_svc,
        SUM(CASE WHEN cross_recommend_1 IS NULL THEN 1 ELSE 0 END) AS null_rec,
        SUM(CASE WHEN rec1_score         IS NULL THEN 1 ELSE 0 END) AS null_rec_score
    FROM user_clusters
""", conn)
print(nulls.to_string())

print("\n── Recommendation sources ──")
print(pd.read_sql_query("""
    SELECT rec1_source, COUNT(*) AS users
    FROM user_clusters
    GROUP BY rec1_source
    ORDER BY users DESC
""", conn).to_string())

print("\n── Sample user_clusters ──")
print(pd.read_sql_query("SELECT * FROM user_clusters LIMIT 5", conn).to_string())

print("\n── Sample user_activity ──")
print(pd.read_sql_query("SELECT * FROM user_activity LIMIT 5", conn).to_string())

print("\n── Sample user_service_stats ──")
print(pd.read_sql_query("SELECT * FROM user_service_stats LIMIT 5", conn).to_string())

conn.close()

print(f"\n✅ SQLite database written to: {Path(db_path).resolve()}")

try:
    from google.colab import files  # type: ignore
    files.download(db_path)
except ImportError:
    print("   (Not in Colab — open the path above for the web app.)")
print(f"\n✅ '{db_path}' downloaded — place it in your project's data/ folder")