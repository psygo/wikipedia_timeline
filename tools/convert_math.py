#!/usr/bin/env python3
"""Draft: "Timeline of mathematics" rebuilt with the live modules (TimelineRail, OutlineList, OutlineTable, ViewSwitcher).

Usage: python3 tools/convert_math.py [out.wikitext]

Sources (CC BY-SA 4.0): the English Wikipedia articles Timeline of mathematics (every event, with its footnotes) and
History of mathematics (events and footnotes the timeline lacks, and its sections by civilization). Say so in the edit summary.

What is added to the events of the timeline, as for the Timeline of Go:
  * the people and things the text names are linked in every event (names that are linked somewhere in the article);
  * the first time a person (or a period) appears on a timeline, the dates follow in parentheses: "Euclid (fl. 300 BC)";
    they come from the first sentence of the person's own article;
  * pictures (only free ones: the page image of the article of a person or a thing named in the event), with a caption
    that links; at most two per event, each file once on the main timeline;
  * page sections for the civilizations of History of mathematics (Mesopotamia, Egypt, Greece and Rome, China and East Asia,
    India, the Islamic world, Mesoamerica, medieval and Renaissance Europe), each a timeline of its own.
"""
import pathlib, re, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from outline_call import invoke
from math_parse import parse_timeline, plain, year_of, REFRE
from math_data import fetch_info
from math_people import dates_of

root = pathlib.Path(__file__).resolve().parent.parent
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
FLAGS = [a for a in sys.argv[1:] if a.startswith('--')]
MODULE = next((f.split('=', 1)[1] for f in FLAGS if f.startswith('--module=')), 'TimelineRail')
out = pathlib.Path(ARGS[0]) if ARGS else root / 'drafts' / 'Timeline_of_mathematics__lua.wikitext'

def fetch(title):
    return subprocess.run(['curl', '-sL', '--max-time', '60', '-A', 'timeline-draft/1.0',
                           'https://en.wikipedia.org/w/index.php?action=raw&title=' + title.replace(' ', '_')],
                          capture_output=True, text=True).stdout

tom = fetch('Timeline_of_mathematics')
hom = fetch('History_of_mathematics')
if 'Rhetorical stage' not in tom or 'Babylonian' not in hom:
    sys.exit('Could not fetch the articles')

# ---------------------------------------------------------------- events of the timeline
FIX = {   # the few bullets without the usual "date – text" shape: (start of the text) -> (date, text)
    'The earliest recorded use of [[combinatorial]]': ('16th century BCE', None),
    '240 BC–190 BC– Greece,': ('240 BC–190 BC', 'Greece, [[Diocles (mathematician)]]'),
    'mid-1st century [[Cleomedes]]': ('mid-1st century', '[[Cleomedes]] (as late as 400 AD)'),
    '625 China:': ('625', 'China: [[Wang Xiaotong]] writes the \'\'[[Jigu Suanjing]]\'\', where cubic and quartic equations are solved.'),
    '1356- [[Narayana': ('1356', '[[Narayana Pandita (mathematician)|Narayana Pandita]] completes his treatise [[Ganita Kaumudi]], generalized Fibonacci sequence, and the first ever algorithm to systematically generate all permutations as well as many new magic figure techniques.'),
}
events = parse_timeline(tom)
for e in events:
    if e['date']:
        continue
    for start, (d, t) in FIX.items():
        if e['text'].startswith(start):
            e['date'] = d
            if t is not None:
                tail = ''.join(REFRE.findall(e['text']))
                e['text'] = t + tail
            break
    else:
        print('WARNING: no date for', e['text'][:60])

PERIODS = ['Before 1000 BC', '1st millennium BC', '1st millennium AD', '1000–1500', '16th century', '17th century', '18th century',
           '19th century', '20th century', '21st century']
STAGE_OF = {'Before 1000 BC': 'Rhetorical stage', '1st millennium BC': 'Syncopated stage', '1st millennium AD': 'Syncopated stage'}
def period_of(e):
    if e['sub'] == '15th century':
        return '1000–1500'
    return e['sub'] or e['period']
for e in events:
    e['p'] = period_of(e)
    e['src'] = 'TOM'
    e['year'] = year_of(e['date'])

