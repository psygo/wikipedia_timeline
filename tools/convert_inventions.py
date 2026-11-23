#!/usr/bin/env python3
"""Draft: "Timeline of historic inventions" rebuilt with TimelineRail.

Usage: python3 tools/convert_inventions.py [--outline [--module=NAME]] [out.wikitext [level-2 heading ...]]

With --outline the timelines are written for the Lua module (one {{#invoke:NAME|outline|text=...}} per
run of sections; the whole article can be converted that way). NAME is TimelineRail/sandbox until the
module is live as Module:TimelineRail. Without it, the template family is used.

Fetches the current wikitext of the article from English Wikipedia. The headings that
only hold other headings (Paleolithic, Classical antiquity and medieval era, ...) stay headings;
each heading that holds bullets (Lower Paleolithic, Middle Paleolithic, ..., 5th century BC, ...)
becomes a TimelineRail section, and the sections under one parent form one timeline. A heading's introduction goes in the section's text=; each
bullet becomes an item (the bold date is the date, the rest is the text); a thumbnail line is
attached to the next bullet. Only the headings named on the command line (default: Paleolithic and
Agricultural and proto-agricultural eras) are converted; the rest of the article is kept exactly as it
is, because converting every section would exceed MediaWiki's 2 MB post-expand include limit (each
template level, item, section and TimelineRail, repeats the text once more). The lead, See also,
Notes, References and External links are kept.

The text is copied from Wikipedia (CC BY-SA 4.0): say so in the edit summary.
"""
import pathlib, re, subprocess, sys, urllib.parse

ARTICLE = 'Timeline of historic inventions'
root = pathlib.Path(__file__).resolve().parent.parent
FLAGS = [a for a in sys.argv[1:] if a.startswith('--')]
from outline_call import invoke
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
OUTLINE = '--outline' in FLAGS
MODULE = next((f.split('=', 1)[1] for f in FLAGS if f.startswith('--module=')), 'TimelineRail/sandbox')
out = pathlib.Path(ARGS[0]) if ARGS else root / 'drafts' / (ARTICLE.replace(' ', '_') + ('__lua' if OUTLINE else '') + '.wikitext')
BASE = 'TimelineRail'

url = 'https://en.wikipedia.org/w/index.php?action=raw&title=' + urllib.parse.quote(ARTICLE.replace(' ', '_'))
wt = subprocess.run(['curl', '-s', '--max-time', '60', '-A', 'timeline-draft/1.0', url], capture_output=True, text=True).stdout
if '==Paleolithic==' not in wt:
    sys.exit('Could not fetch the article wikitext')

lines = wt.split('\n')
H = re.compile(r'^(={2,6})\s*(.*?)\s*\1\s*$')

# ------------------------------------------------------------------ pieces of the page
first_h = next(i for i, l in enumerate(lines) if H.match(l))
end_h = next(i for i, l in enumerate(lines) if H.match(l) and H.match(l).group(2).lower() == 'see also')
lead = '\n'.join(lines[:first_h]).strip()
rest_of_page = '\n'.join(lines[end_h:]).strip()
body = lines[first_h:end_h]

def one_line(s):
    return re.sub(r'\s*\n\s*', ' ', s).strip()

def still_open(buf):
    if buf.count('{{') > buf.count('}}'):
        return True
    return len(re.findall(r'<ref(?:\s[^>]*[^/>])?>', buf)) > len(re.findall(r'</ref>', buf))

# ------------------------------------------------------------------ headings -> tree
class Sec:
    def __init__(self, level, title):
        self.level, self.title = level, title
        self.prose, self.entries, self.children = [], [], []   # entries: ('item', date, text, image) ...
        self.pending_image = None

root_secs = []       # level-2 headings
stack = []
cur_buf = None       # bullet or prose being accumulated across lines
cur_kind = None
anomalies = []

def flush():
    global cur_buf, cur_kind
    if cur_buf is None:
        return
    sec = stack[-1]
    text = cur_buf.rstrip()
    if cur_kind == 'bullet':
        sec.entries.append(['bullet', text, []])
    elif cur_kind == 'sub':
        if sec.entries and sec.entries[-1][0] == 'bullet':
            sec.entries[-1][2].append(text)
        else:
            sec.entries.append(['bullet', text, []])
    else:
        sec.prose.append(text)
    cur_buf = cur_kind = None

for line in body:
    m = H.match(line)
    if m:
        flush()
        lvl, title = len(m.group(1)), m.group(2)
        node = Sec(lvl, title)
        while stack and stack[-1].level >= lvl:
            stack.pop()
        (stack[-1].children if stack else root_secs).append(node)
        stack.append(node)
        continue
    if cur_buf is not None and still_open(cur_buf):
        cur_buf += '\n' + line
        continue
    if line.startswith('**'):
        flush(); cur_buf, cur_kind = line.lstrip('*').strip(), 'sub'
    elif line.startswith('*'):
        flush(); cur_buf, cur_kind = line.lstrip('*').strip(), 'bullet'
    elif re.match(r'\[\[(?:File|Image):', line):
        flush()
        stack[-1].entries.append(['file', line.strip()])
    elif not line.strip():
        flush()
    elif line.startswith('<!--'):
        flush()
    else:
        if cur_buf is not None and cur_kind in ('bullet', 'sub'):
            cur_buf += '\n' + line         # continuation line of a bullet
        else:
            flush(); cur_buf, cur_kind = line, 'prose'
