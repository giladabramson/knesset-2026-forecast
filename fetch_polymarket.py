# Pull every open Polymarket event about the 2026 Knesset election (public gamma API, read-only).
import json
from pathlib import Path

import requests

OUT = Path(__file__).with_name("polymarket_events.json")
QUERIES = ["israel election", "israel knesset", "israel election seats", "israel election largest party",
           "israel prime minister", "israel election turnout", "israel election vote share", "netanyahu bloc"]

events = {}
for q in QUERIES:
    for page in range(1, 6):
        r = requests.get("https://gamma-api.polymarket.com/public-search",
                         params={"q": q, "limit_per_type": 50, "page": page, "events_status": "active"}, timeout=30)
        r.raise_for_status()
        batch = r.json().get("events") or []
        for e in batch:
            if "israel" in (e.get("slug") or "") or "knesset" in (e.get("title") or "").lower():
                events[e["slug"]] = e
        if len(batch) < 50:
            break

rows = []
for slug, e in sorted(events.items()):
    for m in e.get("markets") or []:
        prices = json.loads(m.get("outcomePrices") or "[]")
        rows.append({
            "event": e.get("title"), "slug": slug, "question": m.get("question"),
            "group": m.get("groupItemTitle"), "yes": float(prices[0]) if prices else None,
            "bid": m.get("bestBid"), "ask": m.get("bestAsk"), "last": m.get("lastTradePrice"),
            "volume": float(m.get("volume") or 0), "closed": m.get("closed"), "end": m.get("endDate"),
        })
OUT.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(events), "events,", len(rows), "markets")
for slug in sorted(events):
    print(" ", slug, "|", events[slug].get("title"), "| vol", round(float(events[slug].get("volume") or 0)))