# ---------------------------------------------------------------- events from History of mathematics
HOMTXT = hom.split('\n==See also==')[0]
FULL = {}
for m in REFRE.finditer(HOMTXT):
    nm = re.match(r'<ref\s+name\s*=\s*"?([^">/\s]+)"?\s*>', m.group(0))
    if nm:
        FULL[nm.group(1)] = m.group(0)
SFN = r'\{\{(?:sfnp?|Harv|harvnb)\|[^{}]*\}\}'
ITEM = re.compile(r'<ref(?:\s[^>]*)?/>|<ref(?:\s[^>]*)?>.*?</ref>|' + SFN, re.S)

def plain_map(text):
    """The text without wiki markup for links and quotes, and for each character of it its place in the original."""
    outc, idx, i = [], [], 0
    while i < len(text):
        if text.startswith('[[', i):
            j = text.find(']]', i)
            if j > 0:
                inner = text[i + 2:j]
                start = i + 2 + (inner.find('|') + 1 if '|' in inner else 0)
                for k in range(start, j):
                    outc.append(text[k]); idx.append(k)
                i = j + 2
                continue
        if text.startswith("''", i):
            while text.startswith("'", i):
                i += 1
            continue
        outc.append(text[i]); idx.append(i); i += 1
    return ''.join(outc), idx

HOMPLAIN, HOMIDX = plain_map(HOMTXT)

def hom_refs(phrase):
    """The footnotes that follow `phrase` in History of mathematics (its sentence, else the next one): at most two."""
    pi = HOMPLAIN.find(phrase)
    if pi < 0:
        print('NO PHRASE:', phrase)
        return ''
    i = HOMIDX[pi]
    seg = HOMTXT[i:i + 1600]
    masked = REFRE.sub(lambda m: '\x01' * len(m.group(0)), seg)
    for _ in range(4):
        masked = re.sub(r'\{\{[^{}]*\}\}', lambda m: '\x01' * len(m.group(0)), masked)
    masked = re.sub(r'\[\[[^\]]*\]\]', lambda m: '\x01' * len(m.group(0)), masked)
    ends = [m.end() for m in re.finditer(r'[.!?]["”]?(?=\s|\x01|$)', masked)][:1]      # the footnotes of this sentence only
    found = []
    for end in ends or [len(seg)]:
        while True:
            t = ITEM.match(seg, end)
            if not t:
                break
            end = t.end()
        found = [r.group(0) for r in ITEM.finditer(seg[:end])]
        if found:
            break
    if not found:
        print('NO REF:', phrase)
    out_ = []
    for r in found[:2]:
        nm = re.match(r'<ref\s+name\s*=\s*"?([^">/\s]+)"?\s*(/?)>', r)
        if nm:                                  # History of mathematics' names get a prefix, so they cannot clash with the timeline's
            name = nm.group(1)
            full = FULL.get(name, r)
            full = re.sub(r'<ref\s+name\s*=\s*"?[^">/\s]+"?\s*/?>', '<ref name="hom-%s">' % name.strip(':'), full, count=1) if nm.group(2) == '' or name in FULL else full
            out_.append(full if not full.endswith('/>') else '<ref name="hom-%s" />' % name.strip(':'))
        else:
            out_.append(r)
    return ''.join(out_)

