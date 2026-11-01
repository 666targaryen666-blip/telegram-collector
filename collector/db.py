import sqlite3
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS messages (
  source TEXT NOT NULL,
  message_id INTEGER NOT NULL,
  author TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  date TEXT NOT NULL,
  text TEXT NOT NULL,
  media_type TEXT,
  collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (source, message_id)
);
CREATE TABLE IF NOT EXISTS cursors (
  source TEXT PRIMARY KEY,
  last_id INTEGER NOT NULL DEFAULT 0,
  backfill_before_id INTEGER,
  backfill_complete INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  mode TEXT NOT NULL,
  inserted INTEGER NOT NULL,
  status TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''

def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn

def get_cursor(conn, source):
    conn.execute('INSERT OR IGNORE INTO cursors(source) VALUES (?)', (source,))
    conn.commit()
    return conn.execute('SELECT last_id,backfill_before_id,backfill_complete FROM cursors WHERE source=?', (source,)).fetchone()

def store_batch(conn, source, records, mode, next_cursor=None, complete=False):
    inserted = 0
    with conn:
        for r in records:
            cur = conn.execute('''INSERT OR IGNORE INTO messages
                (source,message_id,author,url,date,text,media_type)
                VALUES (:source,:message_id,:author,:url,:date,:text,:media_type)''', r)
            inserted += cur.rowcount
        if mode == 'new' and next_cursor is not None:
            conn.execute('UPDATE cursors SET last_id=MAX(last_id, ?) WHERE source=?', (next_cursor,source))
        if mode == 'backfill':
            conn.execute('UPDATE cursors SET backfill_before_id=?, backfill_complete=? WHERE source=?',
                         (next_cursor, int(complete), source))
        conn.execute('INSERT INTO runs(source,mode,inserted,status) VALUES (?,?,?,?)',
                     (source,mode,inserted,'ok'))
    return inserted
