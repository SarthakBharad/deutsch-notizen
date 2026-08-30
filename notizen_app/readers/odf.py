"""Minimal OpenDocument reader.

Both .ods and .odt are ZIP archives containing a ``content.xml``. This module
parses that XML directly with the standard library, so the app has no
dependency beyond Streamlit itself.

It handles the three things that actually matter for hand-written notes:
repeated cells/rows, merged cells, and Calc tables embedded inside a Writer
document (LibreOffice stores those as a nested document under ``Object N/``).
"""

from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
}

# A hand-made sheet never legitimately repeats a cell or row thousands of
# times; LibreOffice just pads the grid out to the end of the sheet. Cap the
# expansion so one padded row cannot balloon into a million cells.
MAX_REPEAT = 1024  # ceiling on any one repeat, so a stray value can't explode
MAX_BLANK_ROWS = 16  # interior blank rows kept, enough to spot a separator


def q(prefix: str, tag: str) -> str:
    """Build a Clark-notation tag name, e.g. q('table', 'table-cell')."""
    return "{%s}%s" % (NS[prefix], tag)


@dataclass
class Cell:
    text: str = ""
    colspan: int = 1
    rowspan: int = 1
    covered: bool = False  # swallowed by a merge above/left of it
    bold: bool = False

    @property
    def empty(self) -> bool:
        return not self.text.strip()


@dataclass
class Grid:
    """A rectangular table: the name plus its rows of cells."""

    name: str
    rows: list[list[Cell]] = field(default_factory=list)


@dataclass
class Span:
    """A run of inline text with its emphasis flags."""

    text: str
    bold: bool = False
    italic: bool = False


@dataclass
class ListItem:
    """One line of a list, with how deeply it is nested."""

    spans: list[Span]
    depth: int = 1  # 1 = top level
    ordered: bool = False


@dataclass
class Block:
    """One element in the flow of a text document."""

    kind: str  # "heading" | "paragraph" | "list" | "table"
    spans: list[Span] = field(default_factory=list)
    items: list[ListItem] = field(default_factory=list)  # for "list"
    grid: Grid | None = None  # for "table"
    level: int = 1  # for "heading"


# --------------------------------------------------------------------------
# text extraction
# --------------------------------------------------------------------------


def _inline_spans(el: ET.Element, styles: dict, bold=False, italic=False) -> list[Span]:
    """Flatten an element's inline content into styled spans."""
    out: list[Span] = []

    def push(txt: str, b: bool, i: bool):
        if not txt:
            return
        if out and out[-1].bold == b and out[-1].italic == i:
            out[-1].text += txt
        else:
            out.append(Span(txt, b, i))

    push(el.text or "", bold, italic)
    for child in el:
        tag = child.tag
        if tag == q("text", "s"):
            count = int(child.get(q("text", "c"), 1))
            push(" " * count, bold, italic)
        elif tag == q("text", "tab"):
            push("\t", bold, italic)
        elif tag == q("text", "line-break"):
            push("\n", bold, italic)
        elif tag in (q("text", "span"), q("text", "a")):
            st = styles.get(child.get(q("text", "style-name")), {})
            out.extend(
                _inline_spans(
                    child, styles, bold or st.get("bold", False), italic or st.get("italic", False)
                )
            )
        else:
            out.extend(_inline_spans(child, styles, bold, italic))
        push(child.tail or "", bold, italic)

    return out


def _plain_text(el: ET.Element) -> str:
    """All paragraph text under an element, one line per paragraph."""
    paras = el.findall(".//" + q("text", "p"))
    if not paras:
        return "".join(el.itertext()).strip()
    lines = ["".join(p.itertext()).strip() for p in paras]
    return "\n".join(line for line in lines if line).strip()


# --------------------------------------------------------------------------
# styles
# --------------------------------------------------------------------------


def _collect_cell_styles(root: ET.Element) -> dict[str, bool]:
    """{cell style name: is bold} — used to spot header rows in a sheet."""
    bold: dict[str, bool] = {}
    for style in root.iter(q("style", "style")):
        if style.get(q("style", "family")) != "table-cell":
            continue
        name = style.get(q("style", "name"))
        props = style.find(q("style", "text-properties"))
        if name:
            bold[name] = props is not None and props.get(q("fo", "font-weight")) == "bold"
    return bold


