#!/usr/bin/env python3
"""
AutoEmail - UROP Cold Email Manager
====================================
Reads from urop_emails.json, manages sending, tracking, and follow-ups.
NOW WITH AUTO-SEND VIA APPLESCRIPT (macOS)!

Usage:
    python auto_email.py list                    # List all emails by batch
    python auto_email.py preview <id>            # Preview a specific email
    python auto_email.py preview-batch <batch>   # Preview all emails in a batch
    python auto_email.py send <id>               # AUTO-SEND via AppleScript + mark sent
    python auto_email.py send-batch <batch>      # AUTO-SEND entire batch
    python auto_email.py followup                # Show emails needing follow-up (10+ days)
    python auto_email.py status                  # Summary dashboard
    python auto_email.py responded <id>          # Mark email as responded
    python auto_email.py export-csv              # Export tracking to CSV
    python auto_email.py test <id>               # TEST MODE: preview in mail client
    python auto_email.py test-batch <batch>     # TEST MODE: preview batch

Designed for Apple Mail Smart Mailbox filtering via -UROP- tag in subjects.
AppleScript auto-send requires: System Preferences > Security & Privacy > Automation
"""

import json, sys, os, csv, subprocess, urllib.parse, random, string
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urop_emails.json")
FOLLOWUP_DAYS = 10
TEST_EMAIL = "test+urop@mit.edu"  # Your test email for dry runs

def load_db():
    with open(DB_PATH) as f: return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f: json.dump(data, f, indent=2)

def get_sender(data):
    """Extract sender info from metadata"""
    return data.get("metadata", {}).get("sender", {})

def get_email_field(e, field):
    """Navigate nested JSON structure: to.email -> to.name, lab.name, etc."""
    if field == "to_email": return e.get("to", {}).get("email", "")
    if field == "to_name": return e.get("to", {}).get("name", "")
    if field == "to_role": return e.get("to", {}).get("role", "")
    if field == "lab_name": return e.get("lab", {}).get("name", "")
    if field == "lab_pi": return e.get("lab", {}).get("pi", "")
    if field == "status": return e.get("tracking", {}).get("status", "draft")
    if field == "sent_date": return e.get("tracking", {}).get("sent_date")
    if field == "followup_date": return e.get("tracking", {}).get("followup_date")
    if field == "response_date": return e.get("tracking", {}).get("response_date")
    return e.get(field, "")

def set_email_status(e, status, sent_date=None, followup_date=None, response_date=None):
    """Update tracking info"""
    if "tracking" not in e: e["tracking"] = {}
    e["tracking"]["status"] = status
    if sent_date: e["tracking"]["sent_date"] = sent_date
    if followup_date: e["tracking"]["followup_date"] = followup_date
    if response_date: e["tracking"]["response_date"] = response_date

def escape_for_applescript(text):
    """Escape special characters for AppleScript"""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace("\n", "\\n")
    return text

