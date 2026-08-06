"""Deutsch Notizen — a reader for my German notes.

Run with:  streamlit run app.py
Add notes by dropping .ods / .odt files into notizen/ named <Level>_<Title>.
"""

from __future__ import annotations

import os

import streamlit as st

from notizen_app import library, theme
from notizen_app.layout import structure
from notizen_app.readers import odf
from notizen_app.render import Search, document_html, sheet_html

NOTES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notizen")

st.set_page_config(page_title="Deutsch Notizen", page_icon="ẞ", layout="wide")

# The toggle's value is already in session state when the rerun starts, so the
# stylesheet for this run can be chosen before anything is drawn.
st.markdown(theme.css(dark=bool(st.session_state.get("dark", False))), unsafe_allow_html=True)


# --------------------------------------------------------------------------
# loading (cached on path + mtime, so editing a file and refreshing is enough)
# --------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def load_sheets(path: str, mtime: float):
    return [(g.name, structure(g)) for g in odf.read_spreadsheet(path)]


@st.cache_data(show_spinner=False)
def load_document(path: str, mtime: float):
    return odf.read_document(path)


# --------------------------------------------------------------------------
# routing
# --------------------------------------------------------------------------

state = st.session_state
state.setdefault("level", None)
state.setdefault("note", None)
state.setdefault("dark", False)


def open_level(level: str) -> None:
    state.level = level
    state.note = None


def go_home() -> None:
    state.level = None
    state.note = None


notes = library.scan(NOTES_DIR)
grouped = library.by_level(notes)


# --------------------------------------------------------------------------
# sidebar — present on every screen, so the chrome never shifts
# --------------------------------------------------------------------------


def appearance() -> None:
    st.divider()
    st.toggle("Dark mode", key="dark")


def home_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">Deutsch Notizen</div>', unsafe_allow_html=True)
        st.caption(
            f"{len(notes)} {'Datei' if len(notes) == 1 else 'Dateien'} in notizen/"
            if notes
            else "No files in notizen/ yet"
        )
        appearance()


