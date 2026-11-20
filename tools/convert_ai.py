#!/usr/bin/env python3
"""Draft: "Timeline of artificial intelligence" rebuilt with the Lua module.

Usage: python3 tools/convert_ai.py [--module=NAME] [out.wikitext]

Fetches the current wikitext of the article from English Wikipedia. Every two-column table (date |
development) becomes one {{#invoke:NAME|outline|text=...}} timeline with one item per row; a date
shared by several rows (rowspan) is repeated on each item. Headings, the lead, the pictures and
everything outside the tables (See also, Notes, References, Sources, ...) stay exactly as they are.
NAME is TimelineRail/sandbox until Module:TimelineRail is live.

The text is copied from Wikipedia (CC BY-SA 4.0): say so in the edit summary.
"""
import pathlib, re, subprocess, sys, urllib.parse

ARTICLE = 'Timeline of artificial intelligence'
root = pathlib.Path(__file__).resolve().parent.parent
FLAGS = [a for a in sys.argv[1:] if a.startswith('--')]
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
MODULE = next((f.split('=', 1)[1] for f in FLAGS if f.startswith('--module=')), 'TimelineRail/sandbox')
out = pathlib.Path(ARGS[0]) if ARGS else root / 'drafts' / (ARTICLE.replace(' ', '_') + '__lua.wikitext')

url = 'https://en.wikipedia.org/w/index.php?action=raw&title=' + urllib.parse.quote(ARTICLE.replace(' ', '_'))
wt = subprocess.run(['curl', '-s', '-A', 'timeline-draft/1.0', url], capture_output=True, text=True).stdout
if '{|' not in wt:
    sys.exit('Could not fetch the article wikitext')

REF = re.compile(r'<ref(?:\s[^>]*)?/>|<ref(?:\s[^>]*)?>.*?</ref>', re.S)

def one_line(s):
    return re.sub(r'\s*\n\s*', ' ', s).strip()

def still_open(buf):
    if buf.count('{{') > buf.count('}}'):
        return True
    return len(re.findall(r'<ref(?:\s[^>]*[^/>])?>', buf)) > len(re.findall(r'</ref>', buf))

def bare_pipes(text):
    """| outside [[ ]], {{ }} and <ref>: inside {{#invoke:...|text=...}} each one would end the argument."""
    text = re.sub(r'<ref(?:\s[^>]*[^/>])?>.*?</ref>', '', text, flags=re.S)
    depth = n = 0
    for tok in re.findall(r'\[\[|\{\{|\]\]|\}\}|\|', text):
        if tok in ('[[', '{{'): depth += 1
        elif tok in (']]', '}}'): depth -= 1
        elif depth == 0: n += 1
    return n

warnings, stats = [], {'tables': 0, 'rows': 0}

def parse_table(body):
    """Rows of cells [(kind, text)] from the text between {| and |}."""
    rows, cells, buf, kind = [], None, None, None
    def close():
        if buf is not None:
            cells.append((kind, buf))
    for line in body.split('\n')[1:]:          # first line holds the table attributes
        in_cell = buf is not None and still_open(buf)
        if not in_cell and line.startswith('|-'):
            close(); buf = None
            if cells:
                rows.append(cells)
            cells = []
        elif not in_cell and line.startswith('!'):
            close(); kind, buf = '!', line[1:]
            if cells is None: cells = []
        elif not in_cell and line.startswith('|') and not line.startswith('|+'):
            close(); kind, buf = '|', line[1:]
            if cells is None: cells = []
        elif buf is not None:
            buf += '\n' + line
    close()
    if cells:
        rows.append(cells)
    return rows

def table_to_outline(table_text, n):
    rows = parse_table(table_text)
    carry, pending = [None, None], [0, 0]
    items = []
    for cells in rows:
        if [c[1].strip().lower() for c in cells] == ['date', 'development']:
            continue                           # header row
        it, full = iter(cells), []
        for c in range(2):
            if pending[c] > 0:
                full.append(carry[c]); pending[c] -= 1
                continue
            kind, raw = next(it, ('|', ''))
            span = 1
            m = re.match(r'\s*(?:(?:style|class|scope|align)\s*=\s*"?[^|"]*"?\s*)*rowspan\s*=\s*"?(\d+)"?[^|]*\|(?!\|)(.*)', raw, re.S)
            if m:
                span, raw = int(m.group(1)), m.group(2)
            elif re.match(r'\s*[a-z-]+\s*=\s*"[^"]*"\s*\|(?!\|)', raw):
                warnings.append('cell attributes dropped: ' + raw[:60])
                raw = raw.split('|', 1)[1]
            raw = raw.strip()
            full.append(raw)
            if span > 1:
                carry[c], pending[c] = raw, span - 1
        date_cell, text = full
        refs = ''.join(REF.findall(date_cell))
        date = one_line(REF.sub('', date_cell))
        text = one_line(text) + refs
        if not date or not text:
            warnings.append('empty date or text: %r / %r' % (date[:40], text[:40]))
        items.append(("* '''%s''' %s" % (date, text)))
        stats['rows'] += 1
        for l in items[-1:]:
            if bare_pipes(l):
                warnings.append('bare | would cut the text: ' + l[:80])
            if re.match(r"\* '''[^']*''' *[*=#;:]|\* '''[^']*''' *\[\[(File|Image):", l, re.I):
                warnings.append('text starts like wiki syntax: ' + l[:80])
    stats['tables'] += 1
    return '{{#invoke:%s|outline |id=ai%d\n|text=\n%s\n}}' % (MODULE, n, '\n'.join(items))

# ---------------------------------------------------------------- replace each table
page, pos, n = '', 0, 0
for m in re.finditer(r'^\{\|', wt, re.M):
    if m.start() < pos:
        continue
    end = wt.index('\n|}', m.start())
    n += 1
    page += wt[pos:m.start()] + table_to_outline(wt[m.start():end], n)
    pos = end + 3
page += wt[pos:]
page = re.sub(r'\[\[Category:', '[[:Category:', page)
page = ('{{User sandbox}}\n'
        "<!-- Draft showing how [[Module:%s]] could present the tables of [[%s]]. The text is copied from that "
        'article; see its history for attribution. The original is not changed. -->\n' % (MODULE.split('/')[0], ARTICLE)
        + page)
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print('%d tables, %d rows -> %s (%d bytes)' % (stats['tables'], stats['rows'], out, len(page)))
for w in warnings:
    print('WARNING:', w)