def _collect_styles(root: ET.Element) -> tuple[dict, dict]:
    """Return (text_styles, paragraph_styles) keyed by style name."""
    text_styles: dict[str, dict] = {}
    para_styles: dict[str, dict] = {}

    for style in root.iter(q("style", "style")):
        name = style.get(q("style", "name"))
        family = style.get(q("style", "family"))
        if not name:
            continue
        props = style.find(q("style", "text-properties"))
        info = {
            "parent": style.get(q("style", "parent-style-name"), ""),
            "bold": props is not None and props.get(q("fo", "font-weight")) == "bold",
            "italic": props is not None and props.get(q("fo", "font-style")) == "italic",
        }
        if family == "text":
            text_styles[name] = info
        elif family == "paragraph":
            para_styles[name] = info

    return text_styles, para_styles


def _collect_list_styles(root: ET.Element) -> dict[str, dict[int, bool]]:
    """{list style name: {level: is_ordered}} — numbered vs bulleted."""
    styles: dict[str, dict[int, bool]] = {}
    for ls in root.iter(q("text", "list-style")):
        name = ls.get(q("style", "name"))
        if not name:
            continue
        levels: dict[int, bool] = {}
        for child in ls:
            if not child.tag.startswith(q("text", "list-level-style-")):
                continue
            try:
                level = int(child.get(q("text", "level"), 1))
            except ValueError:
                continue
            levels[level] = child.tag == q("text", "list-level-style-number")
        styles[name] = levels
    return styles


def _heading_level(style_name: str, para_styles: dict) -> int | None:
    """Map a paragraph style (following its parents) to a heading level."""
    seen: set[str] = set()
    name = style_name
    while name and name not in seen:
        seen.add(name)
        base = name.replace("_20_", " ")
        if base == "Title":
            return 1
        if base == "Subtitle":
            return 2
        if base.startswith("Heading"):
            tail = base[len("Heading") :].strip()
            return int(tail) + 1 if tail.isdigit() else 2
        name = para_styles.get(name, {}).get("parent", "")
    return None


# --------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------


def _parse_table(el: ET.Element, bold_styles: dict[str, bool] | None = None) -> Grid:
    bold_styles = bold_styles or {}
    name = el.get(q("table", "name"), "")
    rows: list[list[Cell]] = []
    all_rows = list(el.iter(q("table", "table-row")))
    last_row = all_rows[-1] if all_rows else None

    for row_el in el.iter(q("table", "table-row")):
        cells: list[Cell] = []
        children = list(row_el)
        for index, cell_el in enumerate(children):
            covered = cell_el.tag == q("table", "covered-table-cell")
            if cell_el.tag != q("table", "table-cell") and not covered:
                continue
            text = _plain_text(cell_el)
            bold = bold_styles.get(cell_el.get(q("table", "style-name")), False)
            repeat = int(cell_el.get(q("table", "number-columns-repeated"), 1))
            if not text.strip():
                # LibreOffice pads every row out to the width of the sheet with
                # one hugely repeated blank cell at the end. Drop that padding,
                # but keep interior blank runs exact — they position the columns
                # that come after them.
                repeat = 1 if index == len(children) - 1 else min(repeat, MAX_REPEAT)
            cells.append(
                Cell(
                    text=text,
                    colspan=int(cell_el.get(q("table", "number-columns-spanned"), 1)),
                    rowspan=int(cell_el.get(q("table", "number-rows-spanned"), 1)),
                    covered=covered,
                    bold=bold,
                )
            )
            for _ in range(repeat - 1):
                cells.append(Cell(text=text, covered=covered, bold=bold))

        while cells and cells[-1].empty:
            cells.pop()

        row_repeat = int(row_el.get(q("table", "number-rows-repeated"), 1))
        if not cells:
            # Same padding trick, one dimension up: the sheet ends with a single
            # blank row repeated to the bottom. Interior blank runs are kept, so
            # a deliberate gap between two tables still reads as a gap.
            row_repeat = 1 if row_el is last_row else min(row_repeat, MAX_BLANK_ROWS)
        for _ in range(min(row_repeat, MAX_REPEAT)):
            rows.append(
                [Cell(c.text, c.colspan, c.rowspan, c.covered, c.bold) for c in cells]
            )

    while rows and not any(not c.empty for c in rows[-1]):
        rows.pop()

    return Grid(name=name, rows=rows)


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------


def read_spreadsheet(path: str) -> list[Grid]:
    """Every sheet in an .ods, in document order."""
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("content.xml"))
    bold_styles = _collect_cell_styles(root)
    return [_parse_table(t, bold_styles) for t in root.iter(q("table", "table"))]


