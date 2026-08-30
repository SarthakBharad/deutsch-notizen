"""Colour, type and CSS.

Three colours are fixed by the brief. Everything else — surfaces, hairlines,
secondary text — is derived from them, and the dark palette is built by
rotating the same three: the light mode's text colour becomes the dark mode's
surface, so the two modes are one scheme seen from either end.

All of it goes through CSS variables, so the rules below are written once and
both modes fall out of the variable block.
"""

# --- fixed by the brief ----------------------------------------------------
BACKGROUND = "#E9EDF0"
TEXT = "#202A35"
ACCENT = "#B65C45"

LIGHT = {
    "bg": BACKGROUND,
    "ink": TEXT,
    "paper": "#F4F6F8",  # table and card surface, a step lighter than the page
    "line": "#C7D0D8",
    "line-soft": "#DBE2E7",
    "muted": "#5C6874",
    "accent": ACCENT,
    "accent-deep": "#8F4534",  # accent as text on a light surface
    "accent-wash": "rgba(182, 92, 69, 0.10)",
    "accent-edge": "rgba(182, 92, 69, 0.35)",
    "shade": "rgba(32, 42, 53, 0.04)",
    "shade-hover": "rgba(32, 42, 53, 0.03)",
}

DARK = {
    "bg": "#161E27",
    "ink": "#DCE3E9",
    "paper": "#1F2833",  # a shade off TEXT, which is where this palette starts
    "line": "#333F4C",
    "line-soft": "#28323D",
    "muted": "#8E9BA8",
    "accent": "#CE7A60",  # ACCENT lifted until it carries on a dark ground
    "accent-deep": "#E29478",
    "accent-wash": "rgba(206, 122, 96, 0.14)",
    "accent-edge": "rgba(206, 122, 96, 0.42)",
    "shade": "rgba(220, 227, 233, 0.05)",
    "shade-hover": "rgba(220, 227, 233, 0.04)",
}

FONTS = (
    "https://fonts.googleapis.com/css2"
    "?family=Newsreader:ital,opsz,wght@0,6..72,400;0,600;1,6..72,400"
    "&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400"
    "&family=IBM+Plex+Mono:wght@400;500&display=swap"
)

SERIF = "'Newsreader', Georgia, 'Times New Roman', serif"
SANS = "'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif"
MONO = "'IBM Plex Mono', 'SF Mono', Consolas, monospace"


def palette(dark: bool) -> dict:
    return DARK if dark else LIGHT


