#!/usr/bin/env python3
"""final cleanup — delete the live test row, verify, save webhook evidence log."""
import json, sys, urllib.request, urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SUPA = "https://fapejsnjzijlnpjomjzk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhcGVqc25qemlqbG5wam9tanprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMzEzMjksImV4cCI6MjA5MTkwNzMyOX0.X1WQp3MAHQJKJMCJtVqFyC4JUYc-4Hs5O7t66f5LWrg"
AHDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

def sreq(path, method="GET", body=None, headers=None):
    h = dict(AHDR)
    data = None
    if body is not None:
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    if headers: h.update(headers)
    r = urllib.request.Request(f"{SUPA}/rest/v1/{path}", data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

row = json.load(open("live_row.json"))
rid, slug = row["id"], row["slug"]
print("deleting:", rid, slug)

st, body = sreq(f"m_presale?id=eq.{rid}", "DELETE", None, {"Prefer": "return=representation"})
print(f"[{st}] delete: {body[:150]}")

st, body = sreq(f"m_presale?slug=eq.{slug}&select=slug,id")
print(f"[{st}] verify gone: {body[:120]}")

st, body = sreq("m_presale?select=slug&limit=20")
print(f"[{st}] remaining rows: {body[:400]}")

# save webhook log as evidence
UUID = "735604c2-1bed-40df-86ee-bde11c60ec04"
r = urllib.request.Request(f"https://webhook.site/token/{UUID}/requests?sorting=newest",
                           headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
try:
    with urllib.request.urlopen(r, timeout=25) as resp:
        data = resp.read().decode()
    open("evidence/xss_webhook_log.json", "w", encoding="utf-8").write(data)
    print("webhook log saved, len:", len(data))
except Exception as e:
    print("webhook save err:", e)
