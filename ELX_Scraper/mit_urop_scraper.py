#!/usr/bin/env python3
"""
MIT ELX UROP Scraper
====================
Fetches all UROP listings from the MIT ELO API and stores detailed info in a SQLite database.

Usage:
  1. Log into https://elx.mit.edu/ in your browser
  2. Open DevTools → Network tab → find any request to api.mit.edu
  3. Copy the Bearer token from the Authorization header
  4. Run:  
  python3 mit_urop_scraper.py --token "eyJraWQiOiJOblE3OEhrVzJCVUdBOFwvQm5YUzA3dGc1bUJrd3lHTHNBSGl5RGFDZzEzbz0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJjYjVhOTlhYy0wZjc4LTQ4Y2ItOWM2Mi0zZWI4MTY3MDQwMWEiLCJjb2duaXRvOmdyb3VwcyI6WyJ1cy1lYXN0LTFfYkN1NkJVOGQyX1RvdWNoc3RvbmUiXSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfYkN1NkJVOGQyIiwidmVyc2lvbiI6MiwiY2xpZW50X2lkIjoiN2w4a2szNGtqbnRwdDB1ZmcwZmtpbGJ1dWoiLCJ0b2tlbl91c2UiOiJhY2Nlc3MiLCJzY29wZSI6ImRpZ2l0YWwtaWRcL3VzZXIgb3BlbmlkIHByb2ZpbGUgZWxvXC91c2VyIiwiYXV0aF90aW1lIjoxNzcyODA5NzIwLCJleHAiOjE3NzI4OTYxMjAsImlhdCI6MTc3MjgwOTcyMCwianRpIjoiOTY4MjExODItOGUxNy00ODkwLWI5M2UtOWQxZWJlNWVlZWU0IiwidXNlcm5hbWUiOiJUb3VjaHN0b25lX21pdF9iYWNoQG1pdC5lZHUifQ.B2dUOv2fBEJuNxh5kHdTBLq2HneCE55fmc-F5TUI8kDaCQEHiZXaR6M2KFscTKV1L-VEvaW12aW0jyQTSV0ABGJ7oGWU-ItuxEXPcZ8edVX8gFVVXfxuFb17RCFvrt1-A4vKPibb4Nj7oI5PkfG_FAyyPSBxU3gvXKc9TY9eFS8PY0J4x1piHQMzIUuYnGqwLukBr1gQlgmafBRwGPzxNhL9J6KnCEUR-oCWhmfaHNmAxboBv73J4ljber3ytTYoqsqaPpoYA6Lv0NeTQZNl38C_DTKPRr-_jKesH-OdjoUw6c-jfxIkj-kVExUBNJHMG_zCC96bQ4TM6JAibl1org"

The token expires after ~24 hours, so you'll need a fresh one each session.
"""

import argparse
import json
import sqlite3
import time
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "https://api.mit.edu/elo-v2"
LIST_ENDPOINT = f"{BASE_URL}/opportunity"
DETAIL_ENDPOINT = f"{BASE_URL}/opportunity"  # + /{id}
DB_PATH = "urops.db"
DELAY_BETWEEN_REQUESTS = 0.3  # seconds, be polite

HEADERS_TEMPLATE = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://elx.mit.edu",
    "referer": "https://elx.mit.edu/",
}


