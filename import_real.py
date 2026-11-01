import json
import sqlite3
from pathlib import Path

SOURCE = Path("data/noel_reports_real.jsonl")
DATABASE = Path("data/noel_reports.sqlite")

if not SOURCE.exists():
    raise SystemExit(f"Не знайдено файл: {SOURCE}")

DATABASE.parent.mkdir(parents=True, exist_ok=True)

connection = sqlite3.connect(DATABASE)

try:
    # Така сама структура, як у нашому основному проєкті.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            source TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            date TEXT NOT NULL,
            text TEXT NOT NULL,
            media_type TEXT,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source, message_id)
        )
    """)

    inserted = 0

    with SOURCE.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            cursor = connection.execute("""
                INSERT OR IGNORE INTO messages
                (source, message_id, author, url, date, text, media_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record["source"],
                record["message_id"],
                record["author"],
                record["url"],
                record["date"],
                record["text"],
                record.get("media_type"),
            ))

            inserted += cursor.rowcount

    connection.commit()

    total = connection.execute(
        "SELECT COUNT(*) FROM messages"
    ).fetchone()[0]

    print("Додано нових записів:", inserted)
    print("Усього повідомлень у SQLite:", total)
    print("База:", DATABASE)

finally:
    connection.close()