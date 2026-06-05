"""
Enrich user_clusters.db for the recommendation UI:
- Human-readable service & segment names
- User display titles from latest process_name in tracking CSV
- Fill missing rec1 / compute rec2 for every user
Run: python scripts/enrich_db.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared.labels import (
    clean_activity_title,
    default_user_display,
    load_config,
    segment_label,
    service_label,
)

DB_PATH = ROOT / "data" / "user_clusters.db"
CSV_PATH = ROOT / "colab" / "process_tracking_2026-06-02.csv"
CFG = load_config()
CORE = CFG.get("core_services", [])


def _pick_gap(candidates, used, chosen):
    for svc in candidates:
        if svc in CORE and svc not in used and svc not in chosen:
            return svc
    return None


def _usage_growth_recs(uid, stats, active_service):
    """Users who adopted every service — recommend lowest-usage upsell targets."""
    u = stats[stats["user_id"] == uid].sort_values("interaction_count")
    candidates = [s for s in u["process_type"].tolist() if s != active_service]
    if not candidates:
        candidates = u["process_type"].tolist()
    r1 = candidates[0] if len(candidates) > 0 else None
    r2 = candidates[1] if len(candidates) > 1 else None
    return r1, r2


def _fill_recs_row(row, used, peer_list, global_rank, stats):
    asvc = row["active_service"]
    peer = peer_list.get(asvc, global_rank)
    chosen = set()
    r1, s1, src1 = row.get("cross_recommend_1"), row.get("rec1_score"), row.get("rec1_source")
    r2, s2, src2 = row.get("cross_recommend_2"), row.get("rec2_score"), row.get("rec2_source")

    if pd.isna(r1) or not r1:
        r1 = _pick_gap(peer, used, chosen)
        if r1:
            s1, src1 = 72.0, "peer" if r1 in peer[:3] else "global"
    if pd.notna(r1) and r1:
        chosen.add(r1)

    if pd.isna(r2) or not r2:
        r2 = _pick_gap(peer, used, chosen) or _pick_gap(global_rank, used, chosen)
        if r2:
            s2, src2 = 58.0, "peer" if r2 in peer[:5] else "global"

    if (pd.isna(r1) or not r1) and len(used) >= len(CORE):
        r1, r2 = _usage_growth_recs(row["user_id"], stats, asvc)
        if r1:
            s1, src1 = 65.0, "usage"
        if r2:
            s2, src2 = 52.0, "usage"

    if pd.isna(r2) or not r2:
        for svc in global_rank:
            if svc not in chosen and svc != asvc:
                r2, s2, src2 = svc, 50.0, "global"
                break

    return r1, s1, src1, r2, s2, src2


def load_activity_hints():
    if not CSV_PATH.exists():
        return {}
    header = pd.read_csv(CSV_PATH, nrows=0).columns.tolist()
    usecols = [c for c in ("user_id", "process_name", "status", "created_at") if c in header]
    df = pd.read_csv(CSV_PATH, usecols=usecols)
    df["status"] = df["status"].astype(str).str.upper()
    df = df[df["status"] == "COMPLETED"].dropna(subset=["user_id"])
    if "created_at" in df.columns:
        df = df.sort_values("created_at")
    hints = {}
    for uid, grp in df.groupby("user_id"):
        last_name = grp["process_name"].iloc[-1] if "process_name" in grp.columns else None
        hint = clean_activity_title(last_name)
        if hint:
            hints[str(uid)] = hint
    return hints


def enrich():
    hints = load_activity_hints()
    conn = sqlite3.connect(DB_PATH)
    uc = pd.read_sql("SELECT * FROM user_clusters", conn)
    stats = pd.read_sql("SELECT * FROM user_service_stats", conn)

    # Load Name mappings to prevent user name loss on database rebuild/enrichment
    name_map = {}
    
    # 1. Try to read from existing user_clusters table before overwriting it
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(user_clusters)").fetchall()]
        if "Name" in cols:
            for uid, name in conn.execute("SELECT user_id, Name FROM user_clusters").fetchall():
                if name and str(name).strip() not in ("", "nan", "None"):
                    name_map[str(uid).strip()] = str(name).strip()
    except Exception:
        pass

    # 2. Try to read from reference database user_clusters_new.db (if present)
    ref_db = DB_PATH.parent / "user_clusters_new.db"
    if ref_db.exists():
        try:
            with sqlite3.connect(ref_db) as conn_ref:
                for uid, name in conn_ref.execute("SELECT user_id, Name FROM user_clusters").fetchall():
                    if name and str(name).strip() not in ("", "nan", "None"):
                        name_map[str(uid).strip()] = str(name).strip()
        except Exception:
            pass

    global_rank = (
        stats.groupby("process_type")["interaction_count"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    peer = (
        stats.merge(uc[["user_id", "active_service"]], on="user_id")
        .groupby(["active_service", "process_type"])["interaction_count"]
        .sum()
        .reset_index()
    )
    peer_lists = {
        asvc: grp.sort_values("interaction_count", ascending=False)["process_type"].tolist()
        for asvc, grp in peer.groupby("active_service")
    }
    used_by = stats.groupby("user_id")["process_type"].apply(lambda s: set(s.tolist())).to_dict()

    rows = []
    for _, row in uc.iterrows():
        uid = str(row["user_id"]).strip()
        used = used_by.get(uid, set())
        r1, s1, src1, r2, s2, src2 = _fill_recs_row(
            row, used, peer_lists, global_rank, stats
        )
        hint = hints.get(uid)
        
        # Determine user name
        name_val = row.get("Name")
        if pd.isna(name_val) or not name_val or str(name_val).strip() in ("", "nan", "None"):
            name_val = name_map.get(uid)
            
        rows.append({
            **row.to_dict(),
            "Name": name_val if name_val else None,
            "cross_recommend_1": r1,
            "rec1_score": float(s1) if pd.notna(s1) else None,
            "rec1_source": src1,
            "cross_recommend_2": r2,
            "rec2_score": float(s2) if pd.notna(s2) else None,
            "rec2_source": src2,
            "user_display_name": default_user_display(uid, hint),
            "active_service_name": service_label(row.get("active_service"), CFG),
            "rec1_name": service_label(r1, CFG),
            "rec2_name": service_label(r2, CFG),
            "segment_name": segment_label(row.get("cluster_id"), CFG),
        })

    out = pd.DataFrame(rows)
    out.to_sql("user_clusters", conn, if_exists="replace", index=False)

    # Attach process_name to activity rows for richer feed labels
    if CSV_PATH.exists() and "process_name" in pd.read_csv(CSV_PATH, nrows=0).columns:
        act = pd.read_sql("SELECT * FROM user_activity", conn)
        names = pd.read_csv(
            CSV_PATH,
            usecols=["user_id", "process_type", "status", "process_name", "created_at"],
        )
        names["status"] = names["status"].astype(str).str.upper()
        names = names[names["status"] == "COMPLETED"]
        names = names.rename(columns={"process_type": "process_type", "process_name": "process_name"})
        merged = act.merge(
            names.drop_duplicates(subset=["user_id", "process_type", "created_at"]),
            on=["user_id", "process_type", "created_at"],
            how="left",
        )
        if "process_name" not in merged.columns and "process_name_y" in merged.columns:
            merged["process_name"] = merged["process_name_y"]
        keep = list(dict.fromkeys(
            [c for c in ("user_id", "process_type", "status", "created_at", "process_name") if c in merged.columns]
        ))
        merged[keep].drop_duplicates().to_sql("user_activity", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ua_uid ON user_activity(user_id)")
    for stmt in [
        "CREATE INDEX IF NOT EXISTS idx_uc_uid ON user_clusters(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_uc_cid ON user_clusters(cluster_id)",
        "CREATE INDEX IF NOT EXISTS idx_uc_svc ON user_clusters(active_service)",
        "CREATE INDEX IF NOT EXISTS idx_uc_rec1 ON user_clusters(cross_recommend_1)",
        "CREATE INDEX IF NOT EXISTS idx_uc_rec2 ON user_clusters(cross_recommend_2)",
    ]:
        conn.execute(stmt)
    conn.commit()

    null1 = conn.execute(
        "SELECT COUNT(*) FROM user_clusters WHERE cross_recommend_1 IS NULL"
    ).fetchone()[0]
    null2 = conn.execute(
        "SELECT COUNT(*) FROM user_clusters WHERE cross_recommend_2 IS NULL"
    ).fetchone()[0]
    conn.close()
    print(f"Enriched {len(out):,} users -> {DB_PATH}")
    print(f"null rec1: {null1} | null rec2: {null2}")
    print(f"   sample: {out[['user_display_name','active_service_name','rec1_name','rec2_name']].head(3).to_string()}")


if __name__ == "__main__":
    enrich()
