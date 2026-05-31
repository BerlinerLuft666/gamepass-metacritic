#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Holt die aktuelle Xbox-Game-Pass-Liste (deutscher Markt) und ergaenzt
fuer jedes Spiel den Metacritic-Metascore und User-Score.
Ergebnis wird in games.json geschrieben.

Hinweise:
- Der Game-Pass-Teil nutzt die (inoffiziellen) catalog.gamepass.com- und
  displaycatalog-Endpunkte, die viele Community-Projekte verwenden.
- Der Metacritic-Teil ist Scraping und kann fehlschlagen (Bot-Schutz).
  Fuer Spiele, bei denen das Matching nicht klappt, traegst du den
  korrekten Metacritic-Slug oder feste Scores in overrides.json ein.
"""

import json
import re
import time
import sys
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

MARKET = "DE"
LANGUAGE = "de-de"

# Bekannte Game-Pass-"Sammlungen" (SIGL-IDs). Diese decken Konsole + PC ab.
# Wenn sich Microsoft etwas aendert, muessen diese IDs ggf. aktualisiert werden.
SIGL_IDS = {
    "Konsole": "f6f1f99f-9b49-4ccd-b3bf-4d9767a77f5e",
    "PC":      "fdd9e2a7-0fee-49f6-ad69-4354098401ff",
}

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

ROOT = Path(__file__).parent
OVERRIDES_FILE = ROOT / "overrides.json"
OUTPUT_FILE = ROOT / "games.json"


# ---------------------------------------------------------------------------
# Schritt 1: Produkt-IDs aus dem Game Pass holen
# ---------------------------------------------------------------------------

def get_product_ids():
    ids = set()
    for label, sigl in SIGL_IDS.items():
        url = (f"https://catalog.gamepass.com/sigls/v2"
               f"?id={sigl}&language={LANGUAGE}&market={MARKET}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            data = r.json()
            # Erstes Element ist Metadaten, der Rest enthaelt {"id": "..."}
            found = [item["id"] for item in data if "id" in item]
            ids.update(found)
            print(f"  {label}: {len(found)} Produkte")
        except Exception as e:
            print(f"  WARN: Konnte {label}-Liste nicht laden: {e}")
    return list(ids)


# ---------------------------------------------------------------------------
# Schritt 2: Titel + Jahr zu jeder Produkt-ID holen
# ---------------------------------------------------------------------------

def get_product_details(product_ids):
    games = []
    # Die Detail-API erlaubt mehrere IDs pro Aufruf (in Bloecken).
    for i in range(0, len(product_ids), 20):
        batch = product_ids[i:i + 20]
        url = ("https://displaycatalog.mp.microsoft.com/v7.0/products"
               f"?bigIds={','.join(batch)}"
               f"&market={MARKET}&languages={LANGUAGE}&MS-CV=DGU1mcuYo0WMMp+F.1")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            for product in r.json().get("Products", []):
                title, year = parse_product(product)
                if title:
                    games.append({"title": title, "year": year})
        except Exception as e:
            print(f"  WARN: Detail-Block {i} fehlgeschlagen: {e}")
        time.sleep(0.4)
    # Duplikate (gleicher Titel) entfernen
    seen, unique = set(), []
    for g in sorted(games, key=lambda x: x["title"].lower()):
        if g["title"].lower() not in seen:
            seen.add(g["title"].lower())
            unique.append(g)
    return unique


def parse_product(product):
    try:
        loc = product["LocalizedProperties"][0]
        title = loc.get("ProductTitle", "").strip()
        year = None
        # Release-Datum steht je nach Produkt an unterschiedlichen Stellen
        for sku in product.get("DisplaySkuAvailabilities", []):
            for av in sku.get("Availabilities", []):
                start = av.get("Conditions", {}).get("StartDate", "")
                if start[:4].isdigit():
                    year = int(start[:4])
                    break
        return title, year
    except Exception:
        return None, None


# ---------------------------------------------------------------------------
# Schritt 3: Metacritic-Scores holen
# ---------------------------------------------------------------------------

def slugify(title):
    """Macht aus 'A Plague Tale: Requiem' -> 'a-plague-tale-requiem'."""
    t = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def get_metacritic(title, override=None):
    """Gibt (metascore, userscore, url) zurueck oder (None, None, url)."""
    if override:
        # In overrides.json kann man feste Scores ODER einen Slug angeben
        if "meta" in override or "user" in override:
            return (override.get("meta"), override.get("user"),
                    override.get("url", ""))
        slug = override.get("slug") or slugify(title)
    else:
        slug = slugify(title)

    url = f"https://www.metacritic.com/game/{slug}/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return None, None, url
        soup = BeautifulSoup(r.text, "html.parser")
        # Moderne Metacritic-Seiten betten die Daten als JSON ein:
        tag = soup.find("script", id="__NEXT_DATA__")
        if not tag:
            return None, None, url
        blob = json.loads(tag.string)
        meta, user = extract_scores(blob)
        return meta, user, url
    except Exception:
        return None, None, url


def extract_scores(blob):
    """Sucht rekursiv nach den Score-Feldern im eingebetteten JSON."""
    meta = user = None

    def walk(node):
        nonlocal meta, user
        if isinstance(node, dict):
            # Metacritic nennt die Felder je nach Seite unterschiedlich;
            # wir greifen die haeufigsten ab.
            if meta is None and isinstance(node.get("score"), (int, float)) \
                    and node.get("reviewType") == "critic":
                meta = node["score"]
            if user is None and isinstance(node.get("score"), (int, float)) \
                    and node.get("reviewType") == "user":
                user = node["score"]
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(blob)
    return meta, user


# ---------------------------------------------------------------------------
# Hauptablauf
# ---------------------------------------------------------------------------

def main():
    print("1) Game-Pass-Produkt-IDs holen ...")
    ids = get_product_ids()
    if not ids:
        print("FEHLER: Keine Produkt-IDs erhalten. Abbruch.")
        sys.exit(1)
    print(f"   -> {len(ids)} eindeutige IDs")

    print("2) Titel-Details holen ...")
    games = get_product_details(ids)
    print(f"   -> {len(games)} Spiele")

    overrides = {}
    if OVERRIDES_FILE.exists():
        overrides = json.loads(OVERRIDES_FILE.read_text("utf-8"))

    print("3) Metacritic-Scores holen (das dauert) ...")
    for n, g in enumerate(games, 1):
        ov = overrides.get(g["title"])
        meta, user, url = get_metacritic(g["title"], ov)
        g["meta"] = meta
        g["user"] = user
        g["mcUrl"] = url
        status = "ok" if meta is not None else "—"
        print(f"   [{n}/{len(games)}] {g['title'][:40]:40} {status}")
        time.sleep(1.0)  # hoeflich bleiben, nicht zu schnell anfragen

    out = {
        "updated": time.strftime("%Y-%m-%d"),
        "count": len(games),
        "games": games,
    }
    OUTPUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    matched = sum(1 for g in games if g["meta"] is not None)
    print(f"\nFertig. {matched}/{len(games)} Spiele mit Metascore.")
    print(f"games.json geschrieben.")


if __name__ == "__main__":
    main()
