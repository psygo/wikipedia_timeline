#!/usr/bin/env python3
"""Draft: "Timeline of first images of Earth from space" rebuilt with TimelineRail.

Usage: python3 tools/convert_first_images.py [--outline [--module=NAME]] [--article] [out.wikitext]

With --article the output is the text to paste into the real article: Module:TimelineRail and
Module:ViewSwitcher (not the /sandbox ones), the article's own table as the List view, no
{{User sandbox}} banner and no draft comment, the categories left live. Written to
drafts/Timeline_of_first_images_of_Earth_from_space__article.wikitext.

With --outline the timeline is written for the Lua module: one {{#invoke:NAME|outline|text=...}}
(NAME is TimelineRail/sandbox until Module:TimelineRail is live) instead of the template family.

Fetches the current wikitext of the article from English Wikipedia, turns its table
(image | date | craft or mission | event) into {{TimelineRail}}: one section per craft or mission, with one item per row, and keeps the
lead, See also, Notes and References as they are. Output goes to
drafts/Timeline_of_first_images_of_Earth_from_space.wikitext by default.

The text is copied from Wikipedia (CC BY-SA 4.0): when you save the draft, say so in the
edit summary (see the message printed at the end).
"""
import pathlib, re, subprocess, sys, urllib.parse

ARTICLE = 'Timeline of first images of Earth from space'
root = pathlib.Path(__file__).resolve().parent.parent
ARTICLE_MODE = '--article' in sys.argv[1:]
if ARTICLE_MODE:
    sys.argv += ['--outline'] + ([] if any(a.startswith('--switcher') for a in sys.argv) else ['--switcher'])
FLAGS = [a for a in sys.argv[1:] if a.startswith('--')]
from outline_call import invoke
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
OUTLINE = '--outline' in FLAGS
MODULE = next((f.split('=', 1)[1] for f in FLAGS if f.startswith('--module=')), 'TimelineRail' if ARTICLE_MODE else 'TimelineRail/sandbox')
out = pathlib.Path(ARGS[0]) if ARGS else root / 'drafts' / (ARTICLE.replace(' ', '_') + ('__article' if ARTICLE_MODE else '__lua' if OUTLINE else '') + '.wikitext')
BASE = 'TimelineRail'

from wp_fetch import fetch_article
wt = fetch_article(ARTICLE)
if '{|' not in wt:
    sys.exit('Could not fetch the article wikitext')

head, rest = wt.split('{|', 1)
table, tail = rest.split('\n|}', 1)
head = head.rsplit('== Timeline ==', 1)[0]

# ---------------------------------------------------------------- table -> rows -> cells
def depth_open(buf):
    """True while a {{template}} or <ref> is still open in buf."""
    if buf.count('{{') > buf.count('}}'):
        return True
    opens = len(re.findall(r'<ref(?:\s[^>]*[^/>])?>', buf))
    return opens > len(re.findall(r'</ref>', buf))

rows, cur, cells, buf = [], None, None, None
for line in table.split('\n')[1:]:          # first line holds the table attributes
    in_cell = buf is not None and depth_open(buf)
    if not in_cell and line.startswith('|-'):
        if buf is not None:
            cells.append(buf)
        if cells:
            rows.append(cells)
        cells, buf = [], None
    elif not in_cell and line.startswith('!'):
        continue                            # header row
    elif not in_cell and line.startswith('|'):
        if buf is not None:
            cells.append(buf)
        buf = line[1:]
        if cells is None:
            cells = []
    elif buf is not None:
        buf += '\n' + line
if buf is not None:
    cells.append(buf)
if cells:
    rows.append(cells)

# Rows that skip columns because of rowspan: expand them to 4 columns.
carry, pending, table_rows = [None] * 4, [0] * 4, []
for r in rows:
    it, full = iter(r), []
    for c in range(4):
        if pending[c] > 0:
            full.append(carry[c]); pending[c] -= 1
            continue
        raw = next(it, '')
        m = re.match(r'\s*rowspan="?(\d+)"?[^|]*\|(?!\|)(.*)', raw, re.S)
        span = 1
        if m:
            span, raw = int(m.group(1)), m.group(2)
        raw = raw.strip()
        full.append(raw)
        if span > 1:
            carry[c], pending[c] = raw, span - 1
    table_rows.append(full)

# ---------------------------------------------------------------- cells -> items
REF = re.compile(r'<ref(?:\s[^>]*)?/>|<ref(?:\s[^>]*)?>.*?</ref>', re.S)
FILE = re.compile(r'\[\[(?:File|Image):([^|\]]+)(?:\|[^\]]*)?\]\]')

def one_line(s):
    return re.sub(r'\s*\n\s*', ' ', s).strip()

def bare_pipes(text):
    """Count | outside [[ ]], {{ }} and <ref>: inside {{#invoke:...|text=...}} each one would end the
    argument, and everything after it would be lost."""
    text = re.sub(r'<ref(?:\s[^>]*[^/>])?>.*?</ref>', '', text, flags=re.S)
    depth = n = 0
    for two in re.findall(r'\[\[|\{\{|\]\]|\}\}|\|', text):
        if two in ('[[', '{{'): depth += 1
        elif two in (']]', '}}'): depth -= 1
        elif depth == 0: n += 1
    return n