def read_document(path: str) -> list[Block]:
    """The flow of an .odt as an ordered list of blocks."""
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("content.xml"))
        text_styles, para_styles = _collect_styles(root)
        list_styles = _collect_list_styles(root)

        body = root.find(q("office", "body"))
        text_body = body.find(q("office", "text")) if body is not None else None
        if text_body is None:
            return []

        blocks: list[Block] = []
        for el in text_body:
            blocks.extend(_document_block(el, zf, text_styles, para_styles, list_styles))
        return _merge_lists(blocks)


def _merge_lists(blocks: list[Block]) -> list[Block]:
    """Join lists that were only split apart by nesting or continued numbering.

    LibreOffice ends one <text:list> and starts another whenever the level
    changes, and ties them back together with text:continue-list. On the page
    they are one list, so they are merged back into one here — which is also
    what makes the numbering run 1..n instead of restarting at each break.
    """
    merged: list[Block] = []
    for block in blocks:
        if block.kind == "list" and merged and merged[-1].kind == "list":
            merged[-1].items.extend(block.items)
        else:
            merged.append(block)
    return merged


def _list_items(
    el: ET.Element,
    text_styles: dict,
    list_styles: dict,
    style_name: str,
    depth: int = 1,
) -> list[ListItem]:
    """Flatten a list, and any list nested inside it, keeping the depth.

    LibreOffice writes an indented sub-list as a list whose only item is
    another list, with no text of its own — so this has to recurse rather
    than read one level of list-item paragraphs.
    """
    style_name = el.get(q("text", "style-name")) or style_name
    ordered = list_styles.get(style_name, {}).get(depth, False)

    items: list[ListItem] = []
    for item in el.findall(q("text", "list-item")):
        spans: list[Span] = []
        for child in item:
            if child.tag == q("text", "p"):
                spans.extend(_inline_spans(child, text_styles))
            elif child.tag == q("text", "list"):
                if _joined(spans):
                    items.append(ListItem(spans, depth, ordered))
                    spans = []
                items.extend(
                    _list_items(child, text_styles, list_styles, style_name, depth + 1)
                )
        if _joined(spans):
            items.append(ListItem(spans, depth, ordered))

    return items


def _document_block(el, zf, text_styles, para_styles, list_styles) -> list[Block]:
    tag = el.tag

    if tag == q("text", "h"):
        level = int(el.get(q("text", "outline-level"), 1)) + 1
        spans = _inline_spans(el, text_styles)
        return [Block("heading", spans=spans, level=min(level, 5))] if _joined(spans) else []

    if tag == q("text", "p"):
        embedded = _embedded_grids(el, zf)
        if embedded:
            return [Block("table", grid=g) for g in embedded]
        style = el.get(q("text", "style-name"), "")
        spans = _inline_spans(el, text_styles)
        if not _joined(spans):
            return []
        level = _heading_level(style, para_styles)
        if level is not None:
            return [Block("heading", spans=spans, level=min(level, 5))]
        st = para_styles.get(style, {})
        if st.get("bold") or st.get("italic"):
            for s in spans:
                s.bold = s.bold or st.get("bold", False)
                s.italic = s.italic or st.get("italic", False)
        return [Block("paragraph", spans=spans)]

    if tag == q("text", "list"):
        items = _list_items(el, text_styles, list_styles, el.get(q("text", "style-name"), ""))
        return [Block("list", items=items)] if items else []

    if tag == q("table", "table"):
        return [Block("table", grid=_parse_table(el))]

    if tag in (q("draw", "frame"), q("draw", "g")):
        return [Block("table", grid=g) for g in _embedded_grids(el, zf)]

    return []


def _embedded_grids(el: ET.Element, zf: zipfile.ZipFile) -> list[Grid]:
    """Pull tables out of Calc objects embedded in a Writer document."""
    grids: list[Grid] = []
    for obj in el.iter(q("draw", "object")):
        href = (obj.get(q("xlink", "href")) or "").lstrip("./")
        if not href:
            continue
        inner = f"{href}/content.xml"
        if inner not in zf.namelist():
            continue
        try:
            sub = ET.fromstring(zf.read(inner))
        except ET.ParseError:
            continue
        for table in sub.iter(q("table", "table")):
            grid = _parse_table(table)
            if grid.rows:
                grid.name = ""  # "Sheet1" is noise inside a document
                grids.append(grid)
    return grids


def _joined(spans: list[Span]) -> str:
    return "".join(s.text for s in spans).strip()