flush()

# ------------------------------------------------------------------ bullets -> items
def split_args(s):
    """Split on | at depth 0 of [[ ]] and {{ }}."""
    parts, depth, cur = [], 0, ''
    i = 0
    while i < len(s):
        two = s[i:i + 2]
        if two in ('[[', '{{'):
            depth += 1; cur += two; i += 2
        elif two in (']]', '}}'):
            depth -= 1; cur += two; i += 2
        elif s[i] == '|' and depth == 0:
            parts.append(cur); cur = ''; i += 1
        else:
            cur += s[i]; i += 1
    parts.append(cur)
    return parts

OPT = re.compile(r'^(thumb(nail)?|frame(less)?|border|right|left|center|centre|none|upright.*|\d+x?\d*px|x\d+px|alt=.*|link=.*|class=.*|lang=.*|page=.*|baseline|middle|sub|super|text-top|text-bottom|top|bottom)$', re.I)

def parse_file(line):
    inner = line[2:-2]
    parts = split_args(inner)
    name = re.sub(r'^(?:File|Image):', '', parts[0]).strip()
    caption = ''
    for p in parts[1:]:
        if not OPT.match(p.strip()):
            caption = p.strip()
    return name, caption

def date_and_text(b):
    b = one_line(b)
    m = re.match(r"^'''(.+?)'''\s*(.*)$", b)
    if m:
        return m.group(1).strip().rstrip(':').strip(), m.group(2).strip()
    m = re.match(r"^1'''978:'''\s*(.*)$", b)          # a typo in the source
    if m:
        return '1978', m.group(1).strip()
    m = re.match(r"^([^:\[\]'<{|]{1,40}?):\s+(.*)$", b)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return '', b

def used_id(title, used):
    sid = re.sub(r'[^A-Za-z0-9]+', '_', title).strip('_') or 'section'
    base, k = sid, 1
    while sid in used:
        k += 1; sid = '%s_%d' % (base, k)
    used.add(sid)
    return sid


BANNED = re.compile(r'archive\.(?:today|is|ph|li|vn|md|fo)/', re.I)
ARCHIVE_PARAMS = re.compile(r'^\s*(archive-?url|archive-?date|url-?status|dead-?url)\s*=', re.I)

def drop_banned_archives(text):
    """English Wikipedia's edit filter refuses any edit that adds an archive.today link, even one copied
    from an existing citation. Remove the archive-url (and the parameters that depend on it) from such
    citations; the citation keeps its original url."""
    out, i, n = '', 0, 0
    for m in re.finditer(r'\{\{\s*cite', text, re.I):
        j = m.start()
        if j < i:
            continue                      # inside a block already handled
        depth, k = 0, j
        while k < len(text):
            two = text[k:k + 2]
            if two == '{{': depth += 1; k += 2
            elif two == '}}':
                depth -= 1; k += 2
                if depth == 0: break
            else: k += 1
        block = text[j:k]
        if BANNED.search(block):
            parts = split_args(block[2:-2])
            keep = [parts[0]] + [q for q in parts[1:] if not ARCHIVE_PARAMS.match(q)]
            block = '{{' + '|'.join(keep) + '}}'
            n += 1
        out += text[i:j] + block
        i = k
    out += text[i:]
    return out, n

ids = set()
stats = {'items': 0, 'images': 0, 'sections': 0, 'undated': 0, 'n': 0}

def item_wikitext(bullet, subs, file_line):
    date, text = date_and_text(bullet)
    if not date:
        stats['undated'] += 1
        anomalies.append(text[:90])
    if subs:
        text += ' <ul>' + ''.join('<li>%s</li>' % one_line(x) for x in subs) + '</ul>'
    stats['n'] += 1
    # No title (the section names the period): the item is still collapsible by its dot or date.
    # The toggle id is made from the date and title otherwise, which repeats, so give a plain one.
    p = '{{%s/item |id=i%d |date=%s |text=%s' % (BASE, stats['n'], date, text)
    if file_line:
        name, cap = parse_file(file_line)
        p += ' |image=%s |imagesize=220px' % name
        if cap:
            p += ' |caption=%s' % one_line(cap)
        stats['images'] += 1
    stats['items'] += 1
    return p + '}}'

