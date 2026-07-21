import sqlite3

conn = sqlite3.connect("alerts.db")

tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()
print("Tables:", tables)

for table in tables:
    table_name = table[0]
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    column_names = [col[1] for col in columns]
    print(f"\nColumns in '{table_name}':")
    print(column_names)

conn.close()