def note_sidebar(level: str, items: list[library.Note]) -> tuple[library.Note, Search]:
    with st.sidebar:
        st.button("← All levels", on_click=go_home, use_container_width=True)
        st.markdown(
            '<div class="sidebar-brand">Deutsch Notizen</div>'
            f'<div class="sidebar-level">{level}</div>',
            unsafe_allow_html=True,
        )

        titles = [n.title for n in items]
        if state.note not in titles:
            state.note = titles[0]
        choice = st.radio("Notes", titles, key="note", label_visibility="collapsed")
        note = next(n for n in items if n.title == choice)

        st.divider()
        query = st.text_input(
            "Search", placeholder="Search this note…", label_visibility="collapsed"
        )
        st.caption("Umlauts optional — *uber* finds *über*.")

        st.divider()
        if st.button("Reload from disk", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        appearance()

    return note, Search(query)


# --------------------------------------------------------------------------
# screens
# --------------------------------------------------------------------------


def start_screen() -> None:
    home_sidebar()
    st.markdown(
        '<div class="masthead">'
        '<div class="eyebrow">Meine Notizen</div>'
        "<h1>Deutsch</h1>"
        "<p>Pick a level to read what's in it. Everything comes straight from "
        "the files in <code>notizen/</code>.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not grouped:
        empty_state(
            "No notes found yet. Put an .ods or .odt file in the "
            "<b>notizen</b> folder, named like <b>A2 Grammatik.odt</b>, and reload."
        )
        return

    levels = list(grouped)
    for start in range(0, len(levels), 3):
        for column, level in zip(st.columns(3), levels[start : start + 3]):
            items = grouped[level]
            with column:
                st.markdown(
                    f'<div class="level-card"><div class="code">{level}</div>'
                    f'<div class="meta">{len(items)} '
                    f'{"Datei" if len(items) == 1 else "Dateien"}</div>'
                    f'<div class="files">{" · ".join(n.title for n in items)}</div></div>',
                    unsafe_allow_html=True,
                )
                st.button(
                    f"Open {level}",
                    key=f"open-{level}",
                    use_container_width=True,
                    on_click=open_level,
                    args=(level,),
                )


def note_screen(level: str) -> None:
    note, search = note_sidebar(level, grouped[level])

    st.markdown(
        f'<div class="note-kicker">{level} · '
        f'{"Cheatsheet" if note.kind == "sheet" else "Dokument"}</div>'
        f'<div class="note-title">{note.title}</div>',
        unsafe_allow_html=True,
    )

    if note.kind == "sheet":
        render_sheet(note, search)
    else:
        render_document(note, search)


def render_sheet(note: library.Note, search: Search) -> None:
    try:
        sheets = load_sheets(note.path, note.mtime)
    except Exception as error:  # a half-saved or non-ODF file
        unreadable(note, error)
        return

    if not sheets:
        empty_state("This file has no sheets yet.")
        return

    names = [name or f"Sheet {i + 1}" for i, (name, _) in enumerate(sheets)]

    if search.active:
        # Searching looks across every sheet at once; tabs would hide the hits.
        total = 0
        rendered: list[tuple[str, str, int]] = []
        for name, groups in sheets:
            body, count = sheet_html(groups, search)
            if count:
                rendered.append((name, body, count))
                total += count

        if not total:
            count_line(f"No match for “{search.query}”")
            empty_state("Nothing in this file matches. Try a shorter word — the "
                        "search matches anywhere inside a cell.")
            return

        count_line(f"{total} matching {'row' if total == 1 else 'rows'} "
                   f"in {len(rendered)} {'sheet' if len(rendered) == 1 else 'sheets'}")
        for name, body, _ in rendered:
            st.markdown(f'<div class="doc"><h2>{name}</h2></div>', unsafe_allow_html=True)
            st.markdown(body, unsafe_allow_html=True)
        return

    for tab, (name, groups) in zip(st.tabs(names), sheets):
        with tab:
            body, count = sheet_html(groups, search)
            if body:
                count_line(f"{count} {'row' if count == 1 else 'rows'}")
                st.markdown(body, unsafe_allow_html=True)
            else:
                empty_state(
                    f"<b>{name}</b> is empty. Add rows in LibreOffice, save, "
                    "then hit Reload from disk."
                )


def render_document(note: library.Note, search: Search) -> None:
    try:
        blocks = load_document(note.path, note.mtime)
    except Exception as error:
        unreadable(note, error)
        return

    body, count = document_html(blocks, search, skip_title=f"{note.level} {note.title}")

    if not blocks or body == '<div class="doc"></div>':
        empty_state(
            "Nothing written here yet. Add to the file in LibreOffice, save, "
            "then hit Reload from disk."
        )
        return

    if search.active:
        if not count:
            count_line(f"No match for “{search.query}”")
            empty_state("Nothing in this document matches.")
            return
        count_line(f"{count} matching {'passage' if count == 1 else 'passages'}")

    st.markdown(body, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# small shared pieces
# --------------------------------------------------------------------------


def count_line(text: str) -> None:
    st.markdown(f'<p class="count">{text}</p>', unsafe_allow_html=True)


def empty_state(message: str) -> None:
    st.markdown(f'<div class="empty">{message}</div>', unsafe_allow_html=True)


def unreadable(note: library.Note, error: Exception) -> None:
    """One bad file should cost you that file, not the whole app."""
    empty_state(
        f"<b>{os.path.basename(note.path)}</b> could not be read. Open it in "
        "LibreOffice and save it again as ODF; if it was mid-save when it was "
        "committed, the copy in the repo is incomplete. Every other note still works."
    )
    st.caption(f"{type(error).__name__}: {error}")


# --------------------------------------------------------------------------

if state.level and state.level in grouped:
    note_screen(state.level)
else:
    start_screen()