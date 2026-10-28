#!/usr/bin/env python3
"""Pełna analiza treści publicznego filmu YouTube przez Gemini API (obraz + dźwięk, po samym linku).

Zwraca markdown: transkrypcję z timestampami + to, co widać na ekranie (prompty, ustawienia, kroki),
i zapisuje go do pliku. Klucz API czytany WYŁĄCZNIE z `~/.config/yt_channel/gemini_api_key` — nigdy nie
jest wypisywany. Darmowy limit Gemini: ok. 8 h filmów YouTube dziennie; tylko filmy publiczne.

Użycie:
    python3 scripts/yt_watch.py --url <link> --out <plik.md> [--model gemini-flash-latest] [--question "..."]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

KEY_FILE = Path.home() / ".config" / "yt_channel" / "gemini_api_key"
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

DEFAULT_QUESTION = """Analyse this entire video for a creator who wants to reproduce its method.
Return Markdown with these sections:

## 1. Full transcript
Everything that is said, in the original language, with [mm:ss] timestamps every 20–40 seconds.

## 2. On-screen content
Chronological list with [mm:ss]: every prompt, command, code, file, setting, UI element, tool name and URL
that is SHOWN on screen — quote prompts and commands VERBATIM, even if not read aloud.

## 3. Workflow
Numbered, reproducible step-by-step procedure (tools, inputs, outputs, order).

## 4. Tools and costs
Every tool/service/model mentioned, what it is used for, and any prices, plans or credit costs stated.

## 5. Claims and caveats
Results the author claims, and anything they say does not work or needs care.

Do not invent anything not present in the video; write "not shown" when unsure."""


def video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url)
    if not m:
        raise SystemExit(f"Nie rozpoznaję ID filmu w: {url}")
    return m.group(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--model", default="gemini-flash-latest")
    ap.add_argument("--question", default=DEFAULT_QUESTION)
    a = ap.parse_args()

    clean_url = f"https://www.youtube.com/watch?v={video_id(a.url)}"  # bez parametrów typu &t=
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    body = {
        "contents": [{"parts": [
            {"file_data": {"file_uri": clean_url}},
            {"text": a.question},
        ]}],
        "generationConfig": {"maxOutputTokens": 65536, "temperature": 0.2},
    }
    req = urllib.request.Request(
        API.format(model=a.model), data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        err = json.load(e).get("error", {})
        print(f"BŁĄD Gemini HTTP {e.code}: {err.get('message')}", file=sys.stderr)
        return 1

    cand = (d.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    usage = d.get("usageMetadata", {})
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(f"<!-- źródło: {clean_url} | model: {a.model} -->\n\n{text}\n", encoding="utf-8")
    print(f"{a.out}: {len(text)} znaków, finish={cand.get('finishReason')}, "
          f"tokeny wej./wyj.: {usage.get('promptTokenCount')}/{usage.get('candidatesTokenCount')}")
    return 0 if text else 1


if __name__ == "__main__":
    sys.exit(main())
