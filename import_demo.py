import json
from pathlib import Path

from collector.db import connect, store_batch

data_file = Path("data/demo_200.jsonl")
db_file = Path("data/collector.sqlite")

records = []

with data_file.open("r", encoding="utf-8") as file:
    for line in file:
        if line.strip():
            record = json.loads(line)
            records.append(record)

conn = connect(db_file)

try:
    inserted = store_batch(
        conn,
        source="demo_channel",
        records=records,
        mode="demo"
    )

    total = conn.execute(
        "SELECT COUNT(*) FROM messages"
    ).fetchone()[0]

    print(f"New records inserted: {inserted}")
    print(f"Total records in SQLite: {total}")
finally:
    conn.close()