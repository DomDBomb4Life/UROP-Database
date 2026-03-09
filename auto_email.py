#!/usr/bin/env python3
"""
AutoEmail - UROP Cold Email Manager
====================================
Reads from urop_emails.json, manages sending, tracking, and follow-ups.

Usage:
    python auto_email.py list                    # List all emails by batch
    python auto_email.py preview <id>            # Preview a specific email
    python auto_email.py preview-batch <batch>   # Preview all emails in a batch
    python auto_email.py send <id>               # Mark as sent + open in mail client
    python auto_email.py send-batch <batch>      # Mark entire batch as sent
    python auto_email.py followup                # Show emails needing follow-up (10+ days)
    python auto_email.py status                  # Summary dashboard
    python auto_email.py responded <id>          # Mark email as responded
    python auto_email.py export-csv              # Export tracking to CSV

Designed for Apple Mail Smart Mailbox filtering via --UROP-- tag in subjects.
"""

import json, sys, os, csv, subprocess, urllib.parse
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urop_emails.json")
FOLLOWUP_DAYS = 10

def load_db():
    with open(DB_PATH) as f: return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f: json.dump(data, f, indent=2)

def cmd_list(data):
    batches = {}
    for e in data["emails"]:
        batches.setdefault(e["batch_id"], []).append(e)
    for bid, emails in sorted(batches.items()):
        print(f"\n{'='*60}")
        print(f"BATCH: {bid} | Prof: {emails[0]['professor_name']} | Lab: {emails[0]['lab_name']}")
        print(f"{'='*60}")
        for e in emails:
            icon = {"draft":"📝","sent":"📤","followed_up":"🔄","responded":"✅"}.get(e["status"],"❓")
            print(f"  {icon} [{e['id']:3d}] {e['role']:14s} → {e['to_name']:25s} <{e['to_email']}>")

def cmd_preview(data, eid):
    eid = int(eid)
    for e in data["emails"]:
        if e["id"] == eid:
            print(f"\nTO:      {e['to_name']} <{e['to_email']}>")
            print(f"SUBJECT: {e['subject']}")
            print(f"BATCH:   {e['batch_id']} | ROLE: {e['role']} | STATUS: {e['status']}")
            if e["notes"]: print(f"NOTES:   {e['notes']}")
            print(f"{'='*60}\n{e['body']}\n"); return
    print(f"Email #{eid} not found.")

def cmd_preview_batch(data, bid):
    for e in data["emails"]:
        if e["batch_id"] == bid:
            print(f"\n[{e['id']}] TO: {e['to_name']} <{e['to_email']}> ({e['role']})")
            print(f"SUBJECT: {e['subject']}\n{'─'*50}\n{e['body']}\n")

def cmd_send(data, eid):
    eid = int(eid)
    for e in data["emails"]:
        if e["id"] == eid:
            now = datetime.now().strftime("%Y-%m-%d")
            e["status"] = "sent"; e["sent_date"] = now
            e["followup_date"] = (datetime.now() + timedelta(days=FOLLOWUP_DAYS)).strftime("%Y-%m-%d")
            save_db(data)
            print(f"✅ #{eid} sent on {now}. Follow-up: {e['followup_date']}")
            mailto = f"mailto:{e['to_email']}?subject={urllib.parse.quote(e['subject'])}&body={urllib.parse.quote(e['body'])}"
            try:
                if sys.platform == "darwin": subprocess.run(["open", mailto])
                elif sys.platform == "linux": subprocess.run(["xdg-open", mailto])
            except: print("   Open mail client manually.")
            return
    print(f"#{eid} not found.")

def cmd_send_batch(data, bid):
    now = datetime.now().strftime("%Y-%m-%d")
    fu = (datetime.now() + timedelta(days=FOLLOWUP_DAYS)).strftime("%Y-%m-%d")
    ct = 0
    for e in data["emails"]:
        if e["batch_id"] == bid and e["status"] == "draft":
            e["status"] = "sent"; e["sent_date"] = now; e["followup_date"] = fu; ct += 1
    save_db(data); print(f"✅ {ct} emails in '{bid}' marked sent. Follow-up: {fu}")

