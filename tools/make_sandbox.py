#!/usr/bin/env python3
"""Build a ready-to-paste userspace sandbox from template/.

Usage: python3 tools/make_sandbox.py <WikipediaUsername> [outdir]
       python3 tools/make_sandbox.py --release [outdir]    (Template-space files, into release/)

Writes one file per wiki page into sandbox/<username>/ (default), named
after the page it belongs to. Template names are rewritten to subpages of
User:<name>/Timeline sandbox, the TemplateStyles source points at the
stylesheet page in the Template namespace, and the {{documentation}} lines are dropped.
"""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import real_examples

RELEASE = sys.argv[1] == '--release'
user = 'release' if RELEASE else sys.argv[1]
root = pathlib.Path(__file__).resolve().parent.parent
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else root / ('release' if RELEASE else 'sandbox' / pathlib.Path(user))
out.mkdir(parents=True, exist_ok=True)

# In release mode the pages are the real ones: Template:TimelineRail and its subpages.
BASE = 'TimelineRail' if RELEASE else f'User:{user}/Timeline sandbox'
PAGES = {  # repo file -> page title
    'Template_TimelineRail.wikitext': BASE,
    'Template_TimelineRail_item.wikitext': BASE + '/item',
    'Template_TimelineRail_event.wikitext': BASE + '/event',
    'Template_TimelineRail_parallel.wikitext': BASE + '/parallel',
    'Template_TimelineRail_gap.wikitext': BASE + '/gap',
    'Template_TimelineRail_section.wikitext': BASE + '/section',
}
if RELEASE:
    PAGES['Template_TimelineRail_doc.wikitext'] = BASE + '/doc'

# Sanitized-CSS pages are created by title in the Template namespace; on English
# Wikipedia Special:ChangeContentModel is limited to admins and template editors.
STYLES = 'Template:TimelineRail/styles.css' if RELEASE else f'Template:{user}/Timeline sandbox/styles.css'

NAME = re.compile(r'\{\{TimelineRail(/item|/event|/parallel|/gap|/section)?(?=[\s|}])')
def rename(text):
    return NAME.sub(lambda m: '{{' + BASE + (m.group(1) or ''), text)

def dedupe_ids(text):
    """Toggle ids come from date + title, so repeats on one page would toggle each other.
    Give every repeated item an explicit id= (only the demo and doc pages repeat examples)."""
    seen, n = {}, [0]
    def one(m):
        line = m.group(0)
        t = re.search(r'\|(?:title|summary)=([^|}]*)', line)
        key = (m.group(1).strip(), t.group(1).strip() if t else '')
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 1 or '|id=' in line:
            return line
        n[0] += 1
        return line.replace('/item ', '/item |id=ex%d ' % n[0], 1)
    parts = re.split(r'(<syntaxhighlight.*?</syntaxhighlight>)', text, flags=re.S)  # shown source stays as written
    return ''.join(p if p.startswith('<syntaxhighlight') else
                   re.sub(r'\{\{[^{}\n]*?/item \|date=([^|}\n]*)[^\n]*', one, p) for p in parts)

def doc_examples(text):
    """Release doc: syntax-highlighted source, with the rendered result next to it ({{Markup}}).
    An example that needs a file on the wiki (image=) gets the highlighted source only."""
    def one(m):
        code = m.group(1)
        hl = '<syntaxhighlight lang="wikitext">\n' + code + '\n</syntaxhighlight>'
        if 'image=' in code:
            return hl
        return '{{Markup|' + hl + '|\n' + code + '\n}}'
    return '{{Documentation subpage}}\n' + re.sub(r'<pre>\n(.*?)\n</pre>', one, text, flags=re.S)

def clean(text):
    if RELEASE:
        return text
    text = text.replace('Template:TimelineRail/styles.css', STYLES)
    text = re.sub(r'\n?\{\{documentation[^}]*\}\}\n?', '\n', text)
    return rename(text)

def fname(title):
    return re.sub(r'^(?:User|Template):(?:' + re.escape(user) + '/)?', '', title).replace('/', '__').replace(' ', '_')

written = []
for src, title in PAGES.items():
    body = clean((root / 'template' / src).read_text())
    if RELEASE and src.endswith('_doc.wikitext'):
        body = dedupe_ids(doc_examples(body))
    path = out / (fname(title) + '.wikitext')
    path.write_text(body); written.append((title, path.name))

css = (root / 'template' / 'Template_TimelineRail_styles.css').read_text()
(out / (fname(STYLES))).write_text(css); written.append((STYLES, fname(STYLES)))