def section_wikitext(sec):
    stats['sections'] += 1
    sid = used_id(sec.title, ids)
    # entries: attach each file line to the next bullet (or the previous one if there is none)
    items, pending = [], None
    for e in sec.entries:
        if e[0] == 'file':
            pending = e[1]
        else:
            items.append(item_wikitext(e[1], e[2], pending)); pending = None
    if pending and items:
        # a trailing thumbnail: put it on the last bullet
        last = [e for e in sec.entries if e[0] == 'bullet'][-1]
        items[-1] = item_wikitext(last[1], last[2], pending)
    parts = items
    prose = ''
    if sec.prose:
        prose = ' |text=' + '\n\n'.join(sec.prose)
    return '{{%s/section |id=%s |title=%s%s\n|%s\n}}' % (BASE, sid, sec.title, prose, '\n'.join(parts))

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

def outline_item(bullet, subs, file_line):
    date, text = date_and_text(bullet)
    if not date:
        stats['undated'] += 1
        anomalies.append(text[:90])
    stats['n'] += 1
    stats['items'] += 1
    lines = []
    if file_line:
        lines.append(file_line)
        stats['images'] += 1
    lines.append(("* '''%s''' %s" % (date, text)) if date else ('* ;; ;; ' + text))
    lines += ['** ' + one_line(x) for x in subs]
    for l in lines:
        if bare_pipes(l):
            anomalies.append('bare | in outline line: ' + l[:80])
    return '\n'.join(lines)

def outline_section(sec):
    stats['sections'] += 1
    lines = ['== %s ==' % sec.title]
    if sec.prose:
        lines.append('\n'.join(sec.prose))
    pending = None
    for e in sec.entries:
        if e[0] == 'file':
            pending = e[1]
        else:
            lines.append(outline_item(e[1], e[2], pending)); pending = None
    return '\n'.join(lines)

_pos = [0]
def raw_section(sec):
    """The heading and bullets of one leaf section exactly as the article has them (in document order)."""
    L = sec.level
    m = re.compile(r'(?m)^={%d}[ \t]*%s[ \t]*={%d}[ \t]*$' % (L, re.escape(sec.title), L)).search(raw_lines, _pos[0])
    if not m:
        anomalies.append('original text of a section not found: ' + sec.title)
        return ''
    nxt = re.compile(r'(?m)^={1,%d}[^=\n]' % L).search(raw_lines, m.end())
    _pos[0] = m.end()
    return raw_lines[m.start():nxt.start() if nxt else len(raw_lines)].strip('\n')

def emit(sec, pieces):
    """Headings that only hold other headings stay real headings; the runs of leaf headings
    under one parent become one TimelineRail whose sections are those leaves. (Nesting the
    sections inside each other multiplies the text through every template level, which blows
    MediaWiki's post-expand size limit on a list this long.)"""
    h = '=' * sec.level
    pieces.append('%s%s%s' % (h, sec.title, h))
    if sec.prose:
        pieces.append('\n\n'.join(sec.prose))
    if sec.entries:
        anomalies.append('heading with its own bullets: ' + sec.title)
    run = []
    def close():
        if run:
            if OUTLINE:
                stats['outlines'] = stats.get('outlines', 0) + 1
                pieces.append(invoke(MODULE, 'inv%d' % stats['outlines'], '\n'.join(outline_section(c) for c in run),
                                     original='\n\n'.join(raw_section(c) for c in run), original_as='list'))
            else:
                pieces.append('{{%s\n|%s\n}}' % (BASE, '\n'.join(section_wikitext(c) for c in run)))
            run.clear()
    for c in sec.children:
        if c.children:
            close()
            emit(c, pieces)
        else:
            run.append(c)
    close()

CONVERT = ARGS[1:] or ([t.title for t in root_secs] if OUTLINE else ['Paleolithic', 'Agricultural and proto-agricultural eras'])
raw_lines = '\n'.join(body)
def original_part(title):
    """The level-2 section exactly as in the article."""
    m = re.search(r'(?ms)^==\s*' + re.escape(title) + r'\s*==\s*$.*?(?=^==[^=]|\Z)', raw_lines)
    return m.group(0).strip()

pieces = []
for top in root_secs:
    if top.title in CONVERT:
        emit(top, pieces)
    else:
        pieces.append(re.sub(r'\[\[Category:', '[[:Category:', original_part(top.title)))

page = (
    '{{User sandbox}}\n'
    "<!-- Draft showing how [[Template:%s]] could present [[%s]]. The text is copied from that "
    'article; see its history for attribution. The original is not changed. -->\n' % (BASE, ARTICLE)
    + re.sub(r'\[\[Category:', '[[:Category:', lead) + '\n\n'
    + '\n\n'.join(pieces) + '\n\n'
    + re.sub(r'\[\[Category:', '[[:Category:', rest_of_page) + '\n'
)
page, dropped = drop_banned_archives(page)
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print('%d sections, %d items (%d with a picture) -> %s (%d bytes)' % (stats['sections'], stats['items'], stats['images'], out, len(page)))
print('archive.today links removed from %d citations' % dropped)
if anomalies:
    print('items without a recognised date (%d):' % len(anomalies))
    for a in anomalies:
        print('   ', a)
