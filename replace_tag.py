#!/usr/bin/env python3
"""
replace_tag.py
--------------
Reads urop_emails.json, replaces the subject-line tag in every email
and updates metadata.sender.tag to match.

Usage:
    python replace_tag.py input.json output.json --old "--UROP--" --new "-UROP-"
    python replace_tag.py urop_emails.json urop_emails_fixed.json   # uses defaults
"""
import json, argparse, sys

def main():
    p = argparse.ArgumentParser(description="Replace email subject tag")
    p.add_argument("input", help="Input JSON path")
    p.add_argument("output", help="Output JSON path")
    p.add_argument("--old", default="--UROP--", help="Tag to find (default: --UROP--)")
    p.add_argument("--new", default="-UROP-", help="Replacement tag (default: -UROP-)")
    args = p.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    changed = 0
    for e in data.get("emails", []):
        old_subj = e.get("subject", "")
        new_subj = old_subj.replace(args.old, args.new)
        if new_subj != old_subj:
            e["subject"] = new_subj
            changed += 1

    # Update metadata tag if present
    if "metadata" in data and "sender" in data["metadata"]:
        data["metadata"]["sender"]["tag"] = args.new
    if "metadata" in data and "tag" in data["metadata"]:
        data["metadata"]["tag"] = args.new

    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Replaced '{args.old}' → '{args.new}' in {changed}/{len(data.get('emails',[]))} subjects")
    print(f"Written to {args.output}")

if __name__ == "__main__":
    main()