INTRO_LINKS = '' if RELEASE else ' Source and a live prototype: https://github.com/psygo/wikipedia_timeline (prototype at https://psygo.github.io/wikipedia_timeline/).'
demo = f'''This is a demonstration of a proposed template for vertical timelines. It needs no JavaScript: it is wikitext plus TemplateStyles, and it follows the reader's light or dark theme.{INTRO_LINKS} The sample content is only there to show the layout; check any dates before reusing them.

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

== Nested timelines ==
An item can hold its own timeline, indented under it, through the <code>sub</code> parameter.

{{{{{BASE}
|{{{{{BASE}/item |date=1960s–1990s |title=Hand-written programs |text=Engines encode Go knowledge by hand. |sub=
{{{{{BASE}/item |date=1968 |title=First Go program |text=Albert Zobrist writes a program able to play a full game.}}}}
{{{{{BASE}/item |date=1990s |title=Neural networks meet Go |text=Learning-based programs appear. |sub=
{{{{{BASE}/item |date=1994 |title=NeuroGo}}}}
{{{{{BASE}/item |date=1996 |title=Golem}}}}
}}}}
}}}}
{{{{{BASE}/item |date=2016 |title=AlphaGo defeats Lee Sedol |text=AlphaGo wins four games to one in Seoul.}}}}
}}}}

== Collapsible items ==
Every item is collapsible by default: click a dot or date to hide the item, and its title follows the date after a pipe. This uses MediaWiki's built-in collapsible feature, so the template needs no script. Add <code>collapsed=yes</code> to start collapsed, <code>collapsible=no</code> to switch it off for an item, and <code>summary=</code> to say what shows after the pipe for an item with several events.

{{{{{BASE}
|{{{{{BASE}/item |date=1612 |title=The Go academy |text=The Tokugawa shogunate patronises the game and forms the houses of professional players.}}}}
{{{{{BASE}/item |date=1846 |collapsed=yes |title=The Ear-Reddening Game |text=Shusaku's move 127 stuns Gennan Inseki.}}}}
{{{{{BASE}/item |date=2006 |summary=Crazy Stone and UCT |events=
{{{{{BASE}/event |title=Crazy Stone |text=Monte Carlo tree search arrives in Go.}}}}
{{{{{BASE}/event |title=UCT |text=The UCT algorithm is published.}}}}
}}}}
{{{{{BASE}/item |date=March 2016 |title=AlphaGo defeats Lee Sedol |text=AlphaGo wins four games to one in Seoul.}}}}
}}}}

== Timeline sections ==
A red dot marks a section. Click it to collapse everything inside. Sections can contain sections, to any depth; each level is indented a little.

{{{{{BASE}
|{{{{{BASE}/section |title=Origins
|{{{{{BASE}/item |date=1612 |title=The Go academy |text=The Tokugawa shogunate patronises the game and forms the houses of professional players.}}}}
{{{{{BASE}/section |title=Edo period
|{{{{{BASE}/item |date=1846 |title=The Ear-Reddening Game |text=Shusaku's move 127 stuns Gennan Inseki.}}}}
}}}}
}}}}
{{{{{BASE}/section |title=Modern era
|{{{{{BASE}/item |date=1924 |title=Nihon Ki-in founded |text=The Japanese Go association is founded in Tokyo.}}}}
{{{{{BASE}/section |title=Computer Go
|{{{{{BASE}/item |date=1968 |title=First Go program |text=Albert Zobrist writes a program able to play a full game.}}}}
{{{{{BASE}/section |title=Deep learning
|{{{{{BASE}/item |date=March 2016 |title=AlphaGo defeats Lee Sedol |text=AlphaGo wins four games to one in Seoul.}}}}
{{{{{BASE}/item |date=2017 |title=AlphaGo Zero |text=A version trained without human games is described in ''Nature''.}}}}
}}}}
}}}}
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
The same two timelines, grouped: the dots line up horizontally (at 640 px and wider; below that they fall back to the independent layout).

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
_inv = real_examples.wikitext(BASE)
demo += f'''
== Examples from real articles ==
The same list as it appears on English Wikipedia, rebuilt with this template. Text is adapted from [[Timeline of historic inventions]] (Paleolithic), under CC BY-SA 4.0; references are left out here.

=== Timeline of historic inventions ===
{_inv}

'''
DEMO = 'Template:TimelineRail/testcases' if RELEASE else f'User:{user}/Timeline demo'
(out / fname(DEMO)).with_suffix('.wikitext').write_text(dedupe_ids(demo))
written.append((DEMO, fname(DEMO) + '.wikitext'))

print(f'Wrote {len(written)} files to {out}\n')
for title, f in written:
    print(f'  {f:45s} -> {title}')
