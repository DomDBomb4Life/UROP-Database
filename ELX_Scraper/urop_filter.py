#!/usr/bin/env python3
"""
MIT UROP Database Filter Toolkit
=================================
Filter, search, and export your UROP database.

Pipeline approach: input DB → filter → output DB (chain multiple operations)

Usage:
  # List all keywords
  python3 urop_filter.py input.db --list-keywords

  # Filter to only UROPs
  python3 urop_filter.py input.db -o only_urops.db --type "Undergraduate Research (UROP)"

  # Search overview text for any of these terms
  python3 urop_filter.py input.db -o ml_urops.db --search "machine learning" "deep learning" "neural network"

  # Filter by keywords
  python3 urop_filter.py input.db -o robotics.db --keywords "robotics" "soft robotics" "robotics and automation"

  # Chain: first filter to UROPs, then search
  python3 urop_filter.py input.db -o step1.db --type "Undergraduate Research (UROP)"
  python3 urop_filter.py step1.db -o step2.db --search "machine learning" "LLM"

  # Export to JSON for an LLM
  python3 urop_filter.py input.db --to-json output.json
  python3 urop_filter.py input.db --to-json output.json --compact  # smaller, fewer fields
"""

import argparse
import json
import sqlite3
import shutil
import sys
from pathlib import Path


def copy_db(src: str, dst: str):
    """Copy a database file."""
    shutil.copy2(src, dst)
    # Make writable
    Path(dst).chmod(0o644)


def get_all_urop_ids(conn: sqlite3.Connection) -> set:
    """Get all UROP IDs in the database."""
    return {r[0] for r in conn.execute("SELECT id FROM urops")}


def get_ids_by_type(conn: sqlite3.Connection, types: list[str]) -> set:
    """Get UROP IDs matching any of the given primary_theme types."""
    placeholders = ",".join("?" for _ in types)
    # Check both primary_theme column and urop_themes table
    ids = set()
    # From main table primary_theme column
    for r in conn.execute(
        f"SELECT id FROM urops WHERE primary_theme IN ({placeholders})", types
    ):
        ids.add(r[0])
    # From themes table (catches secondary themes too)
    for r in conn.execute(
        f"SELECT urop_id FROM urop_themes WHERE theme IN ({placeholders})", types
    ):
        ids.add(r[0])
    return ids


def get_ids_by_keywords(conn: sqlite3.Connection, keywords: list[str]) -> set:
    """Get UROP IDs that have any of the given keywords (case-insensitive partial match)."""
    ids = set()
    for kw in keywords:
        for r in conn.execute(
            "SELECT urop_id FROM urop_keywords WHERE LOWER(keyword) LIKE ?",
            (f"%{kw.lower()}%",)
        ):
            ids.add(r[0])
    return ids


def get_ids_by_search(conn: sqlite3.Connection, terms: list[str]) -> set:
    """Get UROP IDs where any search term appears in title, tagline, overview, or prerequisites."""
    ids = set()
    for term in terms:
        pattern = f"%{term}%"
        for r in conn.execute("""
            SELECT id FROM urops
            WHERE title LIKE ? COLLATE NOCASE
               OR tagline LIKE ? COLLATE NOCASE
               OR overview LIKE ? COLLATE NOCASE
               OR prerequisites LIKE ? COLLATE NOCASE
        """, (pattern, pattern, pattern, pattern)):
            ids.add(r[0])
    return ids


def delete_except(conn: sqlite3.Connection, keep_ids: set):
    """Delete all UROPs NOT in keep_ids from all tables."""
    all_ids = get_all_urop_ids(conn)
    remove_ids = all_ids - keep_ids

    if not remove_ids:
        return

    # Delete in batches to avoid SQL variable limits
    remove_list = list(remove_ids)
    batch_size = 500
    for i in range(0, len(remove_list), batch_size):
        batch = remove_list[i:i + batch_size]
        placeholders = ",".join("?" for _ in batch)
        conn.execute(f"DELETE FROM urops WHERE id IN ({placeholders})", batch)
        for table in ["urop_keywords", "urop_terms", "urop_themes",
                       "urop_majors", "urop_years", "urop_payment"]:
            conn.execute(f"DELETE FROM {table} WHERE urop_id IN ({placeholders})", batch)

    conn.commit()
    conn.execute("VACUUM")


