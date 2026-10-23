import json
"""SQLite storage. A fresh connection is opened per call, so it is safe to use from worker threads."""
import os
import re
import sqlite3
from datetime import datetime

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS manuals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    manufacturer TEXT DEFAULT '',
    model TEXT DEFAULT '',
    file_path TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS manual_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manual_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    text TEXT,
    page_image TEXT              -- rendered snapshot of the whole page (real manual content)
);
CREATE TABLE IF NOT EXISTS manual_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manual_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    image_path TEXT NOT NULL      -- embedded illustration extracted from the PDF
);
CREATE TABLE IF NOT EXISTS manual_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- this id is also the FAISS vector id
    manual_id INTEGER NOT NULL,
    page_number INTEGER,
    chunk_text TEXT NOT NULL,
    image_path TEXT,
    section TEXT
);
CREATE INDEX IF NOT EXISTS idx_pages_manual ON manual_pages(manual_id, page_number);
CREATE INDEX IF NOT EXISTS idx_images_manual ON manual_images(manual_id, page_number);
CREATE INDEX IF NOT EXISTS idx_chunks_manual ON manual_chunks(manual_id);
CREATE VIRTUAL TABLE IF NOT EXISTS manual_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    manual_id UNINDEXED,
    chunk_text,
    section,
    tokenize = 'unicode61'
);
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manual_id INTEGER,
    title TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    data_json TEXT,
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_chat_conv ON chat_messages(conversation_id);
CREATE TABLE IF NOT EXISTS component_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path TEXT,
    component_name TEXT,
    category TEXT,
    manufacturer TEXT,
    model TEXT,
    confidence TEXT,
    data_json TEXT,
    created_at TEXT
);
"""


def _connect():
    config.ensure_dirs()
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    try:
        conn.executescript(SCHEMA)
        try:
            conn.execute("ALTER TABLE conversations ADD COLUMN is_pinned INTEGER DEFAULT 0")
            conn.commit()
        except Exception:
            pass
        # Backfill any existing manual_chunks into FTS5
        conn.execute("""
            INSERT INTO manual_chunks_fts (chunk_id, manual_id, chunk_text, section)
            SELECT id, manual_id, chunk_text, section FROM manual_chunks
            WHERE id NOT IN (SELECT chunk_id FROM manual_chunks_fts)
        """)
        conn.commit()
    finally:
        conn.close()


def query(sql, args=()):
    conn = _connect()
    try:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def execute(sql, args=()):
    conn = _connect()
    try:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


# ---- writing ----------------------------------------------------------------
def add_manual(name, manufacturer, model, file_path):
    return execute(
        "INSERT INTO manuals (name, manufacturer, model, file_path, created_at) VALUES (?,?,?,?,?)",
        (name, manufacturer, model, file_path, datetime.now().isoformat(timespec="seconds")))


def add_pages(manual_id, rows):
    """rows: [(page_number, text, page_image_path)]"""
    conn = _connect()
    try:
        conn.executemany("INSERT INTO manual_pages (manual_id, page_number, text, page_image) VALUES (?,?,?,?)",
                         [(manual_id, p, t, img) for p, t, img in rows])
        conn.commit()
    finally:
        conn.close()


def add_images(manual_id, rows):
    """rows: [(page_number, image_path)]"""
    conn = _connect()
    try:
        conn.executemany("INSERT INTO manual_images (manual_id, page_number, image_path) VALUES (?,?,?)",
                         [(manual_id, p, path) for p, path in rows])
        conn.commit()
    finally:
        conn.close()


def add_chunks(manual_id, chunks):
    """Insert chunks and return their ids (used as FAISS vector ids)."""
    conn = _connect()
    ids = []
    try:
        for c in chunks:
            cur = conn.execute(
                "INSERT INTO manual_chunks (manual_id, page_number, chunk_text, image_path, section) "
                "VALUES (?,?,?,?,?)",
                (manual_id, c["page_number"], c["text"], c.get("image_path"), c.get("section", "")))
            cid = cur.lastrowid
            ids.append(cid)
            conn.execute(
                "INSERT INTO manual_chunks_fts (chunk_id, manual_id, chunk_text, section) "
                "VALUES (?,?,?,?)",
                (cid, manual_id, c["text"], c.get("section", "")))
        conn.commit()
    finally:
        conn.close()
    return ids


def delete_manual_rows(manual_id):
    """Delete all DB rows of a manual. Returns file paths that the caller should remove from disk."""
    m = get_manual(manual_id)
    files = []
    if m and m.get("file_path"):
        files.append(m["file_path"])
    files += [r["image_path"] for r in query("SELECT image_path FROM manual_images WHERE manual_id=?", (manual_id,))]
    files += [r["page_image"] for r in query("SELECT page_image FROM manual_pages WHERE manual_id=?", (manual_id,))
              if r["page_image"]]
    conn = _connect()
    try:
        conn.execute("DELETE FROM manual_chunks_fts WHERE manual_id=?", (manual_id,))
        for table in ("manual_chunks", "manual_images", "manual_pages"):
            conn.execute(f"DELETE FROM {table} WHERE manual_id=?", (manual_id,))
        conn.execute("DELETE FROM manuals WHERE id=?", (manual_id,))
        conn.commit()
    finally:
        conn.close()
    return files


def search_chunks_fts(manual_id, query_text, limit=10):
    """Keyword search using SQLite FTS5. Returns [(chunk_id, bm25_rank)] sorted best first.
    If manual_id is None, searches across all manuals."""
    tokens = re.findall(r"[A-Za-z0-9_]+", query_text)
    if not tokens:
        return []
    fts_query = " OR ".join(f'"{t}"' for t in tokens)
    conn = _connect()
    try:
        if manual_id is not None:
            rows = conn.execute(
                "SELECT chunk_id, rank FROM manual_chunks_fts "
                "WHERE manual_id=? AND manual_chunks_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (manual_id, fts_query, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT chunk_id, rank FROM manual_chunks_fts "
                "WHERE manual_chunks_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (fts_query, limit)
            ).fetchall()
        return [(int(r["chunk_id"]), float(r["rank"])) for r in rows]
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return []
    finally:
        conn.close()


# ---- reading ----------------------------------------------------------------
def list_manuals(search=""):
    like = f"%{search.strip()}%"
    return query(
        "SELECT m.*, (SELECT COUNT(*) FROM manual_pages p WHERE p.manual_id = m.id) AS page_count "
        "FROM manuals m WHERE m.name LIKE ? OR m.manufacturer LIKE ? OR m.model LIKE ? ORDER BY m.name",
        (like, like, like))


def get_manual(manual_id):
    rows = query("SELECT * FROM manuals WHERE id=?", (manual_id,))
    return rows[0] if rows else None


def get_chunks(ids):
    """Chunks for the given ids, in the same order as `ids`."""
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    by_id = {r["id"]: dict(r) for r in query(f"SELECT c.*, m.name as manual_name FROM manual_chunks c LEFT JOIN manuals m ON c.manual_id = m.id WHERE c.id IN ({marks})", tuple(ids))}
    return [by_id[i] for i in ids if i in by_id]


def get_all_chunks(manual_id):
    return query("SELECT * FROM manual_chunks WHERE manual_id=? ORDER BY id", (manual_id,))


def get_page_visual(manual_id, page):
    """Best picture for a manual page: (path, kind).
    kind = 'illustration' (largest embedded image) or 'page' (snapshot of the page) or None."""
    imgs = [r["image_path"] for r in query(
        "SELECT image_path FROM manual_images WHERE manual_id=? AND page_number=?", (manual_id, page))]
    imgs = [p for p in imgs if os.path.isfile(p)]
    if imgs:
        return max(imgs, key=os.path.getsize), "illustration"
    rows = query("SELECT page_image FROM manual_pages WHERE manual_id=? AND page_number=?", (manual_id, page))
    if rows and rows[0]["page_image"] and os.path.isfile(rows[0]["page_image"]):
        return rows[0]["page_image"], "page"
    return None, None


def _norm(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def find_manuals_by_hardware(hw):
    """Exact / partial model match (SQL LIKE first, then a punctuation-insensitive comparison)."""
    for candidate in (hw.get("model", ""), hw.get("part_number", "")):
        nc = _norm(candidate)
        if len(nc) < 2:
            continue
        rows = query("SELECT * FROM manuals WHERE model LIKE ? OR name LIKE ?",
                     (f"%{candidate.strip()}%", f"%{candidate.strip()}%"))
        if rows:
            return rows
        found = []
        for m in list_manuals():
            nm, nn = _norm(m["model"]), _norm(m["name"])
            if nc in nm or nc in nn or (len(nm) >= 3 and nm in nc):
                found.append(m)
        if found:
            return found
    return []


# ---- Chat History & Conversations -------------------------------------------
def create_conversation(manual_id=None, title="New Chat"):
    now = datetime.now().isoformat(timespec="seconds")
    return execute(
        "INSERT INTO conversations (manual_id, title, created_at, updated_at) VALUES (?,?,?,?)",
        (manual_id, title, now, now)
    )


def list_conversations():
    return query(
        """
        SELECT c.*, m.name as manual_name,
               (SELECT content FROM chat_messages WHERE conversation_id=c.id AND role='user' ORDER BY id ASC LIMIT 1) as first_question,
               (SELECT COUNT(*) FROM chat_messages WHERE conversation_id=c.id) as message_count
        FROM conversations c
        LEFT JOIN manuals m ON c.manual_id = m.id
        ORDER BY c.is_pinned DESC, c.updated_at DESC, c.id DESC
        """
    )


def get_conversation(conv_id):
    rows = query(
        """
        SELECT c.*, m.name as manual_name, m.file_path as manual_file_path
        FROM conversations c
        LEFT JOIN manuals m ON c.manual_id = m.id
        WHERE c.id=?
        """,
        (conv_id,)
    )
    return rows[0] if rows else None


def update_conversation_title(conv_id, title):
    execute("UPDATE conversations SET title=? WHERE id=?", (title, conv_id))


def update_conversation_manual(conv_id, manual_id):
    now = datetime.now().isoformat(timespec="seconds")
    execute("UPDATE conversations SET manual_id=?, updated_at=? WHERE id=?", (manual_id, now, conv_id))


def delete_conversation(conv_id):
    execute("DELETE FROM chat_messages WHERE conversation_id=?", (conv_id,))
    execute("DELETE FROM conversations WHERE id=?", (conv_id,))


def add_chat_message(conv_id, role, content, data=None):
    now = datetime.now().isoformat(timespec="seconds")
    data_str = json.dumps(data) if data is not None else None
    msg_id = execute(
        "INSERT INTO chat_messages (conversation_id, role, content, data_json, created_at) VALUES (?,?,?,?,?)",
        (conv_id, role, content, data_str, now)
    )
    execute("UPDATE conversations SET updated_at=? WHERE id=?", (now, conv_id))
    return msg_id


def get_chat_messages(conv_id):
    rows = query("SELECT * FROM chat_messages WHERE conversation_id=? ORDER BY id ASC", (conv_id,))
    results = []
    for r in rows:
        item = dict(r)
        if item.get("data_json"):
            try:
                item["data"] = json.loads(item["data_json"])
            except Exception:
                item["data"] = None
        else:
            item["data"] = None
        results.append(item)
    return results


def delete_chat_message(msg_id):
    execute("DELETE FROM chat_messages WHERE id=?", (msg_id,))


# ---- Recent Activity & Scans ------------------------------------------------
def add_component_scan(*args, **kwargs):
    now = datetime.now().isoformat(timespec="seconds")
    if len(args) == 2 and isinstance(args[1], dict):
        image_path = args[0]
        hw_data = args[1]
        name = (
            hw_data.get("product_name") or
            hw_data.get("model") or
            hw_data.get("hardware_type") or
            "Identified Component"
        )
        cat = hw_data.get("category") or hw_data.get("hardware_type") or "General"
        mfg = hw_data.get("manufacturer") or ""
        model = hw_data.get("model") or ""
        conf = str(hw_data.get("confidence") or "")
        data_str = json.dumps(hw_data)
    else:
        name = args[0] if len(args) > 0 else kwargs.get("name", "Component")
        cat = args[1] if len(args) > 1 else kwargs.get("category", "General")
        conf = str(args[2] if len(args) > 2 else kwargs.get("confidence", "0.9"))
        image_path = args[3] if len(args) > 3 else kwargs.get("image_path", "")
        details = args[4] if len(args) > 4 else kwargs.get("details", {})
        mfg = kwargs.get("manufacturer", "")
        model = kwargs.get("model", "")
        data_str = json.dumps(details) if isinstance(details, dict) else str(details or "")

    return execute(
        "INSERT INTO component_scans (image_path, component_name, category, manufacturer, model, confidence, data_json, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (image_path, name, cat, mfg, model, conf, data_str, now)
    )


def list_component_scans(limit=10):
    rows = query("SELECT * FROM component_scans ORDER BY id DESC LIMIT ?", (limit,))
    results = []
    for r in rows:
        item = dict(r)
        item["scanned_at"] = item.get("created_at") or ""
        if item.get("data_json"):
            try:
                item["data"] = json.loads(item["data_json"])
            except Exception:
                item["data"] = None
        else:
            item["data"] = None
        results.append(item)
    return results


def delete_component_scan(scan_id):
    execute("DELETE FROM component_scans WHERE id=?", (scan_id,))


def pin_conversation(conv_id, is_pinned=1):
    execute("UPDATE conversations SET is_pinned=? WHERE id=?", (1 if is_pinned else 0, conv_id))
