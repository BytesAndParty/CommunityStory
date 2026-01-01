#!/usr/bin/env python3
"""
Story Generator: Verarbeitet GitHub Issues und generiert Story-Updates
"""

import os
import anthropic
from pathlib import Path


def read_file(filepath):
    """Liest eine Datei und gibt den Inhalt zurück"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def read_all_files_in_dir(directory):
    """Liest alle .md Dateien in einem Verzeichnis"""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    files_content = []
    for filepath in dir_path.glob('*.md'):
        content = read_file(filepath)
        if content:
            files_content.append(f"## {filepath.name}\n\n{content}")

    return files_content


def main():
    # Umgebungsvariablen auslesen
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    issue_title = os.environ.get('ISSUE_TITLE', '')
    issue_body = os.environ.get('ISSUE_BODY', '')
    issue_number = os.environ.get('ISSUE_NUMBER', '')

    if not api_key:
        print("❌ ANTHROPIC_API_KEY nicht gesetzt!")
        exit(1)

    # Projektdateien einlesen
    instructions = read_file('CLAUDE.md')
    current_story = read_file('story.md')

    # Alle Charaktere, Orte, Items einlesen
    characters = read_all_files_in_dir('characters')
    locations = read_all_files_in_dir('locations')
    items = read_all_files_in_dir('items')

    # Context zusammenstellen
    context = f"""# CommunityStorytime – Story Generator

## Deine Aufgabe
Ein neues Issue wurde eröffnet. Entwickle die Geschichte basierend auf diesem Vorschlag weiter.

## Issue #{issue_number}
**Titel:** {issue_title}

**Beschreibung:**
{issue_body}

---

## Instruktionen
{instructions}

---

## Aktuelle Story
{current_story}

---

## Bestehende Charaktere
{''.join(characters) if characters else 'Noch keine weiteren Charaktere'}

---

## Bestehende Orte
{''.join(locations) if locations else 'Noch keine weiteren Orte'}

---

## Bestehende Items
{''.join(items) if items else 'Noch keine Items'}

---

## Deine Aufgabe jetzt

1. Lies das Issue und verstehe den Vorschlag
2. Erweitere `story.md` mit einem neuen Kapitel (300-800 Wörter)
3. Falls nötig: Erstelle oder aktualisiere Charakter-, Orts- oder Item-Dateien
4. Antworte NUR mit den fertigen Dateiinhalten im folgenden Format:

```
FILE: story.md
---
[Vollständiger neuer Inhalt für story.md]
---

FILE: characters/Charaktername.md
---
[Vollständiger Inhalt]
---

FILE: locations/Ortsname.md
---
[Vollständiger Inhalt]
---
```

WICHTIG:
- Gib IMMER den KOMPLETTEN Inhalt der Datei aus, nicht nur die Änderungen
- Beginne jede Datei mit "FILE: pfad/dateiname.md"
- Trenne Dateien mit "---"
"""

    # Claude API aufrufen
    client = anthropic.Anthropic(api_key=api_key)

    print("🤖 Rufe Claude API auf...")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[
            {"role": "user", "content": context}
        ]
    )

    response_text = message.content[0].text

    print("✅ Claude-Antwort erhalten")
    print("\n" + "="*60)
    print(response_text)
    print("="*60 + "\n")

    # Dateien parsen und schreiben
    parse_and_write_files(response_text)


def parse_and_write_files(response):
    """Parst die Claude-Antwort und schreibt Dateien"""
    lines = response.split('\n')
    current_file = None
    current_content = []

    for line in lines:
        if line.startswith('FILE: '):
            # Vorherige Datei speichern
            if current_file:
                write_file(current_file, '\n'.join(current_content))

            # Neue Datei beginnen
            current_file = line.replace('FILE: ', '').strip()
            current_content = []

        elif line.strip() == '---':
            # Trennlinie ignorieren
            continue

        elif line.startswith('```'):
            # Code-Blöcke ignorieren
            continue

        else:
            # Inhalt sammeln
            if current_file:
                current_content.append(line)

    # Letzte Datei speichern
    if current_file:
        write_file(current_file, '\n'.join(current_content))


def write_file(filepath, content):
    """Schreibt Inhalt in eine Datei"""
    # Verzeichnis erstellen falls nötig
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Datei schreiben
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.strip())

    print(f"✅ Datei geschrieben: {filepath}")


if __name__ == '__main__':
    main()
