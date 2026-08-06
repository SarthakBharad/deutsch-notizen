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
5. The first non-band row of the first block is the header. Later blocks
   reuse it only if their column count matches.

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
            chunk = _trim_cols(chunk)
            if not chunk:
                continue

            block_header: list[Cell] | None = None
            body = chunk
            first_data = next((i for i, r in enumerate(chunk) if not is_band(r)), None)

            if first_data is not None:
                candidate = chunk[first_data]
                takes_row = group_header is None or _same_text(candidate, group_header)
                if takes_row:
                    block_header = candidate
                    body = chunk[:first_data] + chunk[first_data + 1 :]
                    if group_header is None:
                        group_header = candidate
                elif group_header is not None and len(candidate) == len(group_header):
                    # Same shape, different content: repeat the header so the
                    # columns stay legible without eating a row of notes.
                    block_header = group_header

            if any(not c.empty for row in body for c in row):
                group.blocks.append(TableBlock(header=block_header, rows=body))

        if group.blocks:
            groups.append(group)

    return groups


# --------------------------------------------------------------------------


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
