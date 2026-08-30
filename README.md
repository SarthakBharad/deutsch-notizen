# Deutsch Notizen

A reader for my German notes. Nothing is hard-coded — the app reads the
LibreOffice files in `notizen/` directly, so the notes stay the source of
truth and the app is just a way to look at them.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Only dependency is Streamlit. The OpenDocument parsing uses the standard
library.

## Add notes

Drop `.ods`, `.odt` or `.pdf` files into `notizen/`, named `<Level>_<Title>`:

```
notizen/
  A2_Deutsch_Cheatsheet.ods   ->  A2 · Deutsch Cheatsheet
  A2_Grammatik.odt            ->  A2 · Grammatik
  B1_Wortschatz_Extra.ods     ->  B1 · Wortschatz Extra
  C1_Konjunktiv.odt           ->  C1 · Konjunktiv
  A2 Menschen Kursbuch.pdf    ->  A2 · Menschen Kursbuch (a book)
```

Levels A1–C2 get their own card on the start screen, in order. Anything that
doesn't start with a level code lands under **Sonstige**.

Edits to a file show up after **Reload from disk** in the sidebar (or a
restart). Nothing needs to be re-exported or converted.

## How the notes are read

**Spreadsheets (`.ods`)** — one tab per sheet. Each sheet is split back into
the tables it was drawn as:

| In the sheet | In the app |
| --- | --- |
| 2+ blank columns in a row | separate tables, stacked |
| 2+ blank rows | a new table below |
| 1 blank row or column | kept as spacing |
| a row with one filled cell (`Lektion – 1`) | a band across the table |
| the first full row | the header, repeated on later tables of the same width |

**PDFs** — treated as books rather than notes: there is nothing useful to
re-render in a scanned textbook. A book gets a download button and, where the
viewer component is installed, reads in the page. Books sort after notes in
the sidebar and are marked `· PDF`. Search doesn't apply to them, so the
search box is hidden while one is open. Anything over 25 MB asks for a click
before its bytes are read, so a large scan isn't pulled into memory on every
rerun.

**Documents (`.odt`)** — headings, paragraphs, lists and tables in order.
Numbered and bulleted lists keep their own markers, and nesting is preserved:
LibreOffice splits one visual list into several `<text:list>` elements
whenever the indent level changes, so those are stitched back together — which
is also what makes the numbering run 1..n rather than restarting at each
example sentence. An indented sub-item is rendered as a Beispielsatz: italic,
quieter, hung off a rule in the accent colour. Search keeps the parent rule
visible above any example sentence that matches.
Calc tables embedded in a Writer document (the `Beispiel Sätze` table in
`A2_Grammatik.odt`) are pulled out and rendered as real tables, not images.
Bold and italic survive.

## Reading aids

- **Search ignores umlauts.** `uber` finds `über`, `gruss` finds `Gruß`.
  In a cheatsheet it searches every sheet at once and keeps the `Lektion`
  band above each hit, so results stay in context.
- **The article is tinted** in vocabulary entries (`**der** Anfang`), and the
  perfect auxiliary is muted (`*hat* aufgemacht`) — gender and haben/sein are
  the two things a list like this exists to drill. Two guards keep it quiet:
  the entry must be lowercase, so a sentence starting "Das…" is left alone,
  and a word must follow, so the Artikel declension table — whose cells *are*
  the articles — stays plain.
- **Dark mode** toggles in the sidebar. It is the same three colours seen from
  the other end: the light mode's text colour becomes the dark surface, and
  the accent is lifted to `#CE7A60` so it still carries on a dark ground.

## Layout

```
app.py                     screens and routing
notizen/                   the notes themselves
notizen_app/
  library.py               finds files, reads level and title from the name
  layout.py                recovers table structure from a sheet
  render.py                HTML, search, highlighting
  theme.py                 palette and CSS
  readers/odf.py           OpenDocument parser (zip + XML, stdlib only)
.streamlit/config.toml     Streamlit theme colours
```

Palette: background `#E9EDF0`, text `#202A35`, accent `#B65C45` (dark mode in
`theme.py`, derived from the same three). Type: Newsreader for headings,
IBM Plex Sans for text, IBM Plex Mono for labels.

## Before you publish the PDFs

`.gitignore` excludes `notizen/*.pdf` by default. Course textbooks are
copyrighted by their publisher, and a public repo or a public Streamlit Cloud
app is redistribution — being able to download a scan from elsewhere doesn't
make it yours to hand out. Keeping them local costs nothing: the app reads them
straight from `notizen/`.

Two practical limits point the same way. GitHub rejects any file over 100 MB
outright and warns above 50 MB, and Streamlit Cloud pulls the whole repo on
every deploy, so a few hundred megabytes of scans makes deploys slow and can
exhaust the free tier's memory.

If you decide otherwise, delete the `notizen/*.pdf` line — but do it
deliberately, not by accident.

## Pin Streamlit

`theme.py` styles some of Streamlit's own widgets by their DOM hooks, and those
change between releases — tabs moved from BaseWeb to react-aria in 1.61, which
silently broke the old tab rules. Pin the version you tested against:

```bash
pip freeze | grep "^streamlit=="   # put that exact line in requirements.txt
```

If a future upgrade makes some widget look wrong, the tab rules in `theme.py`
show the pattern: cover both the old and new hooks, and use `!important`,
since Streamlit injects its own styles after this stylesheet.