"""Shared service / segment labels (reads config/services.json)."""
import json
from pathlib import Path

_CONFIG = Path(__file__).parent.parent / "config" / "services.json"

_DEFAULT_CLUSTERS = {
    0: {"label": "Heavy Draftsman", "icon": "✍️", "desc": "Power user of Application Drafting — high-frequency document creator"},
    1: {"label": "Heavy Researcher", "icon": "🔬", "desc": "Deep legal research user — case laws, judgments, and court updates"},
    2: {"label": "Query Analyst", "icon": "💬", "desc": "Frequent Q&A user — legal definitions and quick lookups"},
}


def load_config():
    if _CONFIG.exists():
        return json.loads(_CONFIG.read_text(encoding="utf-8"))
    return {"core_services": [], "services": {}, "clusters": _DEFAULT_CLUSTERS}


def service_label(key, cfg=None):
    if not key:
        return "—"
    cfg = cfg or load_config()
    meta = cfg.get("services", {}).get(key, {})
    return meta.get("label", str(key).replace("_", " ").title())


def segment_label(cluster_id, cfg=None):
    cfg = cfg or load_config()
    clusters = cfg.get("clusters") or _DEFAULT_CLUSTERS
    c = clusters.get(int(cluster_id)) or clusters.get(str(int(cluster_id))) or {}
    return c.get("label", f"Cluster {cluster_id}")


def clean_activity_title(process_name, max_len=56):
    """Turn raw process_name into a short human-readable activity title."""
    if not process_name or (isinstance(process_name, float) and process_name != process_name):
        return None
    title = str(process_name).strip()
    for prefix in (
        "Async Research: ", "Async Query: ", "Async Synopsis: ",
        "Async Draft: ", "Async ", "Conversation Record Turn",
    ):
        if title.startswith(prefix):
            title = title[len(prefix) :].strip()
            break
    if len(title) > max_len:
        title = title[: max_len - 1].rstrip() + "…"
    return title or None


def default_user_display(user_id, activity_hint=None):
    short = (user_id or "")[:8]
    if activity_hint:
        return f"{activity_hint}"
    return f"User · {short}…" if short else "Unknown user"
