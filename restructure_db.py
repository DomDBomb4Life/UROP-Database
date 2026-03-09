#!/usr/bin/env python3
"""
restructure_db.py
-----------------
Reads the old master_urop_database.json and urop_emails.json,
outputs cleaned versions with better structure.

Usage:
    python restructure_db.py

Reads from /mnt/user-data/uploads/
Writes to /mnt/user-data/outputs/
"""
import json

# ================================================================
# 1. Restructure master_urop_database.json
# ================================================================
with open("/mnt/user-data/uploads/master_urop_database.json") as f:
    old_master = json.load(f)

# Build a professor lookup keyed by batch_id-friendly slug
def slugify(name):
    return name.lower().replace(" ", "_").replace(".", "").replace("(", "").replace(")", "")

# New structure: labs as the top-level organizing unit
labs = {}
for prof in old_master["part1_professor_database"]:
    # Create a lab entry per research group, or one per professor if no groups
    for rg in prof.get("research_groups", [{}]):
        lab_id = slugify(prof["name"].split()[-1]) + "_" + slugify(rg.get("name", "lab").split("(")[0].strip().split()[0])
        labs[lab_id] = {
            "lab_id": lab_id,
            "lab_name": rg.get("name", prof["name"] + " Lab"),
            "lab_url": rg.get("url", ""),
            "lab_focus": rg.get("focus", ""),
            "pi": {
                "name": prof["name"],
                "email": prof["email"],
                "title": prof["title"],
                "affiliations": prof["affiliations"],
            },
            "category": prof["category"],
            "priority": prof["priority"],
            "research_summary": prof["research_summary"],
            "links": prof.get("links", {}),
            "key_papers": prof.get("key_papers_2024_2025", []),
            "urop_relevance": prof.get("urop_relevance", ""),
            "elx_urops": [],      # filled below
            "grad_students": [],   # to be populated manually or via scraping
        }

# Attach ELX UROPs to their labs via overlaps
for overlap in old_master.get("overlaps", []):
    prof_name = overlap["professor"]
    # Find matching lab
    for lid, lab in labs.items():
        if lab["pi"]["name"] == prof_name:
            # Find full ELX entry
            for elx in old_master.get("part2_kept_elx_urops", []):
                if elx["title"] == overlap["elx_urop_title"]:
                    lab["elx_urops"].append({
                        "title": elx["title"],
                        "department": elx.get("department", ""),
                        "contact": elx.get("contact", ""),
                        "contact_email": elx.get("contact_email", ""),
                        "eligible_years": elx.get("eligible_years", []),
                        "overview": elx.get("overview", "")[:500] + "..." if len(elx.get("overview","")) > 500 else elx.get("overview", ""),
                        "prerequisites": elx.get("prerequisites", ""),
                    })
            break

# Handle ELX-only entries
elx_only_labs = {}
for entry in old_master.get("elx_only_entries", []):
    elx_id = slugify(entry.get("sponsor", "unknown")) + "_elx"
    elx_only_labs[elx_id] = {
        "lab_id": elx_id,
        "lab_name": entry.get("title", ""),
        "lab_url": "",
        "lab_focus": "",
        "pi": {
            "name": entry.get("sponsor", "Unknown"),
            "email": "",
            "title": "",
            "affiliations": [entry.get("department", "")],
        },
        "category": "ELX-only",
        "priority": "MEDIUM",
        "research_summary": "",
        "links": {},
        "key_papers": [],
        "urop_relevance": "Has active ELX listing",
        "elx_urops": [{
            "title": entry.get("title", ""),
            "department": entry.get("department", ""),
            "contact": entry.get("contact", ""),
            "contact_email": entry.get("contact_email", ""),
            "eligible_years": entry.get("eligible_years", []),
            "overview": entry.get("overview", "")[:500],
            "prerequisites": entry.get("prerequisites", ""),
        }],
        "grad_students": [],
    }

new_master = {
    "metadata": {
        "description": "MIT LLM/AI Agents UROP Lab Database",
        "criteria_kept": old_master["metadata"]["criteria_kept"],
        "criteria_eliminated": old_master["metadata"]["criteria_eliminated"],
        "total_labs": len(labs) + len(elx_only_labs),
        "total_eliminated": len(old_master.get("part1_eliminated", [])),
    },
    "labs": {**labs, **elx_only_labs},
    "eliminated": old_master.get("part1_eliminated", []),
    "eliminated_elx": old_master.get("part2_eliminated_elx_urops", []),
}

master_path = "/mnt/user-data/outputs/master_db.json"
with open(master_path, "w") as f:
    json.dump(new_master, f, indent=2)
print(f"master_db.json: {len(new_master['labs'])} labs, {len(new_master['eliminated'])} eliminated profs")


# ================================================================
# 2. Restructure urop_emails.json
# ================================================================
with open("/mnt/user-data/uploads/urop_emails.json") as f:
    old_emails = json.load(f)

TAG = "-UROP-"

new_emails = {
    "metadata": {
        "sender": {
            "name": "Dominik Bach",
            "email": "mit_bach@mit.edu",
            "year": "MIT '29",
            "major": "Course 6-4 (AI & Decision Making)",
            "tag": TAG,
        },
        "policy_version": "v3",
        "total_emails": len(old_emails["emails"]),
        "total_recipients": len(set(e["to_email"] for e in old_emails["emails"])),
        "total_batches": len(set(e["batch_id"] for e in old_emails["emails"])),
    },
    "emails": []
}

for e in old_emails["emails"]:
    # Fix tag in subject
    subj = e["subject"].replace("--UROP--", TAG)

    new_emails["emails"].append({
        "id": e["id"],
        "batch_id": e["batch_id"],
        "to": {
            "name": e["to_name"],
            "email": e["to_email"],
            "role": e["role"],  # professor | grad_student | contact
        },
        "lab": {
            "name": e["lab_name"],
            "pi": e["professor_name"],
        },
        "subject": subj,
        "body": e["body"],
        "notes": e.get("notes", ""),
        "tracking": {
            "status": e.get("status", "draft"),
            "sent_date": e.get("sent_date"),
            "followup_date": e.get("followup_date"),
            "response_date": e.get("response"),
        }
    })

emails_path = "/mnt/user-data/outputs/urop_emails.json"
with open(emails_path, "w") as f:
    json.dump(new_emails, f, indent=2)
print(f"urop_emails.json: {len(new_emails['emails'])} emails, tag={TAG}")

# ================================================================
# SUMMARY
# ================================================================
print(f"\nDone. Files written to /mnt/user-data/outputs/")
print(f"  master_db.json     — lab-centric database")
print(f"  urop_emails.json   — restructured emails with -UROP- tag")