# (date, year, text, phrase of History of mathematics whose footnote is used, regions, a word that says the timeline already has it)
HOM = [
 ('c. 40,000 years ago', -38000, "[[Neanderthal]]s at Abri du Maras, in southern France, use [[yarn]], which suggests that they knew basic mathematical concepts.", 'The use of yarn by Neanderthals', '', 'Abri du Maras'),
 ('5th millennium BC', -4500, "[[Predynastic Egypt|Predynastic Egyptians]] represent geometric designs in pictures.", 'Predynastic Egyptians of the 5th millennium BC', 'E', 'Predynastic'),
 ('3rd millennium BC', -2500, "Megalithic monuments in England and Scotland are claimed to incorporate geometric ideas such as circles, ellipses and [[Pythagorean triple]]s; the claims are disputed.", 'It has been claimed that megalithic monuments', '', 'megalithic'),
 ('From c. 3000 BC', -3000, "The [[Sumer]]ians develop a complex system of [[metrology]], chiefly for administrative and financial counting: grain allotments, workers, weights of silver.", 'They developed a complex system of metrology', 'M', 'metrology'),
 ('c. 1890 BC', -1890, "The [[Moscow Mathematical Papyrus]], from the Middle Kingdom, collects word problems (story problems) that were apparently meant as entertainment.", 'Another significant Egyptian mathematical text', 'E', 'Moscow'),
 ('c. 387 BC', -387, "[[Plato]] founds the [[Platonic Academy|Academy]] in Athens, which becomes the mathematical center of the world in the 4th century BC.", 'Plato (428/427 BC', 'G', 'Platonic Academy'),
 ('c. 330 BC', -330, "The Mohist canon, compiled by the followers of [[Mozi]], contains the oldest extant work on geometry in China.", 'The oldest extant work on geometry in China', 'C', 'Mohist'),
 ('3rd century BC', -250, "The [[Mouseion|Musaeum of Alexandria]] is the premier center of mathematical education and research; the century is regarded as the \"Golden Age\" of Greek mathematics.", 'In the 3rd century BC, the premier center', 'G', 'Musaeum'),
 ('212 BC', -212, "The Emperor [[Qin Shi Huang]] orders all books in the [[Qin dynasty|Qin Empire]] other than officially sanctioned ones to be burned.", 'In 212 BC, the Emperor Qin Shi Huang', 'C', 'Qin Shi Huang'),
 ('c. 190', 190, "The earliest written mention of the [[suanpan]], the Chinese abacus, appears in Xu Yue's ''Supplementary Notes on the Art of Figures''.", 'The date of the invention of the', 'C', 'suan pan'),
 ('250–350', 300, "The \"Silver Age\" of Greek mathematics: [[Diophantus]] makes significant advances in algebra, with his ''[[Arithmetica]]''.", 'Following a period of stagnation after Ptolemy', 'G', 'Silver Age'),
 ('4th–5th century', 400, "The [[Siddhanta]]s, astronomical treatises of the [[Gupta Empire|Gupta]] period that show strong Hellenistic influence, are the next significant mathematical documents of India after the Sulba Sutras.", 'The next significant mathematical documents from India', 'I', 'Siddhanta'),
 ('529', 529, "The emperor [[Justinian I|Justinian]] closes the neo-Platonic Academy of Athens, traditionally taken as the end of the era of Greek mathematics, although the Greek tradition continues in the [[Byzantine Empire]].", 'The closure of the neo-Platonic Academy of Athens', 'G', 'Justinian'),
 ('1st millennium AD', 500, "The [[Maya civilization]] of Mexico and Central America develops a unique tradition of mathematics, independent of the rest of the world.", 'In the Pre-Columbian Americas', 'A', 'Maya'),
 ('c. 1000', 1000, "[[Al-Karaji]] writes a book containing something close to a proof by [[mathematical induction]], which he uses to prove the [[binomial theorem]], [[Pascal's triangle]] and the sum of integral cubes.", 'Something close to a proof by mathematical induction', 'S', 'Karaji'),
 ('15th century', 1450, "[[Piero della Francesca]] writes books on solid geometry and linear perspective, among them ''De Prospectiva Pingendi''.", 'Piero della Francesca', 'U', 'Piero'),
 ('1543', 1543, "[[Nicolaus Copernicus]] publishes ''[[De revolutionibus orbium coelestium]]'', a heliocentric model whose main content is mathematical rather than physical.", 'Nicolaus Copernicus’s', 'U', 'Copernicus'),
 ('1585', 1585, "[[Simon Stevin]]'s ''De Thiende'' (\"the art of tenths\"), first published in Dutch, contains the first systematic treatment of [[decimal]] notation in Europe.", 'Simon Stevin', 'U', 'Stevin'),
 ('1595', 1595, "[[Bartholomaeus Pitiscus]] publishes his ''Trigonometria'', the first use of the word [[trigonometry]].", 'Bartholomaeus Pitiscus', 'U', 'Pitiscus'),
 ('1865–1884', 1870, "National mathematical societies are founded: the [[London Mathematical Society]] (1865), the [[Société mathématique de France]] (1872) and the [[Circolo Matematico di Palermo]] (1884), among others.", 'The 19th century saw the founding', '', 'London Mathematical Society'),
 ('1929–1930', 1930, "[[Mojżesz Presburger]] proves that the truth or falsity of all statements about the natural numbers with either addition or multiplication (but not both) is decidable.", 'In 1929 and 1930, it was proved by', '', 'Presburger'),
 ('2013', 2013, "[[Harald Helfgott]] publishes a proof of the weak [[Goldbach's conjecture]].", 'A proof of Goldbach', '', 'Helfgott'),
 ('2023', 2023, "The first [[einstein problem|einstein]], a single tile that tiles the plane only aperiodically, is discovered.", 'The first einstein was discovered', '', 'einstein'),
]
tomplain = plain(tom).lower()
for d, y, text, phrase, regs, key in HOM:
    if key.lower() in tomplain:
        print('already in the timeline, skipped:', key)
        continue
    per = ('Before 1000 BC' if y < -1000 else '1st millennium BC' if y < 0 else '1st millennium AD' if y < 1000 else '1000–1500' if y < 1500
           else '16th century' if y < 1600 else '17th century' if y < 1700 else '18th century' if y < 1800 else '19th century' if y < 1900
           else '20th century' if y < 2000 else '21st century')
    events.append({'stage': STAGE_OF.get(per, 'Symbolic stage'), 'period': per, 'sub': None, 'date': d, 'text': text + hom_refs(phrase),
                   'p': per, 'src': 'HOM', 'year': y, 'tags': regs})

