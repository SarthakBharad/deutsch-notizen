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

Drop `.ods` or `.odt` files into `notizen/`, named `<Level>_<Title>`:

```
notizen/
  A2_Deutsch_Cheatsheet.ods   ->  A2 · Deutsch Cheatsheet
  A2_Grammatik.odt            ->  A2 · Grammatik
  B1_Wortschatz_Extra.ods     ->  B1 · Wortschatz Extra
  C1_Konjunktiv.odt           ->  C1 · Konjunktiv
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

**Documents (`.odt`)** — headings, paragraphs, lists and tables in order.
Calc tables embedded in a Writer document (the `Beispiel Sätze` table in
`A2_Grammatik.odt`) are pulled out and rendered as real tables, not images.
Bold and italic survive.

## Reading aids

- **Search ignores umlauts.** `uber` finds `über`, `gruss` finds `Gruß`.
  In a cheatsheet it searches every sheet at once and keeps the `Lektion`
  band above each hit, so results stay in context.
- **The article is tinted** in vocabulary entries (`**der** Anfang`), and the
  perfect auxiliary is muted (`*hat* aufgemacht`) — gender and haben/sein are
  the two things a list like this exists to drill. Only lowercase entries are
  tinted, so example sentences starting with "Das…" are left alone.

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

Palette: background `#E9EDF0`, text `#202A35`, accent `#B65C45`.
Type: Newsreader for headings, IBM Plex Sans for text, IBM Plex Mono for
labels.