def cmd_followup(data):
    today = datetime.now().strftime("%Y-%m-%d")
    need = [e for e in data["emails"] if e["status"]=="sent" and e.get("followup_date","9")<=today]
    if not need: print("No follow-ups needed. 🎉"); return
    print(f"\n⚠️  {len(need)} FOLLOW-UPS NEEDED:")
    for e in need:
        days = (datetime.now() - datetime.strptime(e["sent_date"],"%Y-%m-%d")).days
        fn = e["to_name"].split()[0]
        print(f"\n  [{e['id']}] {e['to_name']} ({e['to_email']}) — {days}d ago")
        print(f"      Subject: Re: {e['subject']}")
        print(f"      Body: Hi {fn} — just bumping this in case it got buried. Happy to work around whatever timeline works. Thanks again.\\nDominik")

def cmd_responded(data, eid):
    eid = int(eid)
    for e in data["emails"]:
        if e["id"] == eid:
            e["status"] = "responded"; e["response"] = datetime.now().strftime("%Y-%m-%d")
            save_db(data); print(f"🎉 #{eid} to {e['to_name']} — RESPONDED!"); return
    print(f"#{eid} not found.")

def cmd_status(data):
    total = len(data["emails"])
    st = {}; rl = {}
    for e in data["emails"]:
        st[e["status"]] = st.get(e["status"],0)+1
        rl[e["role"]] = rl.get(e["role"],0)+1
    batches = len(set(e["batch_id"] for e in data["emails"]))
    recip = len(set(e["to_email"] for e in data["emails"]))
    print(f"\n{'='*50}")
    print(f"UROP EMAIL DASHBOARD")
    print(f"{'='*50}")
    print(f"Emails: {total} | Recipients: {recip} | Batches: {batches}\n")
    for s,c in sorted(st.items()):
        print(f"  {'📝📤🔄✅❌'[['draft','sent','followed_up','responded','no_response'].index(s) if s in ['draft','sent','followed_up','responded','no_response'] else 4]} {s:15s}: {c:3d} ({c/total*100:.0f}%)")
    print()
    for r,c in sorted(rl.items()): print(f"  {r:15s}: {c}")
    today = datetime.now().strftime("%Y-%m-%d")
    fu = sum(1 for e in data["emails"] if e["status"]=="sent" and e.get("followup_date","9")<=today)
    if fu: print(f"\n⚠️  {fu} need follow-up! Run: python auto_email.py followup")

def cmd_export_csv(data):
    p = os.path.join(os.path.dirname(DB_PATH), "urop_tracking.csv")
    with open(p,"w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["ID","Batch","Name","Email","Role","Professor","Lab","Status","Sent","Followup","Response","Subject"])
        for e in data["emails"]:
            w.writerow([e["id"],e["batch_id"],e["to_name"],e["to_email"],e["role"],e["professor_name"],e["lab_name"],e["status"],e.get("sent_date",""),e.get("followup_date",""),e.get("response",""),e["subject"]])
    print(f"📊 Exported to {p}")

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit()
    d = load_db(); c = sys.argv[1]
    if c == "list": cmd_list(d)
    elif c == "preview" and len(sys.argv)>=3: cmd_preview(d, sys.argv[2])
    elif c == "preview-batch" and len(sys.argv)>=3: cmd_preview_batch(d, sys.argv[2])
    elif c == "send" and len(sys.argv)>=3: cmd_send(d, sys.argv[2])
    elif c == "send-batch" and len(sys.argv)>=3: cmd_send_batch(d, sys.argv[2])
    elif c == "followup": cmd_followup(d)
    elif c == "status": cmd_status(d)
    elif c == "responded" and len(sys.argv)>=3: cmd_responded(d, sys.argv[2])
    elif c == "export-csv": cmd_export_csv(d)
    else: print(__doc__)
