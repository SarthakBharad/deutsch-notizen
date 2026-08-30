"""Turn parsed notes into HTML.

Two things happen here beyond plain markup:

* **Search that ignores umlauts.** Typing "uber" finds "über" and "gruss"
  finds "Gruß", so nothing has to be typed on a German keyboard layout.
* **Two tints that carry meaning.** The leading article of a noun is set in
  the accent colour and the perfect auxiliary (hat / ist) is muted. Those are
  the two facts a vocabulary list exists to drill, so they get the emphasis
  instead of being decoration.
"""

from __future__ import annotations

import html
import re
import unicodedata

from .layout import SheetGroup, TableBlock, band_text, is_band
from .readers.odf import Block, Cell, ListItem, Span

FOLD = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "s", "é": "e", "è": "e"})

# Both are deliberately narrow. Case-sensitive, because a dictionary entry
# starts "der Anfang" while a capitalised "Das Buch liegt..." is a sentence.
# And a word must follow, so a declension table — whose cells ARE the articles —
# stays plain instead of turning entirely accent-coloured.
_WORD = r"\s+(?=[A-Za-zÄÖÜäöüß])"
ARTICLE = re.compile(
    r"^(der|die|das|den|dem|des|ein|eine|einen|einem|einer|eines"
    r"|kein|keine|keinen|keinem|keiner)" + _WORD
)
AUXILIARY = re.compile(r"^(hat|ist|haben|sind)" + _WORD)


def fold(text: str) -> str:
    """Lowercase and strip diacritics so search is keyboard-agnostic."""
    lowered = text.lower().translate(FOLD)
    stripped = unicodedata.normalize("NFKD", lowered)
    return "".join(c for c in stripped if not unicodedata.combining(c))


class Search:
    """A query, with the ability to test and highlight text."""

    def __init__(self, query: str):
        self.query = query.strip()
        self.needle = fold(self.query)

    @property
    def active(self) -> bool:
        return bool(self.needle)

    def matches(self, text: str) -> bool:
        return not self.active or self.needle in fold(text)

    def matches_any(self, texts) -> bool:
        return not self.active or any(self.needle in fold(t) for t in texts)

    def mark(self, text: str) -> str:
        """Escape for HTML, highlighting occurrences of the query."""
        if not self.active:
            return html.escape(text)
        folded = fold(text)
        if len(folded) != len(text):
            # Decomposition changed the length, so offsets no longer line up.
            # Showing the text unhighlighted beats highlighting the wrong span.
            return html.escape(text)
        out, cursor = [], 0
        while True:
            hit = folded.find(self.needle, cursor)
            if hit < 0:
                break
            out.append(html.escape(text[cursor:hit]))
            end = hit + len(self.needle)
            out.append(f'<mark class="hit">{html.escape(text[hit:end])}</mark>')
            cursor = end
        out.append(html.escape(text[cursor:]))
        return "".join(out)


def cell_html(cell: Cell, search: Search) -> str:
    """One table cell, with the article or auxiliary tinted."""
    text = cell.text
    if not text.strip():
        return ""

    marked = search.mark(text)

    prefix, klass = ARTICLE.match(text), "art"
    if prefix is None:
        prefix, klass = AUXILIARY.match(text), "aux"

    # Only tint the prefix when the search did not already highlight it,
    # so the two emphases never fight over the same characters.
    if prefix is not None and not marked.startswith("<mark"):
        word = html.escape(prefix.group(1))
        marked = f'<span class="{klass}">{word}</span>' + marked[len(word) :]

    return marked.replace("\n", "<br>")


# --------------------------------------------------------------------------
# sheets
# --------------------------------------------------------------------------


def filter_block(block: TableBlock, search: Search) -> TableBlock | None:
    """Keep rows that match, plus the band each surviving row sits under."""
    if not search.active:
        return block

    kept: list[list[Cell]] = []
    pending_band: list[Cell] | None = None

    for row in block.rows:
        if is_band(row):
            pending_band = row
            continue
        if all(c.empty for c in row):
            continue
        if search.matches_any([c.text for c in row]):
            if pending_band is not None:
                kept.append(pending_band)
                pending_band = None
            kept.append(row)

    return TableBlock(header=block.header, rows=kept) if kept else None