def parse_media(cell):
    """Split the image cell: the first picture (a template parameter), other files (framed like
    the picture), and whatever else the cell holds ({{external media}}, {{Image requested
    inline}}, "See article"), which is kept as the article has it."""
    files = [f.strip() for f in FILE.findall(cell)]
    image = next((f for f in files if not re.search(r'\.(ogg|oga|ogv|webm|mp3|wav)$', f, re.I)), '')
    # Videos and audio get the same frame as the image (the template's image box).
    extra = ['<span class="wt-timeline__image">[[File:%s|200px]]</span>' % f for f in files if f != image]
    rest = re.sub(r'<br\s*/?>', ' ', FILE.sub('', cell))
    rest = re.sub(r'float\s*=\s*(left|right)', 'float = none', rest)   # no floating inside the text
    rest = re.sub(r'\s*\|\s*$', '', one_line(rest))   # the article has a stray | after a template; harmless in a table, fatal in an argument
    if rest:
        extra.append(rest)
    others = [f for f in files if f != image]
    return image, extra, others, rest

sections = []   # [craft, [ (date, text, image) ... ]]  one section per run of rows with the same craft
for img, date, craft, event in table_rows:
    refs = ''.join(REF.findall(date))
    date = one_line(REF.sub('', date)) or '?'
    craft = one_line(REF.sub('', craft))
    image, extra, others, rest = parse_media(img)
    text = one_line(event) + refs     # refs the date cell carried
    if OUTLINE:                       # every picture is a file line before the item: they share one row that wraps
        if rest:
            text += '<br />' + rest
    elif extra:                       # framed media start on their own line, like the image
        text += '<br />' + ' '.join(extra)
    if not sections or sections[-1][0] != craft:
        sections.append([craft, []])
    sections[-1][1].append((date, text, image, others if OUTLINE else []))

def plain(title):
    """Section id: the visible words of the craft name, safe for use in a class and an id."""
    t = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', title)
    return re.sub(r'[^A-Za-z0-9]+', '_', t).strip('_') or 'section'

used, blocks, counter = set(), [], 0
for craft, rows_ in sections:
    sid, k = plain(craft), 1
    while sid in used:
        k += 1; sid = '%s_%d' % (plain(craft), k)
    used.add(sid)
    out_items = []
    for n, (date, text, image, _others) in enumerate(rows_):
        counter += 1
        # No title: the section already names the craft. The item is still collapsible (dot or
        # date); closed, it shows its date. Toggle ids must be unique and plain, so give one.
        p = '{{%s/item |id=img%d |date=%s |text=%s' % (BASE, counter, date, text)
        if image:
            p += ' |image=%s |imagesize=200px' % image
        out_items.append(('|' if n == 0 else '') + p + '}}')
    blocks.append('{{%s/section |id=%s |title=%s\n%s\n}}' % (BASE, sid, craft, '\n'.join(out_items)))
timeline = '{{%s\n|%s\n}}' % (BASE, '\n'.join(blocks))
if OUTLINE:
    lines = []
    for craft, rows_ in sections:
        lines.append('!!== %s ==' % craft)
        for date, text, image, others in rows_:
            for f in ([image] if image else []) + others:
                lines.append('!![[File:%s|200px]]' % f)
            lines.append("!!* '''%s''' %s" % (date, text))
    stray = [l[:70] for l in lines if bare_pipes(l)]
    if stray:
        print('WARNING: a bare | would cut the text off in these lines:', *stray, sep='\n  ')
    timeline = invoke(MODULE, 'img', '\n'.join(lines), original='{|' + table + '\n|}', original_as='table')
items = sections

# ---------------------------------------------------------------- the rest of the page
head = head.strip()   # keeps {{short description}} and {{Use mdy dates}}: the dates in the citations depend on it
# The lead gets the first picture of the timeline: the first image on the page is what Wikipedia uses as the page image
# (the thumbnail of search results and link previews, and og:image when the page is shared), and this article had none.
if sections and sections[0][1] and sections[0][1][0][2] and not re.search(r'\[\[(File|Image):', head, re.I):
    first_date, _t, first_image, _o = sections[0][1][0]
    pic = ('[[File:%s|thumb|right|The first photograph of Earth from outer space, taken on a %s flight on %s.]]'
           % (first_image, sections[0][0], first_date))
    parts = head.split('\n\n', 1)             # the templates, then the lead
    head = parts[0] + '\n\n' + pic + '\n' + parts[1] if len(parts) == 2 else pic + '\n' + head
    head += '\n{{clear}}'                      # the picture stays in the lead: the timeline below starts at full width
if not ARTICLE_MODE:
    tail = re.sub(r'\[\[Category:', '[[:Category:', tail)
banner = '' if ARTICLE_MODE else (
    '{{User sandbox}}\n'
    "<!-- Draft showing how [[%s]] could present the table of [[%s]]. "
    'The text is copied from that article; see its history for attribution. '
    'The original table is not changed. -->\n\n' % (('Module:' + MODULE.split('/')[0]) if OUTLINE else ('Template:' + BASE), ARTICLE))
page = (banner
    + head + '\n\n== Timeline ==\nEach section on the following timeline refers to a craft or a mission.\n\n' + timeline + '\n' + tail
)
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print('%d table rows -> %d sections; wrote %s (%d bytes)' % (len(table_rows), len(sections), out, len(page)))