# order inside each period: the timeline's own order, a History of mathematics event before the first later one
ordered = []
for per in PERIODS:
    mine = [e for e in events if e['p'] == per and e['src'] == 'TOM']
    for e in [e for e in events if e['p'] == per and e['src'] == 'HOM']:
        pos = next((j for j, o in enumerate(mine) if o['year'] is not None and o['year'] > e['year']), len(mine))
        mine.insert(pos, e)
    ordered += mine
events = ordered
print(len(events), 'events (%d from History of mathematics)' % sum(1 for e in events if e['src'] == 'HOM'))

# ---------------------------------------------------------------- regions (the civilizations of History of mathematics)
REGION_WORDS = {
    'M': r'Babylon|Sumer|Mesopotamia|Akkad|Assyria|Elam|Plimpton|Susa\b|Old Babylonian|Nippur|Seleucid|Chaldean|cuneiform|YBC',
    'E': r'Egypt|Rhind|Moscow Papyrus|Ahmes|Berlin Papyrus|Kahun|Heqanakht',
    'G': r'Greece|Greek|Hellenistic|Pythagor|Thales|Euclid|Archimedes|Apollonius|Eudoxus|Eratosthenes|Hipparchus|Ptolemy|Diophantus|Hypatia|Pappus|Plato|Aristotle|Hippocrates|Zeno|Democritus|Anaxagoras|Menaechmus|Nicomachus|Theon|Heron|Hero of|Menelaus|Proclus|Rome|Roman|Boethius|Alexandria|Antikythera|Anthemius|Eutocius|Archytas|Theodorus|Theaetetus|Autolycus|Aristarchus|Philolaus|Anaximander|Cleomedes|Diocles|Nicomedes|Serenus|Geminus|Posidonius|Hypsicles|Thymaridas|Ctesibius|Vitruvius|Byzantine|Eudemus|Bryson|Antiphon|Oenopides|Dinostratus|Aristaeus|Conon|Dositheus|Sporus|Isidore',
    'C': r'China|Chinese|Han dynasty|Liu Hui|Zu Chongzhi|Jiuzhang|Sunzi|Qin Jiushao|Zhu Shijie|Yang Hui|Li Ye|Zhoubi|Guo Shoujing|Shen Kuo|Wang Xiaotong|Li Chunfeng|Mohist|Cai Yong|Liu Xin|Japan|Seki Takakazu|Wasan|Korea|Luoshu|Yi Xing|Song dynasty|Qin Empire|suanpan|abacus|rod numerals|Xu Yue|Zhang Qiujian|Zhang Heng|Chen Jiangong|Ceyuan',
    'I': r'India|Indian|Vedic|Shulba|Sulba|Aryabhata|Brahmagupta|Bhaskara|Bh[aā]skara|Mahavira|Madhava|Nilakantha|Kerala|Jain|Pingala|Baudhayana|Sridhara|Varahamihira|Bakhshali|Panini|P[aā]nini|Yajnavalkya|Narayana|Ramanujan|Katyayana|Apastamba|Halayudha|Virahanka|Hemachandra|Jyesthadeva|Ganita|Sanskrit|Lilavati|Siddhanta|Surya|Kaprekar|Lagadha|Vedanga|Yajurveda|Hindu|Indus|Aryabhatiya|Brahmasphuta|Gopala|Pāṇini|Śrīdhara|Sangamagrama|Bhaskaracharya',
    'S': r'al-|Islamic|Arab|Persian|Baghdad|Omar Khayyam|Khwarizmi|Tusi|Kashi|Banu Musa|House of Wisdom|\bIbn |\bAbu |Thabit|Alhazen|Biruni|Samaw|Karaji|Sharaf|Avicenna|Maragha|Ulugh|Samarkand|Uqlidisi|Qalasadi|Banna|Khujandi|Hasib|Ibn',
    'A': r'Maya|Olmec|Aztec|Inca|quipu|Mesoamerica',
    'U': r'Fibonacci|Liber Abaci|Leonardo of Pisa|Regiomontanus|Pacioli|Cardano|Tartaglia|Ferrari|Bombelli|Stevin|Copernicus|Pitiscus|Treviso|Oresme|Bradwardine|Jordanus|Adelard|Robert of Chester|Gerard of Cremona|Sacrobosco|Piero della|Ries|Recorde|Napier|Viète|Viete|Kepler|Boethius|Gerbert|Medieval|Renaissance|Europe|Latin',
}
REGION_TITLE = {'M': 'Mathematics in Mesopotamia', 'E': 'Mathematics in ancient Egypt', 'G': 'Mathematics in ancient Greece and Rome',
                'C': 'Mathematics in China and East Asia', 'I': 'Mathematics in India', 'S': 'Mathematics in the Islamic world',
                'A': 'Mathematics in Mesoamerica', 'U': 'Mathematics in medieval and Renaissance Europe'}