def list_keywords(conn: sqlite3.Connection):
    """Print all keywords with counts."""
    print(f"\n{'KEYWORD':<80} COUNT")
    print("─" * 90)
    for row in conn.execute(
        "SELECT keyword, COUNT(*) as cnt FROM urop_keywords GROUP BY LOWER(keyword) ORDER BY cnt DESC"
    ):
        print(f"  {row[0]:<78} {row[1]}")
    total = conn.execute("SELECT COUNT(DISTINCT keyword) FROM urop_keywords").fetchone()[0]
    print(f"\n  Total unique keywords: {total}")


def list_types(conn: sqlite3.Connection):
    """Print all theme types with counts."""
    print(f"\n{'TYPE':<50} COUNT (primary)  COUNT (any)")
    print("─" * 80)
    for row in conn.execute("""
        SELECT theme,
               SUM(CASE WHEN is_primary = 1 THEN 1 ELSE 0 END) as primary_cnt,
               COUNT(*) as total_cnt
        FROM urop_themes
        GROUP BY theme
        ORDER BY primary_cnt DESC
    """):
        print(f"  {row[0]:<48} {row[1]:<16} {row[2]}")


def db_summary(conn: sqlite3.Connection):
    """Print a quick summary."""
    total = conn.execute("SELECT COUNT(*) FROM urops").fetchone()[0]
    kw_count = conn.execute("SELECT COUNT(DISTINCT keyword) FROM urop_keywords").fetchone()[0]
    print(f"\n  Total UROPs: {total}")
    print(f"  Unique keywords: {kw_count}")
    print(f"  Departments: ", end="")
    depts = conn.execute(
        "SELECT department_name, COUNT(*) FROM urops WHERE department_name IS NOT NULL GROUP BY department_name ORDER BY COUNT(*) DESC LIMIT 8"
    ).fetchall()
    print(", ".join(f"{d[0]} ({d[1]})" for d in depts))


def to_json(conn: sqlite3.Connection, output_path: str, compact: bool = False):
    """Export database to JSON for LLM consumption."""
    urops = []

    for row in conn.execute("SELECT * FROM urops ORDER BY title"):
        cols = [d[0] for d in conn.execute("SELECT * FROM urops LIMIT 0").description]
        record = dict(zip(cols, row))
        uid = record["id"]

        # Remove raw_json and internal fields to keep it clean
        for drop_key in ["raw_json", "scraped_at", "constant_id", "lat", "lng"]:
            record.pop(drop_key, None)

        # Add related data
        record["keywords"] = [r[0] for r in conn.execute(
            "SELECT keyword FROM urop_keywords WHERE urop_id = ?", (uid,))]
        record["terms"] = [r[0] for r in conn.execute(
            "SELECT term FROM urop_terms WHERE urop_id = ?", (uid,))]
        record["themes"] = [r[0] for r in conn.execute(
            "SELECT theme FROM urop_themes WHERE urop_id = ?", (uid,))]
        record["eligible_majors"] = [r[0] for r in conn.execute(
            "SELECT major FROM urop_majors WHERE urop_id = ?", (uid,))]
        record["eligible_years"] = [r[0] for r in conn.execute(
            "SELECT year FROM urop_years WHERE urop_id = ?", (uid,))]
        record["payment_options"] = {r[0]: bool(r[1]) for r in conn.execute(
            "SELECT pay_type, selected FROM urop_payment WHERE urop_id = ?", (uid,))}

        if compact:
            # Strip down to the most useful fields for an LLM
            urops.append({
                "title": record["title"],
                "department": record.get("department_name"),
                "overview": record.get("overview"),
                "prerequisites": record.get("prerequisites"),
                "contact": record.get("contact_name"),
                "contact_email": record.get("contact_email"),
                "sponsor": record.get("sponsor_name"),
                # "hours_per_week": record.get("hours_per_week"),
                # "keywords": record["keywords"],
                # "terms": record["terms"],
                # "eligible_majors": record["eligible_majors"],
                "eligible_years": record["eligible_years"],
                # "payment": record["payment_options"],
                # "deadline": record.get("deadline_date"),
                # "start_date": record.get("start_date"),
                # "end_date": record.get("end_date"),
                # "is_remote": bool(record.get("is_remote")),
                # "city": record.get("city"),
            })
        else:
            urops.append(record)

    with open(output_path, "w") as f:
        json.dump(urops, f, indent=2, default=str)

    size_kb = Path(output_path).stat().st_size / 1024
    print(f"\n  Exported {len(urops)} UROPs to {output_path} ({size_kb:.0f} KB)")
    if size_kb > 500:
        print(f"  Tip: Use --compact to reduce size (better for LLM context windows)")