# ── Database Setup ────────────────────────────────────────────────────────────
def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS urops (
        id                          TEXT PRIMARY KEY,
        constant_id                 TEXT,
        title                       TEXT NOT NULL,
        tagline                     TEXT,
        overview                    TEXT,
        prerequisites               TEXT,
        safety_considerations       TEXT,
        costs                       TEXT,
        website_url                 TEXT,
        external_application_url    TEXT,

        -- Department & People
        department_id               TEXT,
        department_name             TEXT,
        contact_name                TEXT,
        contact_krb                 TEXT,
        contact_email               TEXT,
        sponsor_name                TEXT,
        sponsor_krb                 TEXT,

        -- Classification
        primary_theme               TEXT,
        status                      TEXT,
        hours_per_week              TEXT,
        funding_source              TEXT,

        -- Dates
        deadline_date               TEXT,
        start_date                  TEXT,
        end_date                    TEXT,
        opportunity_start_date      TEXT,
        opportunity_end_date        TEXT,

        -- Location
        city                        TEXT,
        state                       TEXT,
        country                     TEXT,
        lat                         REAL,
        lng                         REAL,
        is_remote                   INTEGER,

        -- Flags
        has_external_application    INTEGER,
        has_deadline                INTEGER,
        has_prerequisites           INTEGER,
        work_authorization_required INTEGER,
        financial_aid_available     INTEGER,

        -- Metadata
        created_on                  TEXT,
        created_by                  TEXT,
        updated_on                  TEXT,
        approved_on                 TEXT,

        -- Raw JSON backup
        raw_json                    TEXT,

        -- Scrape tracking
        scraped_at                  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS urop_keywords (
        urop_id     TEXT NOT NULL,
        keyword_id  INTEGER,
        keyword     TEXT NOT NULL,
        FOREIGN KEY (urop_id) REFERENCES urops(id),
        UNIQUE(urop_id, keyword_id)
    );

    CREATE TABLE IF NOT EXISTS urop_terms (
        urop_id     TEXT NOT NULL,
        term_id     INTEGER,
        term        TEXT NOT NULL,
        FOREIGN KEY (urop_id) REFERENCES urops(id),
        UNIQUE(urop_id, term_id)
    );

    CREATE TABLE IF NOT EXISTS urop_themes (
        urop_id     TEXT NOT NULL,
        theme_id    INTEGER,
        theme       TEXT NOT NULL,
        is_primary  INTEGER DEFAULT 0,
        FOREIGN KEY (urop_id) REFERENCES urops(id),
        UNIQUE(urop_id, theme_id)
    );

    CREATE TABLE IF NOT EXISTS urop_majors (
        urop_id     TEXT NOT NULL,
        major_id    INTEGER,
        major       TEXT NOT NULL,
        FOREIGN KEY (urop_id) REFERENCES urops(id),
        UNIQUE(urop_id, major_id)
    );

    CREATE TABLE IF NOT EXISTS urop_years (
        urop_id     TEXT NOT NULL,
        year_id     INTEGER,
        year        TEXT NOT NULL,
        FOREIGN KEY (urop_id) REFERENCES urops(id),
        UNIQUE(urop_id, year_id)
    );

    CREATE TABLE IF NOT EXISTS urop_payment (
        urop_id     TEXT NOT NULL,
        pay_type    TEXT NOT NULL,
        selected    INTEGER,
        value       TEXT,
        FOREIGN KEY (urop_id) REFERENCES urops(id),
        UNIQUE(urop_id, pay_type)
    );

    -- Useful indexes
    CREATE INDEX IF NOT EXISTS idx_urops_dept ON urops(department_id);
    CREATE INDEX IF NOT EXISTS idx_urops_deadline ON urops(deadline_date);
    CREATE INDEX IF NOT EXISTS idx_urops_status ON urops(status);
    CREATE INDEX IF NOT EXISTS idx_keywords_text ON urop_keywords(keyword);
    CREATE INDEX IF NOT EXISTS idx_majors_text ON urop_majors(major);
    """)
    conn.commit()
    return conn


# ── Insert Logic ──────────────────────────────────────────────────────────────
def safe_get(d, *keys, default=None):
    """Safely navigate nested dicts."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default


def insert_detail(conn: sqlite3.Connection, item: dict):
    """Insert a fully-detailed UROP record."""
    cur = conn.cursor()

    loc = item.get("location") or {}
    coords = loc.get("coordinates") or {}

    cur.execute("""
        INSERT OR REPLACE INTO urops VALUES (
            ?,?,?,?,?,?,?,?,?,?,
            ?,?,?,?,?,?,?,
            ?,?,?,?,
            ?,?,?,?,?,
            ?,?,?,?,?,?,
            ?,?,?,?,?,
            ?,?,?,?,
            ?,
            datetime('now')
        )
    """, (
        item["id"],
        item.get("constant_id"),
        safe_get(item, "texts", "title"),
        safe_get(item, "texts", "tagline"),
        safe_get(item, "texts", "overview"),
        safe_get(item, "texts", "prerequisites"),
        safe_get(item, "texts", "safety_considerations"),
        safe_get(item, "texts", "costs"),
        safe_get(item, "texts", "website_url"),
        safe_get(item, "texts", "external_application_url"),

        safe_get(item, "department", "id"),
        safe_get(item, "department", "text"),
        safe_get(item, "contact", "text"),
        safe_get(item, "contact", "krb_name"),
        item.get("contact_email"),
        safe_get(item, "sponsor", "text"),
        safe_get(item, "sponsor", "krb_name"),

        safe_get(item, "primary_theme", "text"),
        safe_get(item, "status", "text"),
        safe_get(item, "hours_per_week", "text"),
        safe_get(item, "funding", "text"),

        item.get("deadline_date"),
        item.get("start_date"),
        item.get("end_date"),
        item.get("opportunity_start_date"),
        item.get("opportunity_end_date"),

        loc.get("city"),
        safe_get(loc, "state", "text"),
        safe_get(loc, "country", "text"),
        float(coords["lat"]) if coords.get("lat") else None,
        float(coords["lng"]) if coords.get("lng") else None,
        1 if item.get("is_remote") else 0,

        1 if item.get("has_external_application") else 0,
        1 if item.get("has_deadline") else 0,
        1 if item.get("has_prerequisites") else 0,
        1 if item.get("work_authorization_required") else 0,
        1 if item.get("financial_aid_available") else 0,

        item.get("created_on"),
        item.get("created_by"),
        item.get("updated_on"),
        item.get("approved_on"),

        json.dumps(item),
    ))

    uid = item["id"]

    # Keywords
    for kw in (item.get("keywords") or []):
        cur.execute("INSERT OR IGNORE INTO urop_keywords VALUES (?,?,?)",
                    (uid, kw.get("id"), kw.get("text", "").strip()))

    # Terms
    for t in (item.get("terms") or []):
        cur.execute("INSERT OR IGNORE INTO urop_terms VALUES (?,?,?)",
                    (uid, t.get("id"), t.get("text")))

    # Themes
    pt = item.get("primary_theme")
    if pt:
        cur.execute("INSERT OR IGNORE INTO urop_themes VALUES (?,?,?,?)",
                    (uid, pt.get("id"), pt.get("text"), 1))
    for t in (item.get("themes") or []):
        cur.execute("INSERT OR IGNORE INTO urop_themes VALUES (?,?,?,?)",
                    (uid, t.get("id"), t.get("text"), 0))

    # Majors
    for m in (item.get("student_majors") or []):
        cur.execute("INSERT OR IGNORE INTO urop_majors VALUES (?,?,?)",
                    (uid, m.get("id"), m.get("text", "").strip()))

    # Years
    for y in (item.get("student_years") or []):
        cur.execute("INSERT OR IGNORE INTO urop_years VALUES (?,?,?)",
                    (uid, y.get("id"), y.get("text")))

    # Payment
    for p in (item.get("payment") or []):
        cur.execute("INSERT OR IGNORE INTO urop_payment VALUES (?,?,?,?)",
                    (uid, p.get("name"), 1 if p.get("selected") else 0, str(p.get("value", ""))))


# ── API Fetching ──────────────────────────────────────────────────────────────
def make_session(token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS_TEMPLATE)
    s.headers["authorization"] = f"Bearer {token}"
    return s


def fetch_all_listings(session: requests.Session) -> list[dict]:
    """Fetch the listing page (returns summary records)."""
    # Try without search_string to get all, also try with empty params
    # The API seems to return all live UROPs when called with no filters
    print("Fetching UROP listing...")
    resp = session.get(LIST_ENDPOINT, params={})
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, list):
        print(f"  Got {len(data)} listings")
        return data
    elif isinstance(data, dict) and "results" in data:
        print(f"  Got {len(data['results'])} listings (paginated)")
        return data["results"]
    else:
        print(f"  Unexpected response type: {type(data)}")
        return []