for e in events:
    t = plain(e['date']) + ' ' + plain(e['text'])
    tags = set(e.get('tags', ''))
    for k, rx in REGION_WORDS.items():
        if re.search(rx, t):
            tags.add(k)
    y = e['year'] if e['year'] is not None else 0
    if 'U' in tags and not (1000 <= y <= 1650):
        tags.discard('U')            # Europe only for the medieval and Renaissance part
    if 'G' in tags and y > 700:
        tags.discard('G')
    e['tags'] = ''.join(sorted(tags))
for k in REGION_TITLE:
    print(k, sum(1 for e in events if k in e['tags']), 'events')

# ---------------------------------------------------------------- links, people, pictures
LINK = re.compile(r'\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]')
targets = set()
for e in events:
    for m in LINK.finditer(REFRE.sub('', e['text'])):
        targets.add(m.group(1).strip())
    for m in LINK.finditer(e['date'] or ''):
        targets.add(m.group(1).strip())
info = fetch_info(sorted(targets))
resolved = {t: (info.get(t) or {}) for t in targets}

# the words that are linked somewhere in the article: link them everywhere they appear unlinked (once per event)
vocab = {}
for e in events:
    for m in LINK.finditer(REFRE.sub('', e['text'])):
        target, disp = m.group(1).strip(), (m.group(2) or m.group(1)).strip()
        if re.match(r'[A-Z]', disp) and len(disp) >= 6 and not re.search(r'[0-9]', disp) and info.get(target) and not info[target].get('disambig'):
            vocab.setdefault(disp, set()).add(target)
vocab = {d: next(iter(t)) for d, t in vocab.items() if len(t) == 1}
STOP = {'Greece', 'Greek', 'Egypt', 'Egyptian', 'Egyptians', 'India', 'Indian', 'China', 'Chinese', 'Europe', 'Persian', 'Arabic'}
# (countries and nationalities are not linked over and over)
VOCAB = sorted(((d, t) for d, t in vocab.items() if d not in STOP), key=lambda x: -len(x[0]))

def link_text(text):
    """Link every known name in the event text once (outside links, templates and footnotes)."""
    toks = []
    def put(s):
        toks.append(s)
        return '\x02%d\x03' % (len(toks) - 1)
    text = REFRE.sub(lambda m: put(m.group(0)), text)
    text = re.sub(r'\[\[[^\]]*\]\]|\{\{[^{}]*\}\}|\{\{[^{}]*\{\{[^{}]*\}\}[^{}]*\}\}|<[^>]+>', lambda m: put(m.group(0)), text)
    done = set()
    for disp, target in VOCAB:
        if target in done:
            continue
        m = re.search(r'(?<![\w\x02\x03])' + re.escape(disp) + r'(?![\w\x02\x03])', text)
        if not m:
            continue
        done.add(target)
        text = text[:m.start()] + put('[[%s]]' % disp if disp == target else '[[%s|%s]]' % (target, disp)) + text[m.end():]
    return re.sub('\x02(\\d+)\x03', lambda m: toks[int(m.group(1))], text)

