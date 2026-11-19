#!/usr/bin/env python3
"""Build the generated files in template/, or a userspace copy.

Usage: python3 tools/build.py                    regenerate template/TimelineRail__{styles.css,doc,testcases}
       python3 tools/build.py --sandbox <User>   sandbox/<User>/: everything renamed under
                                                 User:<User>/Timeline sandbox (not tracked)

template/ holds the files to paste into Template:TimelineRail and its subpages. The six
template pages (TimelineRail, __item, __event, __parallel, __gap, __section) are edited
by hand there. The stylesheet is copied from prototype/timeline.css, the doc page is
tools/doc_source.wikitext with highlighted, rendered examples, and the testcases page is
the demo text in this file; never edit those three in template/.
"""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import real_examples

RELEASE = len(sys.argv) < 2
if not RELEASE and (sys.argv[1] != '--sandbox' or len(sys.argv) < 3):
    sys.exit(__doc__)
user = 'release' if RELEASE else sys.argv[2]
root = pathlib.Path(__file__).resolve().parent.parent
out = root / 'template' if RELEASE else root / 'sandbox' / user
out.mkdir(parents=True, exist_ok=True)

# Release: the real pages, Template:TimelineRail and its subpages.
BASE = 'TimelineRail' if RELEASE else f'User:{user}/Timeline sandbox'
PAGES = {  # file in template/ -> page title
    'TimelineRail.wikitext': BASE,
    'TimelineRail__item.wikitext': BASE + '/item',
    'TimelineRail__event.wikitext': BASE + '/event',
    'TimelineRail__parallel.wikitext': BASE + '/parallel',
    'TimelineRail__gap.wikitext': BASE + '/gap',
    'TimelineRail__section.wikitext': BASE + '/section',
}

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

def demo_examples(text):
    """Show every demo example as highlighted source followed by its rendering. (No {{Markupv}}: its shaded cell has a different background from the page, which shows through the section boxes.)
    Top-level template calls are found by counting braces; the long real-article
    example at the end is left as a plain rendering."""
    cut = text.index('== Examples from real articles ==')
    head, tail = text[:cut], text[cut:]
    out, i, depth, start = [], 0, 0, None
    while i < len(head):
        two = head[i:i + 2]
        if two == '{{':
            if depth == 0 and (i == 0 or head[i - 1] == '\n'):
                start = i
            depth += 1; i += 2
        elif two == '}}':
            depth -= 1; i += 2
            if depth == 0 and start is not None:
                code = head[start:i]
                out.append((start, i, code)); start = None
        else:
            i += 1
    res, pos = [], 0
    for a, b, code in out:
        res.append(head[pos:a])
        res.append('<syntaxhighlight lang="wikitext">\n' + code + '\n</syntaxhighlight>\n' + code)
        pos = b
    res.append(head[pos:])
    return ''.join(res) + tail

def doc_examples(text):
    """Release doc: syntax-highlighted source, with the rendered result next to it ({{Markup}}).
    An example that needs a file on the wiki (image=) gets the highlighted source only."""
    def one(m):
        code = m.group(1)
        hl = '<syntaxhighlight lang="wikitext">\n' + code + '\n</syntaxhighlight>'
        if 'image=' in code:
            return hl
        return hl + '\n' + code
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
if RELEASE:
    # The hand-edited template pages are already in template/; only the doc is generated here.
    doc = dedupe_ids(doc_examples((root / 'tools' / 'doc_source.wikitext').read_text()))
    (out / 'TimelineRail__doc.wikitext').write_text(doc)
    written.append(('Template:TimelineRail/doc', 'TimelineRail__doc.wikitext'))
else:
    for src, title in PAGES.items():
        body = clean((root / 'template' / src).read_text())
        path = out / (fname(title) + '.wikitext')
        path.write_text(body); written.append((title, path.name))

css = (root / 'prototype' / 'timeline.css').read_text()
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
A red dot marks a section. Click it to collapse everything inside. Sections can contain sections, to any depth; each level is indented a little. On a wide window the section title goes in the date column, like a date. A section can also carry text, and an image, beside its dot.

{{{{{BASE}
|{{{{{BASE}/section |title=Origins |text=How the game spread from China to Korea and Japan.
|{{{{{BASE}/item |date=1612 |title=The Go academy |text=The Tokugawa shogunate patronises the game and forms the houses of professional players.}}}}
{{{{{BASE}/section |title=Edo period
|{{{{{BASE}/item |date=1846 |title=The Ear-Reddening Game |text=Shusaku's move 127 stuns Gennan Inseki.}}}}
}}}}
}}}}
{{{{{BASE}/section |title=Modern era
|{{{{{BASE}/item |date=1924 |title=Nihon Ki-in founded |text=The Japanese Go association is founded in Tokyo.}}}}
{{{{{BASE}/section |title=Computer Go |text=Programs from the first hand-written engines to learning systems.
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
(out / fname(DEMO)).with_suffix('.wikitext').write_text(dedupe_ids(demo_examples(demo)))
written.append((DEMO, fname(DEMO) + '.wikitext'))

print(f'Wrote {len(written)} files to {out}\n')
for title, f in written:
    print(f'  {f:45s} -> {title}')

# The same stylesheet feeds the web component and the React component.
import subprocess
subprocess.run([sys.executable, str(root / 'tools' / 'sync_css.py')], check=True)
