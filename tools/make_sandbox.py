#!/usr/bin/env python3
"""Build a ready-to-paste userspace sandbox from template/.

Usage: python3 tools/make_sandbox.py <WikipediaUsername> [outdir]

Writes one file per wiki page into sandbox/<username>/ (default), named
after the page it belongs to. Template names are rewritten to subpages of
User:<name>/Timeline sandbox, the TemplateStyles source points at the
stylesheet page in the Template namespace, and the {{documentation}} lines are dropped.
"""
import pathlib, re, sys

user = sys.argv[1]
root = pathlib.Path(__file__).resolve().parent.parent
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else root / 'sandbox' / user
out.mkdir(parents=True, exist_ok=True)

BASE = f'User:{user}/Timeline sandbox'
PAGES = {  # repo file -> page title
    'Template_Timeline.wikitext': BASE,
    'Template_Timeline_item.wikitext': BASE + '/item',
    'Template_Timeline_event.wikitext': BASE + '/event',
    'Template_Timeline_parallel.wikitext': BASE + '/parallel',
    'Template_Timeline_gap.wikitext': BASE + '/gap',
}
# Sanitized-CSS pages are created by title in the Template namespace; on English
# Wikipedia Special:ChangeContentModel is limited to admins and template editors.
STYLES = f'Template:{user}/Timeline sandbox/styles.css'

NAME = re.compile(r'\{\{Timeline( item| event| parallel| gap)?(?=[\s|}])')
def rename(text):
    return NAME.sub(lambda m: '{{' + BASE + (('/' + m.group(1).strip()) if m.group(1) else ''), text)

def clean(text):
    text = text.replace('Template:Timeline/styles.css', STYLES)
    text = re.sub(r'\n?\{\{documentation\}\}\n?', '\n', text)
    return rename(text)

def fname(title):
    return re.sub(r'^(User|Template):' + re.escape(user) + '/', '', title).replace('/', '__').replace(' ', '_')

written = []
for src, title in PAGES.items():
    body = clean((root / 'template' / src).read_text())
    path = out / (fname(title) + '.wikitext')
    path.write_text(body); written.append((title, path.name))

css = (root / 'template' / 'Template_Timeline_styles.css').read_text()
(out / (fname(STYLES))).write_text(css); written.append((STYLES, fname(STYLES)))

demo = f'''This is a demonstration of a proposed template for vertical timelines. It needs no JavaScript: it is wikitext plus TemplateStyles, and it follows the reader's light or dark theme. Source and a live prototype: https://github.com/psygo/wikipedia_timeline (prototype at https://psygo.github.io/wikipedia_timeline/). The sample content is only there to show the layout; check any dates before reusing them.

== Simple timeline ==
{{{{{BASE}
|{{{{{BASE}/item |date=1612 |title=The Go academy |text=The Tokugawa shogunate patronises the game and forms the houses of professional players.}}}}
{{{{{BASE}/item |date=1846 |title=The Ear-Reddening Game |text=Shusaku's move 127 stuns Gennan Inseki.}}}}
{{{{{BASE}/item |date=March 2016 |title=AlphaGo defeats Lee Sedol |text=AlphaGo wins four games to one in Seoul.}}}}
}}}}

== Several events on one dot ==
{{{{{BASE}
|{{{{{BASE}/item |date=2006 |events=
{{{{{BASE}/event |title=Crazy Stone |text=Monte Carlo tree search is applied to Go.}}}}
{{{{{BASE}/event |title=UCT |text=The UCT algorithm is published.}}}}
}}}}
}}}}

== Parallel timelines ==
Independent timelines that share a row and wrap when there is no room. Narrow the window to see them wrap.

{{{{{BASE}/parallel
|{{{{{BASE} |title=Players
|{{{{{BASE}/item |date=1846 |title=The Ear-Reddening Game}}}}
{{{{{BASE}/item |date=March 2016 |title=Lee Sedol wins game 4}}}}
}}}}
{{{{{BASE} |title=Programs
|{{{{{BASE}/item |date=1968 |title=First Go program}}}}
{{{{{BASE}/item |date=March 2016 |title=AlphaGo wins the match}}}}
}}}}
}}}}

== Parallel and grouped timelines ==
The same two timelines, grouped: the dots line up horizontally (needs a browser with CSS subgrid).

{{{{{BASE}/parallel |grouped=yes
|{{{{{BASE} |title=Players
|{{{{{BASE}/item |date=1846 |title=The Ear-Reddening Game}}}}
{{{{{BASE}/gap}}}}
{{{{{BASE}/item |date=March 2016 |title=Lee Sedol wins game 4}}}}
}}}}
{{{{{BASE} |title=Programs
|{{{{{BASE}/gap}}}}
{{{{{BASE}/item |date=1968 |title=First Go program}}}}
{{{{{BASE}/item |date=March 2016 |title=AlphaGo wins the match}}}}
}}}}
}}}}
'''
DEMO = f'User:{user}/Timeline demo'
(out / fname(DEMO)).with_suffix('.wikitext').write_text(demo)
written.append((DEMO, fname(DEMO) + '.wikitext'))

print(f'Wrote {len(written)} files to {out}\n')
for title, f in written:
    print(f'  {f:45s} -> {title}')