def life(target):
    """('person'|'period', '1707–1783') for a target, or None."""
    v = info.get(target)
    if not v:
        return None
    kind, t = dates_of(v['extract'])
    return (kind, t) if kind else None

def add_dates(text, seen, date):
    """After the first mention of a person or period on a timeline: its dates in parentheses."""
    out_, pos = [], 0
    for m in LINK.finditer(text):
        if '[[' in text[max(0, m.start() - 0):m.start()]:
            pass
        out_.append(text[pos:m.end()])
        pos = m.end()
        target, disp = m.group(1).strip(), (m.group(2) or m.group(1)).strip()
        lf = life(target)
        if not lf:
            continue
        key = info[target]['title']
        if key in seen:
            continue
        seen.add(key)
        title = re.sub(r'\s*\(.*\)$', '', key)
        # only when the words shown are the name itself (not "Euclid's Elements", not "the Babylonian")
        if not (disp in title or title in disp or disp.split()[-1] in title.split()):
            continue
        nums = re.findall(r'\d+', lf[1])
        if text[m.end():m.end() + 2] in (' (', '(') or (nums and all(n in re.findall(r'\d+', plain(date)) for n in nums)):
            continue                                # the event's own date already says it
        if text[max(0, m.start() - 3):m.start()] == "''":
            continue
        out_.append(' (%s)' % lf[1])
    out_.append(text[pos:])
    return ''.join(out_)

def first_dates_seen(text):
    return text

IMG_BAD = re.compile(r'icon|logo|flag|symbol|commons-|oojs|question|edit-|\.svg$', re.I)
THING = re.compile(r'papyrus|tablet|manuscript|treatise|\bbook\b|\btext\b|bone|abacus|instrument|machine|computer|monument|temple|'
                   r'observatory|calculator|clock|\bmap\b|stone|clay|scroll|codex|astrolabe|compass|engine', re.I)
used_images = set()

def pictures(text, date):
    """[(file, caption)]: persons first, then things; at most two; each file once on the main timeline."""
    cands = []
    for m in LINK.finditer(REFRE.sub('', text)):
        target, disp = m.group(1).strip(), (m.group(2) or m.group(1)).strip()
        v = info.get(target)
        if not v or not v.get('image') or v.get('disambig'):
            continue
        f = v['image'].replace('_', ' ')
        if IMG_BAD.search(f) or f in used_images or any(f == c[0] for c in cands):
            continue
        person = dates_of(v['extract'])[0] == 'person'
        thing = bool(THING.search(v['extract'][:110])) and not person
        if person or thing:
            cands.append((f, disp if person else v['title'], 0 if person else 1, target))
    cands.sort(key=lambda c: c[2])
    res = []
    for f, cap, _, target in cands[:2]:
        used_images.add(f)
        res.append((f, '[[%s|%s]]' % (target, cap) if target != cap else '[[%s]]' % cap))
    return res

# ---------------------------------------------------------------- the outline text
def event_lines(es, seen, with_pictures):
    lines = []
    for e in es:
        text = link_text(e['text'])
        text = add_dates(text, seen, e['date'])
        if with_pictures:
            for f, cap in pictures(text, e['date']):
                lines.append('[[File:%s|200px|%s]]' % (f, cap))
        d = e['date'].strip()
        lines.append("* '''%s''' %s" % (d, text))
    return lines

STAGE_INTRO = {
    'Rhetorical stage': 'Calculations are described purely by words.',
    'Syncopated stage': 'Quantities and common algebraic operations begin to be represented by symbolic abbreviations.',
    'Symbolic stage': 'Comprehensive notational systems for formulas are the norm.',
}
lines, seen_main, stage = [], set(), None
for per in PERIODS:
    es = [e for e in events if e['p'] == per]
    st = STAGE_OF.get(per, 'Symbolic stage')
    if st != stage:
        stage = st
        lines += ['== %s ==' % st, STAGE_INTRO[st]]
    lines.append('=== %s ===' % per)
    lines += event_lines(es, seen_main, True)