def table_html(block: TableBlock, search: Search) -> str:
    widths = [len(r) for r in block.rows] + [len(block.header or [])]
    width = max(widths) or 1
    parts = ['<div class="tbl-wrap"><table class="grid">']

    if block.header:
        cells = "".join(
            f"<th>{search.mark(c.text)}</th>" for c in _pad(block.header, width)
        )
        parts.append(f"<thead><tr>{cells}</tr></thead>")

    parts.append("<tbody>")
    for row in block.rows:
        if all(c.empty for c in row):
            parts.append(f'<tr class="spacer"><td colspan="{width}"></td></tr>')
        elif is_band(row):
            parts.append(
                f'<tr class="band"><td colspan="{width}">{search.mark(band_text(row))}</td></tr>'
            )
        else:
            tds = []
            for i, cell in enumerate(_pad(row, width)):
                if cell.covered:
                    continue
                attrs = ' class="lead"' if i == 0 else ""
                if cell.colspan > 1:
                    attrs += f' colspan="{cell.colspan}"'
                if cell.rowspan > 1:
                    attrs += f' rowspan="{cell.rowspan}"'
                tds.append(f"<td{attrs}>{cell_html(cell, search)}</td>")
            parts.append("<tr>" + "".join(tds) + "</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def sheet_html(groups: list[SheetGroup], search: Search) -> tuple[str, int]:
    """Render every table in a sheet. Returns (html, rows shown)."""
    chunks: list[str] = []
    shown = 0
    for group in groups:
        rendered = []
        for block in group.blocks:
            kept = filter_block(block, search)
            if kept is None:
                continue
            shown += sum(1 for r in kept.rows if not is_band(r) and any(not c.empty for c in r))
            rendered.append(table_html(kept, search))
        if rendered:
            chunks.append('<div class="sheet-group">' + "".join(rendered) + "</div>")
    return "".join(chunks), shown


# --------------------------------------------------------------------------
# documents
# --------------------------------------------------------------------------


def spans_html(spans: list[Span], search: Search) -> str:
    out = []
    for span in spans:
        text = search.mark(span.text).replace("\n", "<br>")
        if span.bold:
            text = f"<strong>{text}</strong>"
        if span.italic:
            text = f"<em>{text}</em>"
        out.append(text)
    return "".join(out)


def list_html(items: list[ListItem], search: Search) -> str:
    """Render a flat depth-tagged list as nested <ol>/<ul>.

    Nested levels get class="beispiel": in these notes an indented sub-item is
    always an example sentence for the rule above it, and it should read as one.
    """
    parts: list[str] = []
    open_lists: list[tuple[int, bool]] = []  # (depth, ordered)

    def close_one() -> None:
        _, ordered = open_lists.pop()
        parts.append("</li></ol>" if ordered else "</li></ul>")

    for item in items:
        while open_lists and open_lists[-1][0] > item.depth:
            close_one()

        if open_lists and open_lists[-1][0] == item.depth:
            parts.append("</li>")
        else:
            tag = "ol" if item.ordered else "ul"
            klass = ' class="beispiel"' if item.depth > 1 else ""
            parts.append(f"<{tag}{klass}>")
            open_lists.append((item.depth, item.ordered))

        parts.append(f"<li>{spans_html(item.spans, search)}")

    while open_lists:
        close_one()
    return "".join(parts)


def _filter_list(items: list[ListItem], search: Search) -> list[ListItem]:
    """Keep matching items, plus the parent line each one sits under."""
    if not search.active:
        return items

    kept: list[ListItem] = []
    for index, item in enumerate(items):
        if not search.matches_any([s.text for s in item.spans]):
            continue
        # walk back to the nearest shallower item so an example sentence
        # never appears without the rule it belongs to
        for parent in reversed(items[:index]):
            if parent.depth < item.depth:
                if parent not in kept:
                    kept.append(parent)
                break
        kept.append(item)
    return kept


def document_html(blocks: list[Block], search: Search, skip_title: str = "") -> tuple[str, int]:
    """Render an .odt. Search filters to matching blocks and their heading."""
    parts: list[str] = []
    shown = 0
    pending_heading: str | None = None
    blocks = _drop_repeated_title(blocks, skip_title)

    for block in blocks:
        if block.kind == "heading":
            level = min(max(block.level, 2), 4)
            markup = f"<h{level}>{spans_html(block.spans, search)}</h{level}>"
            if search.active:
                pending_heading = markup
            else:
                parts.append(markup)
            continue

        if block.kind == "table" and block.grid is not None:
            from .layout import structure

            body, count = sheet_html(structure(block.grid), search)
            if not body:
                continue
            markup, hits = body, count
        elif block.kind == "list":
            items = _filter_list(block.items, search)
            if not items:
                continue
            markup = list_html(items, search)
            hits = sum(1 for i in items if search.matches_any([s.text for s in i.spans]))
        else:
            text = "".join(s.text for s in block.spans)
            if not search.matches(text):
                continue
            markup = f"<p>{spans_html(block.spans, search)}</p>"
            hits = 1

        if pending_heading:
            parts.append(pending_heading)
            pending_heading = None
        parts.append(markup)
        shown += hits

    return '<div class="doc">' + "".join(parts) + "</div>", shown


def _drop_repeated_title(blocks: list[Block], title: str) -> list[Block]:
    """The page already shows the note title; don't print it twice."""
    if not blocks or not title or blocks[0].kind != "heading":
        return blocks
    first = "".join(s.text for s in blocks[0].spans)
    return blocks[1:] if fold(first) == fold(title) else blocks


def _pad(row: list[Cell], width: int) -> list[Cell]:
    return row + [Cell() for _ in range(width - len(row))]