def main():
    parser = argparse.ArgumentParser(
        description="Filter and export MIT UROP database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.db --list-keywords
  %(prog)s input.db --list-types
  %(prog)s input.db -o urops_only.db --type "Undergraduate Research (UROP)"
  %(prog)s input.db -o ml.db --search "machine learning" "deep learning"
  %(prog)s input.db -o robotics.db --keywords "robotics" "soft robotics"
  %(prog)s input.db --to-json urops.json --compact
        """
    )

    parser.add_argument("input_db", help="Input SQLite database")
    parser.add_argument("-o", "--output-db", help="Output SQLite database (filtered copy)")

    # Listing operations (no output db needed)
    parser.add_argument("--list-keywords", action="store_true", help="List all keywords with counts")
    parser.add_argument("--list-types", action="store_true", help="List all theme types with counts")
    parser.add_argument("--summary", action="store_true", help="Print database summary")

    # Filter operations (need --output-db)
    parser.add_argument("--type", nargs="+", help="Keep only UROPs matching these primary theme types")
    parser.add_argument("--search", nargs="+", help="Keep UROPs where ANY term matches title/overview/prerequisites")
    parser.add_argument("--keywords", nargs="+", help="Keep UROPs that have ANY of these keywords")

    # Export
    parser.add_argument("--to-json", help="Export to JSON file")
    parser.add_argument("--compact", action="store_true", help="Compact JSON (fewer fields, smaller file)")

    args = parser.parse_args()

    if not Path(args.input_db).exists():
        print(f"Error: {args.input_db} not found")
        sys.exit(1)

    # --- Listing operations (read-only) ---
    if args.list_keywords or args.list_types or args.summary:
        conn = sqlite3.connect(f"file:{args.input_db}?mode=ro", uri=True)
        if args.list_keywords:
            list_keywords(conn)
        if args.list_types:
            list_types(conn)
        if args.summary:
            db_summary(conn)
        conn.close()
        if not (args.output_db or args.to_json):
            return

    # --- Filter operations ---
    has_filters = args.type or args.search or args.keywords
    if has_filters and not args.output_db:
        print("Error: filters require --output-db / -o to specify output file")
        sys.exit(1)

    if has_filters:
        # Copy input to output, then filter in-place
        copy_db(args.input_db, args.output_db)
        conn = sqlite3.connect(args.output_db)

        before = conn.execute("SELECT COUNT(*) FROM urops").fetchone()[0]

        # Collect matching IDs (union of all filters = OR logic)
        matching_ids = set()

        if args.type:
            type_ids = get_ids_by_type(conn, args.type)
            print(f"  Type filter matched: {len(type_ids)}")
            matching_ids |= type_ids

        if args.search:
            search_ids = get_ids_by_search(conn, args.search)
            print(f"  Search filter matched: {len(search_ids)}")
            matching_ids |= search_ids

        if args.keywords:
            kw_ids = get_ids_by_keywords(conn, args.keywords)
            print(f"  Keyword filter matched: {len(kw_ids)}")
            matching_ids |= kw_ids

        if not matching_ids:
            # If filters were applied but nothing matched, keep nothing
            # (but if no filters of a certain type, don't restrict)
            pass

        # If we're combining type filter WITH search/keyword, we want intersection
        # But the user said "any one of" so we do union within each filter type,
        # and if multiple filter types are used, we intersect them
        if args.type and (args.search or args.keywords):
            type_ids = get_ids_by_type(conn, args.type) if args.type else get_all_urop_ids(conn)
            other_ids = set()
            if args.search:
                other_ids |= get_ids_by_search(conn, args.search)
            if args.keywords:
                other_ids |= get_ids_by_keywords(conn, args.keywords)
            matching_ids = type_ids & other_ids if other_ids else type_ids
            print(f"  After intersecting type with search/keyword: {len(matching_ids)}")

        delete_except(conn, matching_ids)
        after = conn.execute("SELECT COUNT(*) FROM urops").fetchone()[0]
        print(f"\n  Filtered: {before} → {after} UROPs")
        print(f"  Saved to: {args.output_db}")

        conn.close()

    # --- JSON Export ---
    if args.to_json:
        # Export from output_db if we just filtered, otherwise from input_db
        source = args.output_db if args.output_db and Path(args.output_db).exists() else args.input_db
        conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        to_json(conn, args.to_json, compact=args.compact)
        conn.close()


if __name__ == "__main__":
    main()