def css(dark: bool = False) -> str:
    variables = "\n  ".join(f"--{k}: {v};" for k, v in palette(dark).items())

    return f"""
<style>
@import url('{FONTS}');

:root {{
  {variables}
  --serif: {SERIF};
  --sans: {SANS};
  --mono: {MONO};
  --radius: 3px;
}}

/* ---------- page ---------- */
html, body, .stApp {{
  background: var(--bg) !important;
  color: var(--ink);
  font-family: var(--sans);
}}

/* Streamlit's toolbar floats over the page. Let the page colour through it
   and leave enough room underneath that nothing scrolls under the buttons. */
header[data-testid="stHeader"], .stApp > header {{ background: transparent !important; }}
[data-testid="stToolbar"] {{ background: transparent !important; }}
[data-testid="stToolbar"] svg, [data-testid="stMainMenu"] svg {{ color: var(--muted); fill: var(--muted); }}
[data-testid="stToolbar"] a, [data-testid="stToolbar"] span {{ color: var(--muted) !important; }}
[data-testid="stDecoration"] {{ display: none; }}

.block-container {{
  padding-top: 5.5rem !important;
  padding-bottom: 5rem;
  max-width: 1180px;
}}
[data-testid="stSidebarUserContent"] {{ padding-top: 1.2rem !important; }}

/* ---------- shared type ---------- */
.eyebrow, .note-kicker, .count, .level-card .meta,
.sidebar-level, table.grid th, tr.band td {{
  font-family: var(--mono); letter-spacing: .14em; text-transform: uppercase;
  font-size: .7rem; font-weight: 500;
}}

code, [data-testid="stMarkdownContainer"] code {{
  font-family: var(--mono) !important; font-size: .82em;
  background: var(--accent-wash) !important; color: var(--accent-deep) !important;
  padding: .12em .38em; border-radius: 2px;
}}

/* ---------- masthead ---------- */
.masthead {{ margin-bottom: 1.8rem; }}
.masthead .eyebrow {{ color: var(--accent); margin-bottom: .5rem; line-height: 1.4; }}
.masthead h1 {{
  font-family: var(--serif); font-weight: 600; font-size: 2.9rem;
  line-height: 1.08; margin: 0 0 .5rem 0; letter-spacing: -.01em; color: var(--ink);
}}
.masthead p {{ color: var(--muted); margin: 0; font-size: .98rem; max-width: 52ch; line-height: 1.6; }}

/* ---------- level cards ---------- */
.level-card {{
  border: 1px solid var(--line); border-left: 3px solid var(--accent);
  border-bottom: none; background: var(--paper);
  border-radius: var(--radius) var(--radius) 0 0;
  padding: 1.15rem 1.2rem 1rem; margin-bottom: 0;
}}
.level-card .code {{
  font-family: var(--serif); font-size: 2.4rem; font-weight: 600;
  line-height: 1; letter-spacing: -.02em; color: var(--ink);
}}
.level-card .meta {{ color: var(--muted); margin-top: .45rem; }}
.level-card .files {{ color: var(--muted); font-size: .88rem; margin-top: .6rem; line-height: 1.5; }}

/* Join the button to the card above it so they read as one block. */
div[data-testid="stElementContainer"]:has(.level-card) + div[data-testid="stElementContainer"] .stButton button {{
  border-radius: 0 0 var(--radius) var(--radius);
  border-left: 3px solid var(--accent); border-top: 1px solid var(--line-soft);
  background: var(--paper);
}}

/* ---------- note screen ---------- */
.note-kicker {{ color: var(--accent); margin-bottom: .45rem; }}
.note-title {{
  font-family: var(--serif); font-size: 2.1rem; font-weight: 600;
  margin: 0 0 1.4rem 0; letter-spacing: -.01em; color: var(--ink); line-height: 1.15;
}}
.count {{ color: var(--muted); margin: 0 0 .7rem 0; }}

.doc h2 {{
  font-family: var(--serif); font-size: 1.55rem; font-weight: 600; color: var(--ink);
  margin: 2rem 0 .7rem; padding-bottom: .3rem; border-bottom: 1px solid var(--line);
}}
.doc h2:first-child {{ margin-top: .2rem; }}
.doc h3 {{ font-family: var(--serif); font-size: 1.25rem; font-weight: 600; margin: 1.5rem 0 .5rem; color: var(--ink); }}
.doc h4 {{ font-family: var(--sans); font-size: 1rem; font-weight: 600; margin: 1.2rem 0 .4rem; color: var(--ink); }}
.doc p {{ margin: .45rem 0; line-height: 1.65; color: var(--ink); }}
.doc ul, .doc ol {{ margin: .5rem 0 .8rem; padding-left: 1.5rem; line-height: 1.65; color: var(--ink); }}
.doc li {{ margin: .2rem 0; padding-left: .2rem; }}
.doc li::marker {{ color: var(--muted); font-family: var(--mono); font-size: .85em; }}

/* An indented sub-item is always an example sentence for the rule above it,
   so it is set apart rather than just pushed right: italic, quieter, and
   hung off a rule in the accent colour. */
.doc ul.beispiel, .doc ol.beispiel {{
  margin: .35rem 0 .6rem 0; padding-left: 1.6rem;
  border-left: 2px solid var(--accent-edge); list-style: none;
}}
.doc .beispiel li {{
  font-style: italic; color: var(--muted); padding-left: 0; margin: .25rem 0;
}}
.doc .beispiel li::marker {{ content: none; }}
.doc .beispiel strong {{ font-style: normal; }}
.doc .beispiel mark.hit {{ font-style: normal; }}
.doc strong {{ font-weight: 600; color: var(--accent-deep); }}

/* ---------- tables ---------- */
.sheet-group {{ margin-bottom: 2rem; }}
.tbl-wrap {{
  overflow-x: auto; border: 1px solid var(--line);
  border-radius: var(--radius); background: var(--paper); margin-bottom: 1rem;
}}
table.grid {{ border-collapse: collapse; width: 100%; font-size: .92rem; color: var(--ink); }}
table.grid th {{
  text-align: left; color: var(--muted); background: var(--shade);
  padding: .6rem .8rem; border-bottom: 1px solid var(--line); white-space: nowrap;
}}
table.grid td {{
  padding: .48rem .8rem; border-bottom: 1px solid var(--line-soft);
  vertical-align: top; line-height: 1.45;
}}
table.grid tr:last-child td {{ border-bottom: none; }}
table.grid tbody tr:hover td {{ background: var(--shade-hover); }}
table.grid td.lead {{ font-weight: 500; }}
table.grid tr.spacer td, table.grid tr.spacer:hover td {{
  padding: .25rem; background: transparent; border-bottom: none;
}}

tr.band td, tr.band:hover td {{
  background: var(--accent-wash); color: var(--accent-deep);
  border-top: 1px solid var(--accent-edge); border-bottom: 1px solid var(--accent-edge);
  padding: .45rem .8rem;
}}

.art {{ color: var(--accent); font-weight: 500; }}
.aux {{ color: var(--muted); }}
mark.hit {{ background: var(--accent-edge); color: var(--ink); padding: 0 .1em; border-radius: 2px; }}

.empty {{
  border: 1px dashed var(--line); border-radius: var(--radius);
  padding: 1.4rem; color: var(--muted); font-size: .92rem; line-height: 1.6;
}}
.empty b {{ color: var(--ink); }}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {{ background: var(--paper); border-right: 1px solid var(--line); }}
section[data-testid="stSidebar"] * {{ color: var(--ink); }}
.sidebar-brand {{
  font-family: var(--serif); font-size: 1.35rem; font-weight: 600;
  color: var(--ink); margin: .3rem 0 .15rem;
}}
.sidebar-level {{ color: var(--accent) !important; margin-bottom: .9rem; }}

/* ---------- widgets ---------- */
.stButton button {{
  font-family: var(--sans); font-size: .9rem; font-weight: 400;
  background: transparent; color: var(--ink);
  border: 1px solid var(--line); border-radius: var(--radius);
  transition: border-color .12s ease, color .12s ease, background .12s ease;
}}
.stButton button:hover {{
  border-color: var(--accent); color: var(--accent) !important;
  background: var(--accent-wash);
}}
.stButton button:focus:not(:active) {{ border-color: var(--accent); color: var(--accent) !important; }}
.stButton button p {{ color: inherit !important; }}

[data-baseweb="input"], [data-baseweb="base-input"] {{
  background: var(--bg) !important; border-color: var(--line) !important;
  border-radius: var(--radius) !important;
}}
.stTextInput input {{ background: var(--bg) !important; color: var(--ink) !important; font-family: var(--sans); }}
.stTextInput input::placeholder {{ color: var(--muted) !important; opacity: 1; }}

[data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"] p,
.stCaption, .stCaption p {{ color: var(--muted) !important; font-size: .8rem; }}

.stRadio [role="radiogroup"] {{ gap: .1rem; }}
.stRadio label p {{ font-size: .92rem; color: var(--ink) !important; }}

hr, [data-testid="stDivider"] hr {{ border-color: var(--line) !important; background: var(--line); }}

/* Tabs: Streamlit builds these on react-aria (1.61+) and on BaseWeb before
   that, so both sets of hooks are covered. */
.stTabs [role="tablist"], .stTabs [data-baseweb="tab-list"] {{
  gap: .15rem; background: transparent;
}}
.stTabs [data-testid="stTab"], .stTabs [data-baseweb="tab"] {{
  /* Streamlit injects its emotion styles after this block, so ties in
     specificity go to it — these need !important to land. */
  font-family: var(--sans); color: var(--muted) !important; padding: .4rem .7rem;
  transition: color .12s ease, background .12s ease;
}}
/* the label sits in a nested <p> carrying Streamlit's own colour */
.stTabs [data-testid="stTab"] p, .stTabs [data-baseweb="tab"] p {{
  color: inherit !important; font-size: .89rem; font-family: var(--sans);
}}
.stTabs [data-testid="stTab"]:hover, .stTabs [data-baseweb="tab"]:hover {{
  color: var(--ink) !important; background: var(--shade-hover);
}}
.stTabs [role="tab"][aria-selected="true"], .stTabs [aria-selected="true"] {{
  color: var(--accent-deep) !important;
}}
.stTabs .react-aria-SelectionIndicator,
.stTabs [data-baseweb="tab-highlight"] {{ background: var(--accent) !important; }}
.stTabs [data-baseweb="tab-border"] {{ background: var(--line); }}

[data-testid="stTooltipHoverTarget"] svg {{ color: var(--muted); }}

/* download button — the one call to action, so it carries the accent */
.stDownloadButton button {{
  font-family: var(--sans); font-size: .9rem;
  background: var(--accent) !important; color: #FFF !important;
  border: 1px solid var(--accent) !important; border-radius: var(--radius);
}}
.stDownloadButton button:hover {{ background: var(--accent-deep) !important; border-color: var(--accent-deep) !important; }}
.stDownloadButton button p {{ color: #FFF !important; }}

/* the embedded PDF viewer sits on the page, so give it the same frame
   as a table rather than the browser's default white slab */
[data-testid="stPdf"], [data-testid="stPdfContainer"] {{
  border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--paper); overflow: hidden; margin-top: 1rem;
}}
[data-testid="stPdf"] iframe, [data-testid="stPdf"] embed {{ border: none; }}
</style>
"""