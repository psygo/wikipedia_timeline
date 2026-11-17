#!/usr/bin/env python3
"""Rewrite the prototype's hand-written timeline markup into what the item template
now emits: every item with content gets a toggler row and a collapsible body.
Idempotent (items already converted are left alone). Usage: make_collapsible_html.py file.html ..."""
import re, sys

LI = re.compile(r'<li class="wt-timeline__item">')
DATE = re.compile(r'\s*<span class="wt-timeline__date">(.*?)</span>', re.S)
n = [0]


def end_of(s, i):
    """index just after the </li> matching the <li> opened at s[i:]"""
    depth = 0
    for m in re.finditer(r'<li\b|</li>', s[i:]):
        depth += 1 if m.group(0).startswith('<li') else -1
        if depth == 0:
            return i + m.end()
    raise ValueError('unbalanced li')

def convert(s):
    out, pos = [], 0
    while True:
        m = LI.search(s, pos)
        if not m:
            out.append(s[pos:]); break
        out.append(s[pos:m.start()])
        e = end_of(s, m.start())
        inner = s[m.end():e - len('</li>')]
        d = DATE.match(inner)
        rest = inner[d.end():] if d else inner
        has_content = bool(re.search(r'wt-timeline__(title|text|image)', rest)) and d
        if not has_content:
            out.append(s[m.start():m.end()] + convert(inner) + '</li>')
        else:
            n[0] += 1
            ident = 'wt%d' % n[0]
            head = re.split(r'<ol class="wt-timeline wt-timeline--sub"', rest)[0]
            titles = re.findall(r'<span class="wt-timeline__title">(.*?)</span>', head, re.S)
            peek = ', '.join(t.strip() for t in titles if t.strip())
            out.append(
                '<li class="wt-timeline__item wt-timeline__item--collapsible">'
                '\n\t\t<div class="wt-timeline__row mw-customtoggle-%s"><span class="wt-timeline__date">%s</span><span class="wt-timeline__peek">%s</span></div>'
                '\n\t\t<div class="wt-timeline__body mw-collapsible" id="mw-customcollapsible-%s">%s</div>\n\t</li>'
                % (ident, d.group(1), peek, ident, convert(rest)))
        pos = e
    return ''.join(out)

def retitle(s):
    """One-event collapsible items keep their title in the row (so it is the toggler)."""
    starts = [m.start() for m in re.finditer(r'<li class="wt-timeline__item wt-timeline__item--collapsible">', s)]
    for st in reversed(starts):
        e = end_of(s, st)
        li = s[st:e]
        head = re.split(r'<ol class="wt-timeline wt-timeline--sub"', li)[0]
        if 'wt-timeline__peek--title' in head or head.count('class="wt-timeline__event"') != 1:
            continue
        m = re.search(r'\s*<span class="wt-timeline__title">(.*?)</span>', head, re.S)
        if not m:
            continue
        title = m.group(1)
        new = head.replace(m.group(0), '', 1)
        new = re.sub(r'<span class="wt-timeline__peek">.*?</span>', '<span class="wt-timeline__peek wt-timeline__peek--title">%s</span>' % title, new, count=1, flags=re.S)
        s = s[:st] + new + li[len(head):] + s[e:]
    return s

for f in sys.argv[1:]:
    s = open(f).read()
    n[0] = max([int(x) for x in re.findall(r'mw-customtoggle-wt(\d+)', s)] or [0])
    open(f, 'w').write(retitle(convert(s)))
    print(f, n[0], 'items converted so far')
