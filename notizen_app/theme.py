"""Colour, type and CSS.

Three colours are fixed by the brief; everything else is derived from them so
the palette stays coherent when new surfaces are added.
"""

BACKGROUND = "#E9EDF0"
TEXT = "#202A35"
ACCENT = "#B65C45"

# Derived tones
PAPER = "#F4F6F8"  # table and card surface, a step lighter than the page
LINE = "#C7D0D8"  # hairlines
LINE_SOFT = "#DBE2E7"
MUTED = "#5C6874"  # secondary text, between TEXT and BACKGROUND
ACCENT_DEEP = "#8F4534"
ACCENT_WASH = "rgba(182, 92, 69, 0.10)"
ACCENT_EDGE = "rgba(182, 92, 69, 0.35)"

FONTS = (
    "https://fonts.googleapis.com/css2"
    "?family=Newsreader:ital,opsz,wght@0,6..72,400;0,600;1,6..72,400"
    "&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400"
    "&family=IBM+Plex+Mono:wght@400;500&display=swap"
)

SERIF = "'Newsreader', Georgia, 'Times New Roman', serif"
SANS = "'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif"
MONO = "'IBM Plex Mono', 'SF Mono', Consolas, monospace"


def css() -> str:
    return f"""
<style>
@import url('{FONTS}');

:root {{
  --bg: {BACKGROUND};
  --ink: {TEXT};
  --accent: {ACCENT};
  --accent-deep: {ACCENT_DEEP};
  --accent-wash: {ACCENT_WASH};
  --accent-edge: {ACCENT_EDGE};
  --paper: {PAPER};
  --line: {LINE};
  --line-soft: {LINE_SOFT};
  --muted: {MUTED};
  --serif: {SERIF};
  --sans: {SANS};
  --mono: {MONO};
}}

html, body, [class*="css"], .stApp {{
  background: var(--bg);
  color: var(--ink);
  font-family: var(--sans);
}}

.block-container {{ padding-top: 2.2rem; padding-bottom: 5rem; max-width: 1180px; }}

/* ---------- masthead ---------- */
.masthead {{ margin-bottom: 1.6rem; }}
.masthead .eyebrow {{
  font-family: var(--mono); font-size: .72rem; letter-spacing: .18em;
  text-transform: uppercase; color: var(--accent); margin-bottom: .35rem;
}}
.masthead h1 {{
  font-family: var(--serif); font-weight: 600; font-size: 2.9rem;
  line-height: 1.05; margin: 0 0 .4rem 0; letter-spacing: -.01em;
}}
.masthead p {{ color: var(--muted); margin: 0; font-size: .98rem; max-width: 46ch; }}

/* ---------- level cards on the start screen ---------- */
.level-card {{
  border: 1px solid var(--line); border-left: 3px solid var(--accent);
  background: var(--paper); border-radius: 3px;
  padding: 1.1rem 1.2rem .9rem; margin-bottom: .55rem;
}}
.level-card .code {{
  font-family: var(--serif); font-size: 2.4rem; font-weight: 600;
  line-height: 1; letter-spacing: -.02em;
}}
.level-card .meta {{
  font-family: var(--mono); font-size: .72rem; letter-spacing: .1em;
  text-transform: uppercase; color: var(--muted); margin-top: .35rem;
}}
.level-card .files {{ color: var(--muted); font-size: .88rem; margin-top: .5rem; line-height: 1.5; }}

/* ---------- headings inside a note ---------- */
.note-title {{
  font-family: var(--serif); font-size: 2.1rem; font-weight: 600;
  margin: 0 0 .15rem 0; letter-spacing: -.01em;
}}
.note-kicker {{
  font-family: var(--mono); font-size: .72rem; letter-spacing: .16em;
  text-transform: uppercase; color: var(--accent); margin-bottom: 1.3rem;
}}
.doc h2 {{
  font-family: var(--serif); font-size: 1.55rem; font-weight: 600;
  margin: 2rem 0 .7rem; padding-bottom: .3rem; border-bottom: 1px solid var(--line);
}}
.doc h3 {{ font-family: var(--serif); font-size: 1.25rem; font-weight: 600; margin: 1.5rem 0 .5rem; }}
.doc h4 {{ font-family: var(--sans); font-size: 1rem; font-weight: 600; margin: 1.2rem 0 .4rem; }}
.doc p {{ margin: .45rem 0; line-height: 1.65; }}
.doc ul {{ margin: .4rem 0 .8rem 1.1rem; line-height: 1.65; }}
.doc strong {{ font-weight: 600; color: var(--accent-deep); }}

/* ---------- tables ---------- */
.sheet-group {{ margin-bottom: 2rem; }}
.tbl-wrap {{
  overflow-x: auto; border: 1px solid var(--line);
  border-radius: 3px; background: var(--paper); margin-bottom: 1rem;
}}
table.grid {{ border-collapse: collapse; width: 100%; font-size: .92rem; }}
table.grid th {{
  font-family: var(--mono); font-size: .7rem; font-weight: 500;
  letter-spacing: .1em; text-transform: uppercase; text-align: left;
  color: var(--muted); background: rgba(32, 42, 53, .04);
  padding: .6rem .8rem; border-bottom: 1px solid var(--line);
  white-space: nowrap;
}}
table.grid td {{
  padding: .48rem .8rem; border-bottom: 1px solid var(--line-soft);
  vertical-align: top; line-height: 1.45;
}}
table.grid tr:last-child td {{ border-bottom: none; }}
table.grid tr:hover td {{ background: rgba(32, 42, 53, .03); }}
table.grid td.lead {{ font-weight: 500; }}
table.grid tr.spacer td {{ padding: .25rem; background: transparent; border-bottom: none; }}
table.grid tr.spacer:hover td {{ background: transparent; }}

tr.band td {{
  background: var(--accent-wash); border-bottom: 1px solid var(--accent-edge);
  border-top: 1px solid var(--accent-edge);
  font-family: var(--mono); font-size: .72rem; font-weight: 500;
  letter-spacing: .12em; text-transform: uppercase; color: var(--accent-deep);
  padding: .45rem .8rem;
}}
tr.band:hover td {{ background: var(--accent-wash); }}

/* gender article and perfect auxiliary — the two things worth memorising */
.art {{ color: var(--accent); font-weight: 500; }}
.aux {{ color: var(--muted); }}

mark.hit {{ background: var(--accent-edge); color: var(--ink); padding: 0 .1em; border-radius: 2px; }}

/* ---------- misc ---------- */
.empty {{
  border: 1px dashed var(--line); border-radius: 3px; background: transparent;
  padding: 1.4rem; color: var(--muted); font-size: .92rem;
}}
.count {{ font-family: var(--mono); font-size: .72rem; letter-spacing: .1em;
  text-transform: uppercase; color: var(--muted); margin: 0 0 .6rem 0; }}

section[data-testid="stSidebar"] {{ background: var(--paper); border-right: 1px solid var(--line); }}
section[data-testid="stSidebar"] h2 {{ font-family: var(--serif); font-size: 1.3rem; }}
.stTabs [data-baseweb="tab-list"] {{ gap: .2rem; border-bottom: 1px solid var(--line); }}
.stTabs [data-baseweb="tab"] {{ font-family: var(--sans); font-size: .9rem; }}
.stTabs [aria-selected="true"] {{ color: var(--accent-deep); }}
</style>
"""
