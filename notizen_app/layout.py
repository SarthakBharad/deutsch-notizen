"""Recover structure from a hand-made spreadsheet.

A sheet in a cheatsheet is rarely one clean table. It is usually several
tables laid out side by side or stacked, separated by blank rows and columns,
with label rows ("Lektion - 1") running across. This module reconstructs that
intent so each piece can be rendered as its own table.

The rules, in order:

1. Trim blank rows and columns off the outside.
2. Split into column groups on runs of 2+ blank columns.
3. Split each group into blocks on runs of 2+ blank rows.
4. A row with exactly one filled cell is a band (a heading inside the table).
5. A row whose filled cells are mostly bold is a header row. A block is split
   again at every one of these, so a sheet that stacks Akkusativ over Dativ
   in one grid becomes two tables, each under its own header.
6. Otherwise the first non-band row of a block is taken as its header.
7. A header cell that spans rows is not a header at all — it is a label for
   the block beside it (the merged "Akkusativ"), so it moves into the body
   and keeps its rowspan there.

A single blank row or column is treated as breathing room, not a divide,
because that is how these sheets actually use them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .readers.odf import Cell, Grid

BLANK_RUN = 2  # blank rows/columns needed to count as a real separator


@dataclass
class TableBlock:
    header: list[Cell] | None
    rows: list[list[Cell]] = field(default_factory=list)


@dataclass
class SheetGroup:
    """One column group of a sheet: a stack of tables sharing a layout."""

    blocks: list[TableBlock] = field(default_factory=list)


# A header row has to be mostly bold, not entirely bold: a column added to a
# sheet later often misses the formatting of the ones beside it. Half is high
# enough to stay clear of a data row carrying a bold label down its side
# (Artikel's "Bestimmt", das Wetter's "Maskulin"), which run nearer a third.
HEADER_BOLD_SHARE = 0.5


def is_header_row(row: list[Cell]) -> bool:
    """Mostly bold, with at least two bold cells to go on."""
    filled = [c for c in row if not c.empty]
    if len(filled) < 3:
        return False
    bold = sum(1 for c in filled if c.bold)
    return bold >= 2 and bold >= HEADER_BOLD_SHARE * len(filled)


def is_band(row: list[Cell]) -> bool:
    """A label row: exactly one filled cell, in the first column or two."""
    filled = [i for i, c in enumerate(row) if not c.empty]
    return len(filled) == 1 and filled[0] <= 1


def band_text(row: list[Cell]) -> str:
    return next((c.text for c in row if not c.empty), "")


def structure(grid: Grid) -> list[SheetGroup]:
    rows = _rectangular(grid.rows)
    rows = _trim_rows(rows)
    if not rows:
        return []
    rows = _trim_cols(rows)
    if not rows or not rows[0]:
        return []

    groups: list[SheetGroup] = []

    for col_slice in _column_groups(rows):
        sub = _trim_rows([row[col_slice] for row in rows])
        if not sub:
            continue

        group = SheetGroup()
        group_header: list[Cell] | None = None  # each column group has its own

        for chunk in _row_blocks(sub):
            for piece in _split_on_headers(chunk):
                piece = _trim_cols(piece)
                if not piece:
                    continue

                block_header: list[Cell] | None = None
                body = piece
                first_data = next((i for i, r in enumerate(piece) if not is_band(r)), None)

                if first_data is not None:
                    candidate = piece[first_data]
                    takes_row = (
                        group_header is None
                        or is_header_row(candidate)
                        or _same_text(candidate, group_header)
                    )
                    if takes_row:
                        rest = piece[:first_data] + piece[first_data + 1 :]
                        block_header, body = _lift_header(candidate, rest)
                        if group_header is None:
                            group_header = block_header
                    elif group_header is not None and len(candidate) == len(group_header):
                        # Same shape, different content: repeat the header so
                        # the columns stay legible without eating a row.
                        block_header = group_header

                if any(not c.empty for row in body for c in row):
                    group.blocks.append(TableBlock(header=block_header, rows=body))

        if group.blocks:
            groups.append(group)

    return groups


# --------------------------------------------------------------------------


def _split_on_headers(rows: list[list[Cell]]) -> list[list[list[Cell]]]:
    """Cut a chunk before each interior all-bold row.

    If most of the chunk is bold the sheet is simply set in bold throughout,
    and the signal means nothing — so it is ignored rather than turning every
    row into its own table.
    """
    marks = [i for i, r in enumerate(rows) if is_header_row(r)]
    if not marks or len(marks) > max(1, len(rows) // 2):
        return [rows]

    pieces, start = [], 0
    for mark in marks:
        # a band sitting just above a header ("Teil - 1", "Länder") introduces
        # the table below it, so the cut goes above the band, not between them
        cut = mark
        while cut > 0 and _blank_row(rows[cut - 1]):
            cut -= 1
        while cut > 0 and is_band(rows[cut - 1]):
            cut -= 1
        if cut > start:
            pieces.append(rows[start:cut])
            start = cut
    pieces.append(rows[start:])
    return [p for p in pieces if any(not c.empty for row in p for c in row)]


def _lift_header(
    candidate: list[Cell], body: list[list[Cell]]
) -> tuple[list[Cell], list[list[Cell]]]:
    """Take a header row, leaving behind any cell that spans into the body.

    A merged label like "Akkusativ" sits in the same row as the column
    headings, because that is where a vertical merge puts its text. It is not
    a heading for its column, so it is pushed down into the first body row
    with one row of its span used up.
    """
    header = [Cell(c.text, c.colspan, 1, c.covered, c.bold) for c in candidate]
    if not body:
        return header, body

    body = [list(row) for row in body]
    for index, cell in enumerate(candidate):
        if cell.rowspan <= 1 or cell.empty:
            continue
        header[index] = Cell(bold=cell.bold)
        if index < len(body[0]):
            body[0][index] = Cell(
                cell.text, cell.colspan, min(cell.rowspan - 1, len(body)), False, cell.bold
            )
    return header, body


def _rectangular(rows: list[list[Cell]]) -> list[list[Cell]]:
    width = max((len(r) for r in rows), default=0)
    return [r + [Cell() for _ in range(width - len(r))] for r in rows]


def _blank_row(row: list[Cell]) -> bool:
    return all(c.empty for c in row)


def _trim_rows(rows: list[list[Cell]]) -> list[list[Cell]]:
    start, end = 0, len(rows)
    while start < end and _blank_row(rows[start]):
        start += 1
    while end > start and _blank_row(rows[end - 1]):
        end -= 1
    return rows[start:end]


def _trim_cols(rows: list[list[Cell]]) -> list[list[Cell]]:
    if not rows:
        return rows
    width = len(rows[0])
    filled = [i for i in range(width) if any(not r[i].empty for r in rows)]
    if not filled:
        return []
    lo, hi = filled[0], filled[-1] + 1
    return [r[lo:hi] for r in rows]


def _column_groups(rows: list[list[Cell]]) -> list[slice]:
    width = len(rows[0])
    blank = [all(r[i].empty for r in rows) for i in range(width)]
    return [slice(a, b) for a, b in _segments(blank)]


def _row_blocks(rows: list[list[Cell]]) -> list[list[list[Cell]]]:
    blank = [_blank_row(r) for r in rows]
    return [rows[a:b] for a, b in _segments(blank)]


def _segments(blank: list[bool]) -> list[tuple[int, int]]:
    """Index ranges of content, split on runs of BLANK_RUN or more blanks."""
    segments: list[tuple[int, int]] = []
    start = None
    run = 0
    for i, is_blank in enumerate(blank):
        if is_blank:
            run += 1
            if run >= BLANK_RUN and start is not None:
                segments.append((start, i - run + 1))
                start = None
        else:
            run = 0
            if start is None:
                start = i
    if start is not None:
        segments.append((start, len(blank)))
    return [(a, b) for a, b in segments if b > a]


def _same_width(a: list[Cell], b: list[Cell]) -> bool:
    return len(a) == len(b)


def _same_text(a: list[Cell], b: list[Cell]) -> bool:
    return [c.text.strip() for c in a] == [c.text.strip() for c in b]