def fetch_detail(session: requests.Session, urop_id: str) -> dict | None:
    """Fetch the full detail for a single UROP."""
    url = f"{DETAIL_ENDPOINT}/{urop_id}"
    try:
        resp = session.get(url)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"  ERROR fetching {urop_id}: {e}")
        return None


def scrape_all(token: str, db_path: str, from_json: str = None):
    """Main scrape workflow."""
    conn = init_db(db_path)
    session = make_session(token)

    # Step 1: Get all UROP IDs from the listing
    if from_json:
        print(f"Loading listings from {from_json}...")
        with open(from_json) as f:
            listings = json.load(f)
        print(f"  Loaded {len(listings)} listings from file")
    else:
        listings = fetch_all_listings(session)

    ids = [item["id"] for item in listings]
    print(f"\nTotal UROPs to fetch details for: {len(ids)}")

    # Step 2: Fetch detail for each UROP
    success = 0
    failed = 0
    for i, uid in enumerate(ids):
        # Check if we already have this one with full detail
        existing = conn.execute(
            "SELECT contact_name FROM urops WHERE id = ?", (uid,)
        ).fetchone()
        if existing and existing[0] is not None:
            print(f"  [{i+1}/{len(ids)}] Skipping {uid} (already scraped)")
            success += 1
            continue

        print(f"  [{i+1}/{len(ids)}] Fetching {uid}...", end=" ")
        detail = fetch_detail(session, uid)

        if detail:
            insert_detail(conn, detail)
            conn.commit()
            title = safe_get(detail, "texts", "title") or "?"
            print(f"✓ {title[:60]}")
            success += 1
        else:
            failed += 1

        time.sleep(DELAY_BETWEEN_REQUESTS)

    conn.commit()
    print(f"\nDone! {success} succeeded, {failed} failed")
    print(f"Database saved to: {db_path}")

    # Print summary
    print_summary(conn)
    conn.close()


