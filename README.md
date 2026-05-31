# Game Pass × Metacritic

Eine kostenlose Web-App, die alle Spiele im Xbox Game Pass auflistet
und je Spiel den Metacritic-Metascore und User-Score zeigt.
Läuft komplett im Browser, gehostet auf GitHub Pages, Daten werden
einmal pro Woche automatisch aktualisiert.

---

## Was tut was?

| Datei | Aufgabe |
|---|---|
| `index.html` | Die App selbst (Suche, Sortierung). Das sieht der Besucher. |
| `games.json` | Die Daten (Spiele + Scores). Wird automatisch erneuert. |
| `scraper.py` | Holt Game-Pass-Liste + Metacritic-Scores. |
| `overrides.json` | Hier korrigierst du Spiele von Hand, die nicht gefunden wurden. |
| `requirements.txt` | Liste der Python-Pakete. Nicht ändern. |
| `.github/workflows/update.yml` | Der „Roboter", der wöchentlich läuft. |

---

## Einrichtung (Schritt für Schritt)

### 1. GitHub-Konto anlegen
Falls noch nicht vorhanden: auf https://github.com kostenlos registrieren.

### 2. Neues Repository (Repo) erstellen
1. Oben rechts auf **+** → **New repository**.
2. Name z. B. `gamepass-metacritic`.
3. **Public** auswählen (nötig für kostenlose GitHub Pages).
4. **Create repository** klicken.

### 3. Diese Dateien hochladen
1. Im neuen Repo auf **Add file** → **Upload files**.
2. Alle Dateien aus diesem Projekt hineinziehen — **wichtig**: den
   Ordner `.github` mit der Datei darin ebenfalls. Am einfachsten:
   die ganze ZIP entpacken und den kompletten Inhalt hochladen.
3. Unten **Commit changes** klicken.

> Wenn der Ordner `.github/workflows/` beim Hochladen verloren geht,
> lege ihn manuell an: **Add file → Create new file**, als Namen
> `.github/workflows/update.yml` eingeben (die Schrägstriche erzeugen
> die Ordner automatisch) und den Inhalt einfügen.

### 4. GitHub Pages aktivieren (App sichtbar machen)
1. Im Repo auf **Settings** (oben).
2. Links auf **Pages**.
3. Bei „Branch" **main** wählen, Ordner **/ (root)**, **Save**.
4. Nach 1–2 Minuten erscheint dort deine Adresse, etwa:
   `https://deinname.github.io/gamepass-metacritic/`
   Diese Adresse kannst du am Handy und überall öffnen.

Ab jetzt funktioniert die App bereits — mit den Beispieldaten.

### 5. Den Roboter (Action) zulassen und einmal manuell starten
1. Im Repo auf **Actions**.
2. Falls eine Sicherheitsfrage kommt: **I understand … enable workflows**.
3. Links **„Spiele aktualisieren"** anklicken.
4. Rechts **Run workflow** → **Run workflow**.
5. Zusehen: Der Lauf holt die echten Spiele und schreibt eine neue
   `games.json`. Danach Seite neu laden — jetzt mit echten Daten.

Ab dann läuft das jeden Montag von allein. Du musst nichts mehr tun.

---

## Wenn Metacritic-Scores fehlen

Manche Spiele werden nicht automatisch gefunden (anderer Schreibweise,
Bot-Schutz von Metacritic). Bei diesen steht „–" statt einer Zahl.

So korrigierst du eins:
1. Such das Spiel auf https://www.metacritic.com und kopiere den
   Teil aus der Adresse nach `/game/` — das ist der „Slug".
   Beispiel: `…/game/lies-of-p/` → Slug ist `lies-of-p`.
2. Öffne `overrides.json` im Repo (Stift-Symbol = bearbeiten).
3. Trag das Spiel ein, **exakt mit dem Titel wie er in der App steht**:
   ```json
   "Genauer Spieltitel": { "slug": "der-richtige-slug" }
   ```
4. Klappt das Scraping gar nicht, trag die Zahlen direkt ein:
   ```json
   "Genauer Spieltitel": { "meta": 88, "user": 7.9 }
   ```
5. **Commit changes**, dann unter **Actions** den Lauf erneut starten.

---

## Wichtige Hinweise

- **Metacritic erlaubt automatisches Auslesen offiziell nicht.** Für ein
  privates Projekt ist das meist unproblematisch, aber es kann sein, dass
  Metacritic Zugriffe von GitHub-Servern zeitweise blockt. Dann hilft die
  `overrides.json` oder ein gelegentlicher manueller Lauf vom eigenen PC.
- **Game-Pass-Liste:** Microsoft hat keine offizielle öffentliche API.
  Der Scraper nutzt bewährte inoffizielle Endpunkte. Sollten irgendwann
  keine Spiele mehr kommen, müssen die IDs oben in `scraper.py`
  (`SIGL_IDS`) aktualisiert werden.
- **Robustere Alternative zu Metacritic:** Die kostenlose IGDB-API liefert
  Kritiker- und Nutzerwertungen offiziell und zuverlässig — das sind dann
  aber andere Zahlen als Metacritic. Bei Bedarf umbaubar.
