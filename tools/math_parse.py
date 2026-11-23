"""Parse the English Wikipedia article "Timeline of mathematics" into events (for tools/convert_math.py)."""
import re

REFRE = re.compile(r'<ref(?:\s[^>]*)?/>|<ref(?:\s[^>]*)?>.*?</ref>', re.S)

def open_refs(buf):
    return len(re.findall(r'<ref(?:\s[^>]*[^/>])?>', buf)) > len(re.findall(r'</ref>', buf)) or buf.count('{{') > buf.count('}}')

def split_date(body):
    """'c. 1000 BC&nbsp;– text' -> ('c. 1000 BC', 'text'). The first separator that is not inside [[ ]] or {{ }}."""
    depth = 0
    i = 0
    cands = ['&nbsp;–', '&nbsp;—', '&nbsp;-', '—', ' – ', ' — ']
    best = None
    for sep in cands:
        j = 0
        while True:
            j = body.find(sep, j)
            if j < 0: break
            pre = body[:j]
            if pre.count('[[') == pre.count(']]') and pre.count('{{') == pre.count('}}'):
                if best is None or j < best[0]:
                    best = (j, sep)
                break
            j += 1
        if sep.startswith('&nbsp;') and best is not None:
            break
    if best is None:
        return None, body
    j, sep = best
    date, text = body[:j].strip(), body[j + len(sep):].strip()
    # "490 BC – 430 BC – Greece, ...": the second date belongs to the first
    m = re.match(r'^(\d[\d,]*\s*(?:BC|BCE|AD|CE)?)\s*(?:&nbsp;)?\s*[–—-]\s*(?=\D)(.*)$', text, re.S)
    if m and re.search(r'\d', date):
        date, text = date + ' – ' + m.group(1).strip(), m.group(2).strip()
    return date, text

def parse_timeline(wt):
    """-> list of dict(stage, period, date, text) in article order."""
    wt = wt.split('==See also==')[0]
    stage = period = sub = None
    events = []
    lines = wt.split('\n')
    i = 0
    while i < len(lines):
        l = lines[i]
        m = re.match(r'^(={2,4})\s*(.*?)\s*\1\s*$', l)
        if m:
            lvl, title = len(m.group(1)), m.group(2)
            if lvl == 2: stage, period, sub = title, None, None
            elif lvl == 3: period, sub = title, None
            else: sub = title
            i += 1
            continue
        if l.startswith('*') and not l.startswith('**'):
            buf = l[1:].strip()
            while open_refs(buf) and i + 1 < len(lines):
                i += 1
                buf += ' ' + lines[i].strip()
            date, text = split_date(buf)
            events.append({'stage': stage, 'period': period, 'sub': sub, 'date': date, 'text': text})
        i += 1
    return events

if __name__ == '__main__':
    import subprocess, sys, collections
    wt = subprocess.run(['curl', '-sL', '--max-time', '60', '-A', 'timeline-draft/1.0', 'https://en.wikipedia.org/w/index.php?action=raw&title=Timeline_of_mathematics'], capture_output=True, text=True).stdout
    ev = parse_timeline(wt)
    print(len(ev))
    print(collections.Counter((e['stage'], e['period'], e['sub']) for e in ev))
    print([e for e in ev if not e['date']][:5])


# ---------------------------------------------------------------- dates
def plain(s):
    s = re.sub(r'<ref(?:\s[^>]*)?/>|<ref(?:\s[^>]*)?>.*?</ref>', '', s or '', flags=re.S)
    s = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', s)
    s = re.sub(r"'''?", '', s).replace('&nbsp;', ' ').replace('&ndash;', '–').replace('&mdash;', '—')
    s = re.sub(r'\{\{[Cc]irca\|([^}|]*)(?:\|([^}]*))?\}\}', lambda m: 'c. ' + m.group(1) + ('–' + m.group(2) if m.group(2) else ''), s)
    return re.sub(r'\s+', ' ', s).strip()

def year_of(date):
    """Rough year of a date label (negative = BC); None when there is no number."""
    d = plain(date)
    dl = d.lower()
    m = re.search(r'(\d+)(?:st|nd|rd|th)\s+(millennium|century)\s*(BC|BCE|AD|CE)?', d)
    if m:
        n, kind, era = int(m.group(1)), m.group(2), m.group(3)
        bc = era in ('BC', 'BCE') or (era is None and re.search(r'\bBCE?\b', d))
        span = 1000 if kind == 'millennium' else 100
        mid = n * span - span / 2
        y = -mid if bc else (n - 1) * span + span / 2
        if dl.startswith(('early', 'first half')): y -= span / 4          # earlier = smaller, BC or AD
        if dl.startswith(('late', 'second half')): y += span / 4
        return y
    nums = [(int(x.replace(',', '')), e) for x, e in re.findall(r'(\d[\d,]*)\s*(BC|BCE|AD|CE)?', d) if x.replace(',', '').isdigit()]
    if not nums:
        return -50 if re.search(r'\bBCE?\b', d) else None
    n, e = nums[0]
    bc = e in ('BC', 'BCE') or (e is None and any(x[1] in ('BC', 'BCE') for x in nums) and not any(x[1] in ('AD', 'CE') for x in nums))
    return -n if bc else n