body = '\n' + invoke(MODULE, 'math', '\n'.join(lines), flags=['--switcher', '--no-original']) + '\n'

solo = ''
for k, title in REGION_TITLE.items():
    es = [e for e in events if k in e['tags']]
    if len(es) < 3:
        continue                       # too few events for a timeline of its own
    ls = event_lines(es, set(), False)
    call = invoke(MODULE, 'math' + k.lower(), '\n'.join(ls), flags=['--switcher', '--no-original'])
    solo += '\n\n== %s ==\n%s' % (title, call)

# ---------------------------------------------------------------- the rest of the page
works = re.search(r'^=== ?Works cited ?===\n(.*?)(?=^==)', hom, re.S | re.M)
works = works.group(1).strip() if works else ''
see_also = re.search(r'==See also==\n(.*?)\n==References==', tom, re.S)
see_also = see_also.group(1).strip() if see_also else ''
refs_extra = re.search(r'==References==\n\{\{reflist\}\}\n(.*?)\n==External links==', tom, re.S)
refs_extra = refs_extra.group(1).strip() if refs_extra else ''
ext = re.search(r'==External links==\n(.*?)\n\n', tom, re.S)
ext = ext.group(1).strip() if ext else ''
lead = ("This is a [[timeline]] of [[pure mathematics|pure]] and [[applied mathematics]] [[History of mathematics|history]]. "
        "It is divided into three stages, corresponding to stages in the [[History of mathematical notation|development of mathematical notation]]: "
        "a \"rhetorical\" stage in which calculations are described purely by words, a \"syncopated\" stage in which quantities and common "
        "algebraic operations are beginning to be represented by symbolic abbreviations, and finally a \"symbolic\" stage, in which "
        "comprehensive notational systems for formulas are the norm. Below the timeline, the same events are grouped by civilization, "
        "as in [[History of mathematics]].")

# the same footnote, wherever it is repeated, is defined once (a name for the unnamed ones, <ref name=".." /> for the repeats)
def dedupe(text):
    seen, by_body, k = set(), {}, [0]
    def one(m):
        tag = m.group(0)
        nm = re.match(r'<ref\s+name\s*=\s*"?([^">/\s]+)"?\s*(/?)>', tag)
        if nm and nm.group(2):
            return tag
        body = re.sub(r'^<ref[^>]*>|</ref>$', '', tag)
        if not body.strip():
            return ''                              # an empty footnote in the article
        name = nm.group(1) if nm else by_body.get(body)
        if not name:
            k[0] += 1
            name = by_body[body] = 'm%d' % k[0]
        by_body.setdefault(body, name)
        if name in seen:
            return '<ref name="%s" />' % name
        seen.add(name)
        return '<ref name="%s">%s</ref>' % (name, body)
    return re.sub(r'<ref(?:\s[^>]*)?/>|<ref(?:\s[^>]*)?>.*?</ref>', one, text, flags=re.S)

# the Works cited of History of mathematics: only the books that the short citations of the page point to
cited = set(re.findall(r'\{\{(?:Harv|sfnp?|harvnb)\|([^|}]+)', body + solo))
entries = re.split(r'\n(?=\s*\*)', re.sub(r'<!--.*?-->', '', works, flags=re.S))
keep = [en for en in entries if any(re.search(r'(?:last\d?|surname)\s*=\s*%s\b' % re.escape(c.strip()), en) for c in cited)]
works = '{{refbegin|30em}}\n' + '\n'.join(keep) + '\n{{refend}}' if keep else ''
page = ('{{short description|Chronology of mathematics}}\n{{Use mdy dates|date=November 2026}}\n\n'
        + lead + '\n\n__TOC__\n\n== Timeline ==' + body + solo
        + '\n\n== See also ==\n' + see_also + '\n\n== References ==\n{{reflist|30em}}\n' + refs_extra
        + ('\n\n== Works cited ==\n' + works if works else '') + '\n\n== External links ==\n' + ext + '\n\n{{Areas of mathematics}}\n{{History of mathematics}}\n')
page = dedupe(page)
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print('%d events -> %s (%d bytes)' % (len(events), out, len(page)))