def send_via_applescript(to_email, subject, body):
    """Send email via AppleScript (macOS only)"""
    subject_escaped = escape_for_applescript(subject)
    body_escaped = escape_for_applescript(body)
    
    applescript = f"""
tell application "Mail"
    set newMessage to make new outgoing message with properties {{subject:"{subject_escaped}", content:"{body_escaped}"}}
    tell newMessage
        make new to recipient at end of to recipients with properties {{address:"{to_email}"}}
        send
    end tell
end tell
"""
    try:
        result = subprocess.run(["osascript", "-e", applescript], 
                              check=False, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "AppleScript timeout (Mail may be busy)"
    except Exception as e:
        return False, str(e)

def cmd_list(data):
    batches = {}
    for e in data["emails"]:
        bid = e.get("batch_id", "unknown")
        batches.setdefault(bid, []).append(e)
    for bid, emails in sorted(batches.items()):
        if emails:
            prof = emails[0].get("to", {}).get("name", "Unknown")
            lab = emails[0].get("lab", {}).get("name", "Unknown")
            print(f"\n{'='*60}")
            print(f"BATCH: {bid} | Prof/Contact: {prof} | Lab: {lab}")
            print(f"{'='*60}")
            for e in emails:
                status = get_email_field(e, "status")
                icon = {"draft":"📝","sent":"📤","followed_up":"🔄","responded":"✅"}.get(status,"❓")
                to_name = get_email_field(e, "to_name")
                to_email = get_email_field(e, "to_email")
                to_role = get_email_field(e, "to_role")
                print(f"  {icon} [{e['id']:3d}] {to_role:14s} → {to_name:25s} <{to_email}>")

def cmd_preview(data, eid, test_mode=False):
    eid = int(eid)
    for e in data["emails"]:
        if e["id"] == eid:
            to_email = get_email_field(e, "to_email")
            to_name = get_email_field(e, "to_name")
            display_email = TEST_EMAIL if test_mode else to_email
            status = get_email_field(e, "status")
            
            print(f"\nTO:      {to_name} <{display_email}>")
            if test_mode:
                print(f"         (TEST MODE: normally sends to {to_email})")
            print(f"SUBJECT: {e.get('subject', '')}")
            print(f"BATCH:   {e.get('batch_id', '')} | ROLE: {get_email_field(e, 'to_role')} | STATUS: {status}")
            notes = e.get("notes", "")
            if notes: print(f"NOTES:   {notes}")
            print(f"{'='*60}\n{e.get('body', '')}\n")
            return
    print(f"Email #{eid} not found.")

def cmd_preview_batch(data, bid, test_mode=False):
    found = False
    for e in data["emails"]:
        if e.get("batch_id") == bid:
            found = True
            to_name = get_email_field(e, "to_name")
            to_email = get_email_field(e, "to_email")
            display_email = TEST_EMAIL if test_mode else to_email
            to_role = get_email_field(e, "to_role")
            
            print(f"\n[{e['id']}] TO: {to_name} <{display_email}> ({to_role})")
            if test_mode:
                print(f"    (TEST MODE: normally sends to {to_email})")
            print(f"SUBJECT: {e.get('subject', '')}\n{'─'*50}\n{e.get('body', '')}\n")
    if not found:
        print(f"Batch '{bid}' not found.")

def cmd_send(data, eid, test_mode=False):
    eid = int(eid)
    for e in data["emails"]:
        if e["id"] == eid:
            to_email = get_email_field(e, "to_email")
            to_name = get_email_field(e, "to_name")
            display_email = TEST_EMAIL if test_mode else to_email
            
            subject = e.get("subject", "")
            body = e.get("body", "")
            
            # Test mode: open in mail client for review, don't save
            if test_mode:
                mailto = f"mailto:{display_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                try:
                    if sys.platform == "darwin": 
                        subprocess.run(["open", mailto], check=False)
                except: 
                    print("   Open mail client manually.")
                print(f"✅ [TEST MODE] #{eid} opened in Mail for review (not saved)")
                return
            
            # Real send on macOS: use AppleScript
            if sys.platform == "darwin":
                print(f"📧 Sending #{eid} to {to_name} <{to_email}>...", end=" ", flush=True)
                success, error = send_via_applescript(display_email, subject, body)
                
                if success:
                    now = datetime.now().strftime("%Y-%m-%d")
                    followup = (datetime.now() + timedelta(days=FOLLOWUP_DAYS)).strftime("%Y-%m-%d")
                    set_email_status(e, "sent", sent_date=now, followup_date=followup)
                    save_db(data)
                    print(f"✅ sent! Follow-up: {followup}")
                else:
                    print(f"❌ FAILED")
                    print(f"\n   Error: {error}")
                    print(f"\n   Possible causes:")
                    print(f"   1. Mail.app is not running")
                    print(f"   2. AppleScript permissions not granted")
                    print(f"      → System Settings > Privacy & Security > Automation")
                    print(f"      → Grant Terminal (or your IDE) access to Mail")
                    print(f"   3. Mail is stuck (try restarting Mail.app)")
                    print(f"\n   Fallback: opening Mail manually...")
                    mailto = f"mailto:{display_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                    subprocess.run(["open", mailto], check=False)
            else:
                # Non-macOS: fallback to mailto
                print(f"ℹ️  macOS not detected. Opening mail client for manual send...")
                mailto = f"mailto:{display_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                try:
                    subprocess.run(["xdg-open", mailto], check=False)
                except:
                    print("   Open mail client manually.")
            return
    print(f"#{eid} not found.")

def cmd_send_batch(data, bid, test_mode=False):
    now = datetime.now().strftime("%Y-%m-%d")
    followup = (datetime.now() + timedelta(days=FOLLOWUP_DAYS)).strftime("%Y-%m-%d")
    emails_in_batch = [e for e in data.get("emails", []) if e.get("batch_id") == bid]
    draft_count = sum(1 for e in emails_in_batch if get_email_field(e, "status") == "draft")
    
    if draft_count == 0:
        print(f"⚠️  No draft emails in '{bid}' (all already sent).")
        return
    
    print(f"📧 Sending {draft_count} emails from batch '{bid}'...")
    sent_count = 0
    failed_count = 0
    
    for e in emails_in_batch:
        if get_email_field(e, "status") != "draft":
            continue
        
        to_email = get_email_field(e, "to_email")
        to_name = get_email_field(e, "to_name")
        subject = e.get("subject", "")
        body = e.get("body", "")
        
        print(f"  [{e['id']}] {to_name}...", end=" ", flush=True)
        
        if sys.platform == "darwin":
            success, error = send_via_applescript(to_email, subject, body)
            if success:
                set_email_status(e, "sent", sent_date=now, followup_date=followup)
                print("✅")
                sent_count += 1
            else:
                print(f"❌ ({error[:30]}...)")
                failed_count += 1
        else:
            print("(non-macOS, skipped)")
    
    save_db(data)
    print(f"\n✅ {sent_count} sent | ❌ {failed_count} failed")
    if sent_count > 0:
        print(f"   Follow-up reminders set to: {followup}")

def cmd_followup(data):
    today = datetime.now().strftime("%Y-%m-%d")
    need = [e for e in data["emails"] if get_email_field(e, "status") == "sent" 
            and e.get("tracking", {}).get("followup_date", "9") <= today]
    if not need: print("No follow-ups needed. 🎉"); return
    
    print(f"\n⚠️  {len(need)} FOLLOW-UPS NEEDED:")
    for e in need:
        sent_date = get_email_field(e, "sent_date")
        to_name = get_email_field(e, "to_name")
        to_email = get_email_field(e, "to_email")
        days = (datetime.now() - datetime.strptime(sent_date, "%Y-%m-%d")).days
        fn = to_name.split()[0]
        subject = e.get("subject", "").split(" — ")[0]
        
        print(f"\n  [{e['id']}] {to_name} ({to_email}) — {days}d ago")
        print(f"      Subject: Re: {subject}")
        print(f"      Body: Hi {fn} — just bumping this in case it got buried. Happy to work around whatever timeline works. Thanks again.\\nDominik")

def cmd_responded(data, eid):
    eid = int(eid)
    for e in data["emails"]:
        if e["id"] == eid:
            response_date = datetime.now().strftime("%Y-%m-%d")
            set_email_status(e, "responded", response_date=response_date)
            save_db(data)
            to_name = get_email_field(e, "to_name")
            print(f"🎉 #{eid} to {to_name} — RESPONDED!")
            return
    print(f"#{eid} not found.")

def cmd_status(data):
    emails = data.get("emails", [])
    total = len(emails)
    if total == 0:
        print("No emails in database.")
        return
    
    st = {}; rl = {}
    for e in emails:
        status = get_email_field(e, "status")
        role = get_email_field(e, "to_role")
        st[status] = st.get(status, 0) + 1
        rl[role] = rl.get(role, 0) + 1
    
    batches = len(set(e.get("batch_id") for e in emails if e.get("batch_id")))
    recip = len(set(e.get("to", {}).get("email") for e in emails if e.get("to", {}).get("email")))
    
    sender = get_sender(data)
    print(f"\n{'='*50}")
    print(f"UROP EMAIL DASHBOARD")
    print(f"{'='*50}")
    print(f"Sender: {sender.get('name', 'Unknown')} <{sender.get('email', 'Unknown')}>")
    print(f"Emails: {total} | Recipients: {recip} | Batches: {batches}\n")
    
    for s in ["draft", "sent", "followed_up", "responded", "no_response"]:
        if s in st:
            icons = {"draft":"📝","sent":"📤","followed_up":"🔄","responded":"✅","no_response":"❌"}
            c = st[s]
            print(f"  {icons.get(s, '❓')} {s:15s}: {c:3d} ({c/total*100:.0f}%)")
    
    print()
    for r, c in sorted(rl.items()): 
        print(f"  {r:15s}: {c}")
    
    today = datetime.now().strftime("%Y-%m-%d")
    fu = sum(1 for e in emails if get_email_field(e, "status") == "sent" 
             and e.get("tracking", {}).get("followup_date", "9") <= today)
    if fu: print(f"\n⚠️  {fu} need follow-up! Run: python auto_email.py followup")

def cmd_export_csv(data):
    p = os.path.join(os.path.dirname(DB_PATH), "urop_tracking.csv")
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ID","Batch","Name","Email","Role","Lab","PI","Status","Sent","Followup","Response","Subject"])
        for e in data.get("emails", []):
            w.writerow([
                e.get("id"),
                e.get("batch_id"),
                get_email_field(e, "to_name"),
                get_email_field(e, "to_email"),
                get_email_field(e, "to_role"),
                get_email_field(e, "lab_name"),
                get_email_field(e, "lab_pi"),
                get_email_field(e, "status"),
                get_email_field(e, "sent_date") or "",
                get_email_field(e, "followup_date") or "",
                get_email_field(e, "response_date") or "",
                e.get("subject", "")
            ])
    print(f"📊 Exported to {p}")

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit()
    
    d = load_db()
    c = sys.argv[1]
    
    if c == "list": cmd_list(d)
    elif c == "preview" and len(sys.argv)>=3: cmd_preview(d, sys.argv[2], test_mode=False)
    elif c == "preview-batch" and len(sys.argv)>=3: cmd_preview_batch(d, sys.argv[2], test_mode=False)
    elif c == "send" and len(sys.argv)>=3: cmd_send(d, sys.argv[2], test_mode=False)
    elif c == "send-batch" and len(sys.argv)>=3: cmd_send_batch(d, sys.argv[2], test_mode=False)
    elif c == "test" and len(sys.argv)>=3: cmd_preview(d, sys.argv[2], test_mode=True)
    elif c == "test-batch" and len(sys.argv)>=3: cmd_preview_batch(d, sys.argv[2], test_mode=True)
    elif c == "followup": cmd_followup(d)
    elif c == "status": cmd_status(d)
    elif c == "responded" and len(sys.argv)>=3: cmd_responded(d, sys.argv[2])
    elif c == "export-csv": cmd_export_csv(d)
    else: print(__doc__)
