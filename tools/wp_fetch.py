"""Fetch the wikitext of an English Wikipedia article for the converters.

The current revision is used unless it has already been converted (it holds {{#invoke:...}} and no table): then the
newest earlier revision that still has the original table is used.
"""
import json, subprocess, urllib.parse

UA = 'timeline-draft/1.0'
API = 'https://en.wikipedia.org/w/api.php'

def _curl(args):
    return subprocess.run(['curl', '-sL', '-A', UA] + args, capture_output=True, text=True).stdout

def fetch_article(title):
    page = urllib.parse.quote(title.replace(' ', '_'))
    wt = _curl(['https://en.wikipedia.org/w/index.php?action=raw&title=' + page])
    if '{|' in wt and '{{#invoke:' not in wt:
        return wt
    q = _curl(['-G', API, '--data-urlencode', 'action=query', '--data-urlencode', 'format=json', '--data-urlencode', 'formatversion=2',
               '--data-urlencode', 'prop=revisions', '--data-urlencode', 'rvprop=ids', '--data-urlencode', 'rvlimit=60',
               '--data-urlencode', 'titles=' + title])
    try:
        revs = json.loads(q)['query']['pages'][0]['revisions']
    except Exception:
        return wt
    for r in revs:
        old = _curl(['https://en.wikipedia.org/w/index.php?action=raw&oldid=%d' % r['revid']])
        if '{|' in old and '{{#invoke:' not in old:
            print('Note: the current article already holds a timeline; using revision %d (the newest with the original table)' % r['revid'])
            return old
    return wt
