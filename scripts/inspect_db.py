import sqlite3
from pathlib import Path

conn = sqlite3.connect(Path(__file__).parent.parent / "data" / "user_clusters.db")
for (tbl,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print("===", tbl, "===")
    for row in conn.execute(f"PRAGMA table_info({tbl})"):
        print(" ", row[1], row[2])
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({tbl})")]
    for r in conn.execute(f"SELECT * FROM {tbl} LIMIT 2"):
        print(" ", dict(zip(cols, r)))
print("\nnull recs:", conn.execute(
    "SELECT COUNT(*) FROM user_clusters WHERE cross_recommend_1 IS NULL"
).fetchone())
print("rec sources:", conn.execute(
    "SELECT rec1_source, COUNT(*) FROM user_clusters GROUP BY rec1_source"
).fetchall())
conn.close()
