#!/usr/bin/env python3
"""Analiza publicznych danych kanałów YouTube przez YouTube Data API v3 — research dobrych praktyk.

Dla każdego kanału pobiera statystyki kanału i ostatnie N filmów (tytuł, pełny opis, tagi, długość,
wyświetlenia, polubienia, komentarze, miniatura), liczy wskaźnik „outlier” (wyświetlenia / mediana kanału)
i zapisuje surowe dane + podsumowanie do katalogu wyjściowego (domyślnie poza repo).

Klucz API czytany WYŁĄCZNIE z pliku `~/.config/yt_channel/youtube_api_key` — nigdy nie jest wypisywany.
Zużycie limitu: ~3 jednostki na kanał (channels + playlistItems + videos), bez search.list.

Użycie:
    python3 scripts/yt_research.py --out <katalog> [--videos 50] @handle1 @handle2 ...
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

KEY_FILE = Path.home() / ".config" / "yt_channel" / "youtube_api_key"
API = "https://www.googleapis.com/youtube/v3/"
SHORT_MAX_S = 180          # filmy do 3 min traktujemy jako Shorts / krótkie formy
MIN_AGE_DAYS = 14          # świeże filmy nie zebrały jeszcze wyświetleń — pomijamy w medianie
URL_RE = re.compile(r"https?://[^\s)>\]]+")
CHAPTER_RE = re.compile(r"^\s*\(?(\d{1,2}:)?\d{1,2}:\d{2}\)?\s", re.MULTILINE)
HASHTAG_RE = re.compile(r"(?<!\w)#\w+")
CTA_RE = re.compile(r"subscribe|like (?:the|this) video|hit the like|newsletter|patreon|membership|sponsor",
                    re.IGNORECASE)


def api(endpoint: str, key: str, **params) -> dict:
    """Wywołanie API; komunikat błędu bez klucza."""
    q = urllib.parse.urlencode({**params, "key": key})
    try:
        with urllib.request.urlopen(API + endpoint + "?" + q, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        err = json.load(e).get("error", {})
        raise RuntimeError(f"{endpoint}: HTTP {e.code} {err.get('message')}") from None


def iso_duration_s(d: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m:
        return 0
    dd, h, mi, s = (int(x or 0) for x in m.groups())
    return dd * 86400 + h * 3600 + mi * 60 + s


def channel_by_handle(handle: str, key: str) -> dict | None:
    d = api("channels", key, part="snippet,statistics,contentDetails,brandingSettings", forHandle=handle)
    return (d.get("items") or [None])[0]


def recent_video_ids(uploads: str, key: str, limit: int) -> list[str]:
    ids: list[str] = []
    token = None
    while len(ids) < limit:
        params = {"part": "contentDetails", "playlistId": uploads, "maxResults": 50}
        if token:
            params["pageToken"] = token
        d = api("playlistItems", key, **params)
        ids += [it["contentDetails"]["videoId"] for it in d.get("items", [])]
        token = d.get("nextPageToken")
        if not token:
            break
    return ids[:limit]


def videos(ids: list[str], key: str) -> list[dict]:
    out: list[dict] = []
    for i in range(0, len(ids), 50):
        d = api("videos", key, part="snippet,contentDetails,statistics", id=",".join(ids[i:i + 50]))
        out += d.get("items", [])
    return out


def analyse_video(v: dict, now: datetime) -> dict:
    sn, st, cd = v["snippet"], v.get("statistics", {}), v["contentDetails"]
    desc = sn.get("description", "")
    published = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
    links = URL_RE.findall(desc)
    thumbs = sn.get("thumbnails", {})
    best = next((thumbs[k]["url"] for k in ("maxres", "standard", "high") if k in thumbs), None)
    return {
        "id": v["id"],
        "title": sn["title"],
        "title_len": len(sn["title"]),
        "published": sn["publishedAt"],
        "age_days": (now - published).days,
        "weekday_utc": published.strftime("%a"),
        "hour_utc": published.hour,
        "duration_s": iso_duration_s(cd.get("duration")),
        "has_captions": cd.get("caption") == "true",
        "views": int(st.get("viewCount", 0)),
        "likes": int(st.get("likeCount", 0)) if "likeCount" in st else None,
        "comments": int(st.get("commentCount", 0)) if "commentCount" in st else None,
        "tags": sn.get("tags", []),
        "desc_len": len(desc),
        "desc_first_150": desc[:150],
        "chapters": len(CHAPTER_RE.findall(desc)),
        "links": len(links),
        "link_domains": sorted({urllib.parse.urlparse(u).netloc.removeprefix("www.") for u in links}),
        "hashtags": HASHTAG_RE.findall(desc),
        "desc_cta": sorted({m.lower() for m in CTA_RE.findall(desc)}),
        "thumbnail": best,
        "description": desc,
    }


def summarise(ch: dict, vids: list[dict]) -> dict:
    longs = [v for v in vids if v["duration_s"] > SHORT_MAX_S]
    shorts = [v for v in vids if 0 < v["duration_s"] <= SHORT_MAX_S]
    base = [v for v in longs if v["age_days"] >= MIN_AGE_DAYS] or longs
    med = statistics.median([v["views"] for v in base]) if base else 0
    for v in vids:
        v["outlier"] = round(v["views"] / med, 2) if med else None
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return round(statistics.mean(xs), 1) if xs else None
    dates = sorted(v["published"] for v in longs)
    span_days = ((datetime.fromisoformat(dates[-1].replace("Z", "+00:00"))
                  - datetime.fromisoformat(dates[0].replace("Z", "+00:00"))).days if len(dates) > 1 else 0)
    return {
        "channel": ch["snippet"]["title"],
        "handle": ch["snippet"].get("customUrl"),
        "subscribers": int(ch["statistics"].get("subscriberCount", 0)),
        "total_videos": int(ch["statistics"].get("videoCount", 0)),
        "analysed": len(vids),
        "long_count": len(longs),
        "short_count": len(shorts),
        "long_per_month": round(len(longs) / (span_days / 30), 1) if span_days else None,
        "median_views_long": med,
        "median_duration_min": round(statistics.median([v["duration_s"] for v in longs]) / 60, 1) if longs else None,
        "mean_title_len": mean([v["title_len"] for v in longs]),
        "share_with_chapters": round(sum(v["chapters"] >= 3 for v in longs) / len(longs), 2) if longs else None,
        "share_with_captions": round(sum(v["has_captions"] for v in longs) / len(longs), 2) if longs else None,
        "mean_links": mean([v["links"] for v in longs]),
        "mean_desc_len": mean([v["desc_len"] for v in longs]),
        "share_with_tags": round(sum(bool(v["tags"]) for v in longs) / len(longs), 2) if longs else None,
        "top_outliers": [
            {k: v[k] for k in ("title", "views", "outlier", "duration_s", "published", "thumbnail", "id")}
            for v in sorted(longs, key=lambda x: x["outlier"] or 0, reverse=True)[:5]
        ],
        "channel_description": ch["snippet"].get("description", ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--videos", type=int, default=50)
    ap.add_argument("handles", nargs="+")
    a = ap.parse_args()
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    a.out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    summary = []
    for h in a.handles:
        ch = channel_by_handle(h, key)
        if not ch:
            print(f"{h}: nie znaleziono kanału", file=sys.stderr)
            continue
        uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        vids = [analyse_video(v, now) for v in videos(recent_video_ids(uploads, key, a.videos), key)]
        s = summarise(ch, vids)
        summary.append(s)
        (a.out / f"{h.lstrip('@')}.json").write_text(
            json.dumps({"summary": s, "videos": vids}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{h}: {s['channel']} — {s['subscribers']:,} sub., {s['long_count']} długich / "
              f"{s['short_count']} krótkich, mediana {s['median_views_long']:,.0f} wyśw.")
    (a.out / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
