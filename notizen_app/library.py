"""Find the note files on disk and group them by level.

Naming convention — the filename is the metadata:

    <Level>_<Title>.<ods|odt>       (underscores or spaces, either works)
    A2_Deutsch_Cheatsheet.ods  ->  level "A2", title "Deutsch Cheatsheet"
    B1 Grammatik.odt           ->  level "B1", title "Grammatik"

Drop a new file into ``notizen/`` and it shows up. A file that does not start
with a level code lands under "Sonstige" rather than being ignored.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
OTHER = "Sonstige"
SUPPORTED = {".ods": "sheet", ".odt": "document"}


@dataclass(frozen=True)
class Note:
    path: str
    level: str
    title: str
    kind: str  # "sheet" | "document"
    mtime: float

    @property
    def key(self) -> str:
        return f"{self.level}/{self.title}"


def level_sort_key(level: str) -> tuple[int, str]:
    return (LEVELS.index(level) if level in LEVELS else len(LEVELS), level)


def scan(folder: str) -> list[Note]:
    """All readable notes in ``folder``, sorted by level then title."""
    notes: list[Note] = []
    if not os.path.isdir(folder):
        return notes

    for name in os.listdir(folder):
        stem, ext = os.path.splitext(name)
        kind = SUPPORTED.get(ext.lower())
        if not kind or name.startswith((".", "~")):
            continue
        path = os.path.join(folder, name)
        notes.append(
            Note(
                path=path,
                level=_level_of(stem),
                title=_title_of(stem),
                kind=kind,
                mtime=os.path.getmtime(path),
            )
        )

    notes.sort(key=lambda n: (level_sort_key(n.level), n.title.lower()))
    return notes


def by_level(notes: list[Note]) -> dict[str, list[Note]]:
    grouped: dict[str, list[Note]] = {}
    for note in notes:
        grouped.setdefault(note.level, []).append(note)
    return dict(sorted(grouped.items(), key=lambda kv: level_sort_key(kv[0])))


SEPARATOR = re.compile(r"[_\s]+")


def _level_of(stem: str) -> str:
    head = SEPARATOR.split(stem.strip(), 1)[0].upper()
    return head if head in LEVELS else OTHER


def _title_of(stem: str) -> str:
    parts = SEPARATOR.split(stem.strip())
    if parts and parts[0].upper() in LEVELS and len(parts) > 1:
        parts = parts[1:]
    return " ".join(p for p in parts if p).replace("-", " ").strip() or stem