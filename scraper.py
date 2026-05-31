#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liest die "Xbox Game Pass Master List" (oeffentliche Google-Tabelle)
und erzeugt daraus games.json.

Vorteil gegenueber dem alten Scraper: kein fragiles Metacritic-Scraping
und keine inoffizielle Xbox-API mehr. Die Tabelle enthaelt die komplette
Game-Pass-Liste samt Metascore bereits fertig.

Hinweis: Die Tabelle hat KEINEN User-Score, daher bleibt der leer.
"""

import csv
import io
import re
import json
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Konfiguration: die Google-Tabelle
# ---------------------------------------------------------------------------
SHEET_ID = "1kspw-4paT-eE5-mrCrc4R9tg70lH2ZTFrJOUmOtOytg"
GID = "115010307"  # Tab "Master List"
CSV_URL = (f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
           f"/export?format=csv&gid={GID}")

# Nur Spiele mit diesem Status uebernehmen (= aktuell im Game Pass).
KEEP_STATUS = "active"

ROOT = Path(__file__).parent
LOCAL_CSV = ROOT / "gamepass.csv"     # optionaler manueller Fallback
OUTPUT_FILE = ROOT / "games.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GamePassApp/1.0)"}


def get_csv_text():
    """Holt die CSV: bevorzugt eine lokal abgelegte Datei, sonst Download."""
    if LOCAL_CSV.exists():
        print(f"Lese lokale Datei {LOCAL_CSV.name}")
        return LOCAL_CSV.read_text("utf-8")
    print("Lade Tabelle als CSV herunter ...")
    r = requests.get(CSV_URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text


def parse_year(value):
    m = re.search(r"(19|20)\d{2}", value or "")
    return int(m.group(0)) if m else None


def slugify(title):
    import unicodedata
    t = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z0-9]+", "-", t.lower())
    return t.strip("-")


def main():
    text = get_csv_text()
    reader = csv.DictReader(io.StringIO(text))

    games = []
    seen = set()
    for row in reader:
        title = (row.get("Game") or "").strip()
        status = (row.get("Status") or "").strip().lower()
        if not title or KEEP_STATUS not in status:
            continue

        # Doppelte Titel (z. B. mehrere Systeme) ueberspringen
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)

        meta_raw = (row.get("Metacritic") or "").strip()
        try:
            meta = int(float(meta_raw)) if meta_raw else None
        except ValueError:
            meta = None

        games.append({
            "title": title,
            "year": parse_year(row.get("Release")),
            "meta": meta,
            "user": None,  # Tabelle hat keinen User-Score
            "mcUrl": f"https://www.metacritic.com/game/{slugify(title)}/",
        })

    games.sort(key=lambda g: (-(g["meta"] or -1), g["title"].lower()))

    out = {
        "updated": time.strftime("%Y-%m-%d"),
        "count": len(games),
        "games": games,
    }
    OUTPUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")

    with_meta = sum(1 for g in games if g["meta"] is not None)
    print(f"Fertig. {len(games)} aktive Spiele, davon {with_meta} mit Metascore.")
    print("games.json geschrieben.")


if __name__ == "__main__":
    main()
