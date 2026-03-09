#!/usr/bin/env python3
"""
merge_emails.py
---------------
Merges two urop_emails.json files into one.
Deduplicates by recipient email address (keeps the version from file A if conflict).
Reassigns sequential IDs.

Usage:
    python merge_emails.py a.json b.json output.json
"""
import json, argparse, sys

def main():
    p = argparse.ArgumentParser(description="Merge two urop_emails.json files")
    p.add_argument("a", help="First email JSON (priority on conflicts)")
    p.add_argument("b", help="Second email JSON")
    p.add_argument("output", help="Output merged JSON")
    p.add_argument("--keep", choices=["a", "b", "both"], default="a",
                   help="On duplicate to.email: keep 'a' (default), 'b', or 'both'")
    args = p.parse_args()

    with open(args.a) as f:
        da = json.load(f)
    with open(args.b) as f:
        db = json.load(f)

    emails_a = da.get("emails", [])
    emails_b = db.get("emails", [])

    seen_emails = set()
    merged = []
    dupes = 0

    # Add all from A first
    for e in emails_a:
        addr = e["to"]["email"] if isinstance(e.get("to"), dict) else e.get("to_email", "")
        if args.keep == "both" or addr not in seen_emails:
            merged.append(e)
            seen_emails.add(addr)

    # Add from B, checking for duplicates
    for e in emails_b:
        addr = e["to"]["email"] if isinstance(e.get("to"), dict) else e.get("to_email", "")
        if addr in seen_emails:
            dupes += 1
            if args.keep == "b":
                # Replace the A version
                merged = [m for m in merged if (m["to"]["email"] if isinstance(m.get("to"), dict) else m.get("to_email", "")) != addr]
                merged.append(e)
            elif args.keep == "both":
                merged.append(e)
            # else keep=a, skip
        else:
            merged.append(e)
            seen_emails.add(addr)

    # Reassign sequential IDs
    for i, e in enumerate(merged):
        e["id"] = i + 1

    # Build output with metadata from A as base
    meta_a = da.get("metadata", {})
    output = {
        "metadata": {
            "sender": meta_a.get("sender", {}),
            "policy_version": meta_a.get("policy_version", "v3"),
            "total_emails": len(merged),
            "total_recipients": len(set(
                e["to"]["email"] if isinstance(e.get("to"), dict) else e.get("to_email", "")
                for e in merged
            )),
            "total_batches": len(set(e.get("batch_id", "") for e in merged)),
            "merged_from": [args.a, args.b],
        },
        "emails": merged,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Merged: {len(emails_a)} + {len(emails_b)} → {len(merged)} emails")
    print(f"Duplicates found: {dupes} (policy: keep={args.keep})")
    print(f"Unique recipients: {output['metadata']['total_recipients']}")
    print(f"Written to {args.output}")

if __name__ == "__main__":
    main()
