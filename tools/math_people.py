"""Life dates of people, and dates of periods, from the first sentences of their Wikipedia articles."""
import re

PROFESSIONS = (r'mathematician|astronomer|astrologer|philosopher|physicist|scientist|polymath|logician|geometer|scholar|engineer|'
               r'statistician|economist|cryptographer|cryptologist|computer scientist|monk|priest|scribe|grammarian|algebraist|'
               r'theologian|chemist|inventor|professor|historian|teacher|writer|banker|merchant|physician|lawyer|politician|cleric|'
               r'poet|encyclopedist|architect|surveyor|numismatist|mathematicians?|computer pioneer|programmer|cartographer|'
               r'geodesist|naturalist|educator|author|jurist|surgeon|navigator|clergyman|abbot|bishop|pope|emperor|king')
PERIOD_WORDS = r'period|age\b|dynasty|empire|era\b|civilization|civilisation|kingdom|culture|school|Golden Age|Republic'
YEAR = re.compile(r'(?<![\d.,])(\d{1,4})(?![\d,]\d)(?:\s*(BCE|BC|CE|AD))?')

def parens(s):
    """The top-level (...) groups that start within the first 220 characters: [(content, start)]"""
    out, depth, start = [], 0, None
    for j, ch in enumerate(s[:700]):
        if ch == '(':
            if depth == 0:
                start = j
            depth += 1
        elif ch == ')' and depth:
            depth -= 1
            if depth == 0 and start is not None and start <= 220:
                out.append((s[start + 1:j], start))
    return out

def first_paren(s):
    """The first top-level (...) that holds years."""
    for par, i in parens(s):
        if years(par) or 'fl.' in par:
            return par, i
    return None

def years(par):
    out = []
    par = re.sub(r'\[[^\]]*\]', '', par)                       # "[O.S. 20 March 1726]"
    par = re.sub(r'(\d{3,4})\s*/\s*\d{1,4}', r'\1', par)      # "626/623": the first reading
    for m in YEAR.finditer(par):
        n = int(m.group(1))
        after = par[m.end():]
        before = par[max(0, m.start() - 12):m.start()]
        if re.match(r'\s*(January|February|March|April|May|June|July|August|September|October|November|December)', after):
            continue                                   # a day: "10 June 940"
        if re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s*$', before) \
                and after.lstrip().startswith(',') and not m.group(2):
            continue                                   # a day: "June 10, 940"
        era = m.group(2) or ('AD' if re.search(r'\b(?:AD|CE)\s*$', before) else None)
        if n < 32 and not era:
            continue
        out.append((n, era, bool(re.search(r'(?:\bc\.|\bca\.|\bcirca)\s*(?:AD\s*)?$', before))))
    return out

def fmt(ys, par, bc_hint):
    """'1412–1486', 'c. 570–c. 495 BC', '46 BC–23 AD', 'born 1934', 'fl. 300 BC'; None when unsure."""
    def era(e):
        return {'BCE': 'BC', 'CE': 'AD'}.get(e, e)
    if not ys:
        return None
    toks = [(n, era(e), c) for n, e, c in ys]
    # a number without an era takes the era of the next one that has one
    for i in range(len(toks) - 1, -1, -1):
        n, e, c = toks[i]
        if e is None:
            nxt = next((toks[j][1] for j in range(i + 1, len(toks)) if toks[j][1]), None)
            toks[i] = (n, nxt or ('BC' if bc_hint else 'AD'), c)
    if 'fl.' in par or 'flourished' in par:
        n, e, _ = toks[0]
        return 'fl. %d%s' % (n, ' BC' if e == 'BC' else '')
    if len(toks) == 1:
        n, e, c = toks[0]
        if re.search(r'\bborn\b|\bb\.', par) and e == 'AD':
            return 'born %d' % n
        return None
    a, b = toks[0], toks[-1]
    if a[1] == b[1]:
        if a[1] == 'BC' and a[0] < b[0]:
            return None
        if a[1] == 'AD' and a[0] > b[0]:
            return None
        return '%s%d–%s%d%s' % ('c. ' if a[2] else '', a[0], 'c. ' if b[2] else '', b[0], ' BC' if a[1] == 'BC' else '')
    if a[1] == 'BC' and b[1] == 'AD':
        return '%s%d BC–%s%d AD' % ('c. ' if a[2] else '', a[0], 'c. ' if b[2] else '', b[0])
    return None

def dates_of(extract):
    """(kind, text) kind 'person' or 'period' or None."""
    if not extract:
        return None, None
    fp = first_paren(extract)
    if not fp:
        return None, None
    par, i = fp
    par = re.sub(r'\[[^\]]*\]', '', par)
    par = re.sub(r'(\d{3,4})\s*/\s*\d{1,4}', r'\1', par)
    head = extract[:i]
    rest = extract[i + len(par) + 2:i + len(par) + 260]
    ys = years(par)
    if not ys:
        return None, None
    bc_hint = bool(re.search(r'\bBCE?\b', par)) and not re.search(r'\bAD\b|\bCE\b(?!\w)', par.replace('BCE', ''))
    person = (re.search(r'\b(?:was|is|were)\s+(?:an?|the)\b[^.]{0,140}?\b(?:%s)\b' % PROFESSIONS, extract, re.I)
              and len(head) < 140 and not re.search(r'\b(?:is|was|are|were)\b', head))
    if person:
        t = fmt(ys, par, bc_hint)
        return ('person', t) if t else (None, None)
    if re.search(PERIOD_WORDS, extract[:160]) and len(ys) >= 2 and len(head) < 90:
        t = fmt(ys, par, bc_hint)
        return ('period', t) if t else (None, None)
    return None, None

if __name__ == '__main__':
    import json
    info = json.load(open('tools/.cache/math_info.json'))
    n = 0
    for k, v in sorted(info.items()):
        if not v: continue
        kind, t = dates_of(v['extract'])
        if kind:
            n += 1
            print('%-8s %-40s %s' % (kind, k, t))
    print(n)