def print_summary(conn: sqlite3.Connection):
    """Print a quick summary of the database."""
    print("\n" + "=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    total = conn.execute("SELECT COUNT(*) FROM urops").fetchone()[0]
    print(f"Total UROPs: {total}")

    print("\nBy Department:")
    for row in conn.execute("""
        SELECT department_name, COUNT(*) as cnt
        FROM urops
        WHERE department_name IS NOT NULL
        GROUP BY department_name
        ORDER BY cnt DESC
        LIMIT 15
    """):
        print(f"  {row[0]}: {row[1]}")

    print("\nTop Keywords:")
    for row in conn.execute("""
        SELECT keyword, COUNT(*) as cnt
        FROM urop_keywords
        GROUP BY keyword
        ORDER BY cnt DESC
        LIMIT 15
    """):
        print(f"  {row[0]}: {row[1]}")

    print("\nBy Term:")
    for row in conn.execute("""
        SELECT term, COUNT(*) as cnt
        FROM urop_terms
        GROUP BY term
        ORDER BY cnt DESC
    """):
        print(f"  {row[0]}: {row[1]}")

    print("\nUpcoming Deadlines:")
    for row in conn.execute("""
        SELECT title, deadline_date, department_name
        FROM urops
        WHERE deadline_date IS NOT NULL AND deadline_date >= date('now')
        ORDER BY deadline_date
        LIMIT 10
    """):
        print(f"  {row[1]} | {row[0][:50]} ({row[2]})")

    paid = conn.execute("""
        SELECT COUNT(DISTINCT urop_id) FROM urop_payment
        WHERE pay_type = 'hourly_wage' AND selected = 1
    """).fetchone()[0]
    credit = conn.execute("""
        SELECT COUNT(DISTINCT urop_id) FROM urop_payment
        WHERE pay_type = 'credit' AND selected = 1
    """).fetchone()[0]
    print(f"\nPaid (hourly): {paid} | Credit available: {credit}")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MIT ELX UROP Scraper")
    parser.add_argument("--token", "-t", required=True,
                        help="Bearer token from your authenticated ELX session")
    parser.add_argument("--db", default=DB_PATH,
                        help=f"SQLite database path (default: {DB_PATH})")
    parser.add_argument("--from-json", default=None,
                        help="Load listing IDs from a local JSON file instead of fetching")
    parser.add_argument("--summary-only", action="store_true",
                        help="Just print summary of existing DB, don't scrape")
    args = parser.parse_args()

    if args.summary_only:
        conn = sqlite3.connect(args.db)
        print_summary(conn)
        conn.close()
    else:
        scrape_all(args.token, args.db, args.from_json)
