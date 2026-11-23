"""Wikipedia facts for tools/convert_math.py: for each linked title, the first sentence of the lead (to find people and their
dates) and the free page image. Cached in tools/.cache/math_info.json."""
import json, pathlib, subprocess, time

CACHE = pathlib.Path(__file__).resolve().parent / '.cache' / 'math_info.json'

def _api(params):
    args = ['curl', '-s', '--max-time', '60', '-A', 'timeline-draft/1.0', 'https://en.wikipedia.org/w/api.php']
    for k, v in params.items():
        args += ['--data-urlencode', '%s=%s' % (k, v)]
    for _ in range(5):
        r = subprocess.run(args, capture_output=True, text=True).stdout
        try:
            return json.loads(r)
        except Exception:
            time.sleep(4)
    return None

def fetch_info(titles):
    info = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [t for t in titles if t not in info]
    for i in range(0, len(todo), 20):
        chunk = todo[i:i + 20]
        d = _api({'action': 'query', 'format': 'json', 'formatversion': 2, 'redirects': 1, 'prop': 'extracts|pageprops',
                  'exintro': 1, 'explaintext': 1, 'exsentences': 2, 'exlimit': 20, 'ppprop': 'page_image_free|disambiguation',
                  'titles': '|'.join(chunk)})
        if not d or 'query' not in d:
            continue
        q = d['query']
        redir = {x['from']: x['to'] for x in q.get('redirects', [])}
        norm = {x['from']: x['to'] for x in q.get('normalized', [])}
        pages = {p['title']: p for p in q['pages']}
        for t in chunk:
            p = pages.get(redir.get(norm.get(t, t), norm.get(t, t)))
            if not p or p.get('missing'):
                info[t] = None
                continue
            pp = p.get('pageprops') or {}
            info[t] = {'title': p['title'], 'extract': (p.get('extract') or '')[:400], 'image': pp.get('page_image_free'),
                       'disambig': 'disambiguation' in pp}
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(info, ensure_ascii=False))
    return info
