#!/usr/bin/env python3
"""Draft: "Timeline of Go" built with the live modules (TimelineRail, OutlineList, OutlineTable, ViewSwitcher).

Usage: python3 tools/convert_go.py [--module=TimelineRail/sandbox] [out.wikitext]

The events come from two places:
  * [[History of Go]] on English Wikipedia (CC BY-SA 4.0). Each event below names a phrase ("ref") of that
    article; the footnote that follows the phrase in its wikitext is copied to the event. The wording of the
    events is a condensed rewrite, not a copy.
  * the Go | Hall of Fame timeline (https://go-hall-of-fame.vercel.app/timeline), the author's own project:
    the events marked HOF below. Those that the History of Go does not cover have no footnote.
Say in the edit summary that text and sources are adapted from [[History of Go]].
"""
import pathlib, re, subprocess, sys, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from outline_call import invoke

root = pathlib.Path(__file__).resolve().parent.parent
FLAGS = [a for a in sys.argv[1:] if a.startswith('--')]
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
MODULE = next((f.split('=', 1)[1] for f in FLAGS if f.startswith('--module=')), 'TimelineRail')
out = pathlib.Path(ARGS[0]) if ARGS else root / 'drafts' / 'Timeline_of_Go__lua.wikitext'

url = 'https://en.wikipedia.org/w/index.php?action=raw&title=History_of_Go'
hog = subprocess.run(['curl', '-sL', '-A', 'timeline-draft/1.0', url], capture_output=True, text=True).stdout
if 'Weiqi' not in hog:
    sys.exit('Could not fetch History of Go')

# ---------------------------------------------------------------- footnotes of History of Go
REF_ANY = re.compile(r'<ref(?:\s[^>]*)?/>|<ref(?:\s[^>]*)?>.*?</ref>', re.S)
SFN = r'\{\{sfnp?\|[^{}]*\}\}'      # short citation: needs the Sources section of History of Go
ITEM = re.compile(r'<ref(?:\s[^>]*)?/>|<ref(?:\s[^>]*)?>.*?</ref>|' + SFN, re.S)
FULL = {}     # name -> full definition
for m in REF_ANY.finditer(hog):
    nm = re.match(r'<ref\s+name\s*=\s*"?([^">/\s]+)"?\s*>', m.group(0))
    if nm:
        FULL[nm.group(1)] = m.group(0)

def refs_after(phrase):
    """The footnotes of the sentence that holds `phrase` (those between the phrase and the end of the
    sentence, and those that follow its full stop)."""
    i = hog.find(phrase)
    if i < 0:
        print('NO PHRASE:', phrase)
        return []
    seg = hog[i:i + 1500]
    masked = REF_ANY.sub(lambda m: '\x01' * len(m.group(0)), seg)
    for _ in range(4):             # nested templates, innermost first
        masked = re.sub(r'\{\{[^{}]*\}\}', lambda m: '\x01' * len(m.group(0)), masked)
    masked = re.sub(r'\[\[[^\]]*\]\]', lambda m: '\x01' * len(m.group(0)), masked)
    ends = [m.end() for m in re.finditer(r'[.!?]["”]?(?=\s|\x01|$)', masked)][:3]   # this sentence and the next two
    found = []
    for end in ends or [len(seg)]:
        while True:                # footnotes stuck to the full stop
            t = ITEM.match(seg, end)
            if not t:
                break
            end = t.end()
        found = [r.group(0) for r in ITEM.finditer(seg[:end])
                 if not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', r.group(0))]   # no Japanese-language footnotes
        if found:                  # the footnote of the sentence, else that of the next one
            break
    if not found:
        print('NO REF:', phrase)
    return found[:3]

used = set()
def ref_text(phrase):
    out = []
    for r in refs_after(phrase):
        if r.startswith('{{sfn'):
            out.append(r)
            continue
        nm = re.match(r'<ref\s+name\s*=\s*"?([^">/\s]+)"?\s*(/?)>', r)
        if nm:
            name = nm.group(1)
            if name in used:
                out.append('<ref name="%s" />' % name)
            else:
                used.add(name)
                out.append(FULL.get(name, r))
        else:
            out.append(r)
    return ''.join(out)

# ---------------------------------------------------------------- the events
# (date, text, phrase of History of Go whose footnote is used or None, source)
# Section titles are level-2 headings.
GO = '[[Go (game)|Go]]'
SECTIONS = [
 ('Legends and first records', [
  ('Unknown', 'The "Rotten Handle" legend of the origin of the game: a carpenter in Zhejiang watches deities playing a mysterious game and loses track of time.', None, 'HOF'),
  ('c. 2356–2255 BCE', 'According to legend, Emperor Yao creates the game to teach discipline and balance to his son Danzhu.', 'According to legend, the game was created', 'HOG+HOF'),
  ('548 BCE', 'The earliest written reference to the game is usually taken to be the historical annal [[Zuo Zhuan]], about an event of this year; it is also mentioned in the [[Analects]] of Confucius and in the books of [[Mencius]].', 'The earliest written reference', 'HOG+HOF'),
  ('206 BCE – 24 CE', 'Western Han: a broken piece of a pottery board, the earliest board found in China, is later unearthed in Shaanxi.', 'Chinese archaeologists have discovered a broken piece', 'HOG'),
 ]),
 ('Ancient and medieval East Asia', [
  ('1st–3rd century', 'Eastern Han: Ban Gu writes {i}Yì Zhǐ{/i} ("The Essentials of Go"), considered the first specialized book on the game, and boards have 17 × 17 lines.', 'Ban Gu', 'HOG'),
  ('3rd–6th century', 'The board grows from 17 × 17 to 19 × 19 lines. The {i}Dunhuang Go Manual{/i}, the first book devoted to Go on the larger board, dates to this period.', 'The board expanded to 19x19', 'HOG'),
  ('475', 'In the rivalry between Goguryeo and Baekje, the Goguryeo priest To-lim uses the game of Go to spy on King Yogyong; the invasion of Baekje follows.', 'To-lim', 'HOG'),
  ('Around 500', 'Emperor Wu of Liang promotes the game and holds the first documented national tournament; 278 players receive a rank.', 'Emperor Wu also organized', 'HOG'),
  ('618–907', 'Tang dynasty: the court creates the post of Go attendant ("Qídàizhào") for players who play against the emperor, and players are ranked.', 'Qídàizhào', 'HOG'),
  ('Early 8th century', 'The game reaches Tibet and Mongolia, where the 17 × 17 board survives.', 'early eighth century', 'HOG'),
  ('8th century', 'Go reaches Japan, traditionally brought by Kibi no Makibi; the Taihō Code of 701 already describes it.', 'Kibi no Makibi', 'HOG'),
  ('737', 'The Chinese player Yang Jiying travels to Korea as an envoy and no player of Silla can match him.', 'Yang Jiying', 'HOG'),
  ('c. 1050', 'Song dynasty: Wang Ni writes {i}The Classic of Weiqi{/i}, tying the board to yin and yang and to the days of the year.', 'Wang Ni', 'HOG'),
  ('c. 1100', 'The {i}Wangyou Qingle Ji{/i} records a game between a Japanese prince and Gu Shiyan, probably the best Chinese player of his time, the first recorded double-ladder breaker.', 'Gu Shiyan played against', 'HOG+HOF'),
  ('1349', 'Yuan dynasty: the {i}Xuanxuan Qijing{/i} ("Gateway to All Marvels"), a large collection of problems, ''joseki'' and set patterns, is compiled; it becomes one of the most influential Go books.', 'Xuánxuán Qí Jīng', 'HOG+HOF'),
  ('Ming dynasty', 'The Hongwu Emperor issues an "Edict Banning Weiqi" in the face of widespread gambling on the game.', 'Edict Banning', 'HOG'),
  ('1582', 'Honinbo Sansa plays a triple ko against Kashio Rigen at a monastery in Kyoto in the presence of Oda Nobunaga; the game is suspended. The next day Nobunaga is killed, and a triple ko is considered bad luck ever after.', None, 'HOF'),
  ('1588', 'Toyotomi Hideyoshi organizes the first Japanese Go tournament; Hon\'inbō (Sansa) wins and is granted a salary.', 'first Japanese Go tournament', 'HOG'),
 ]),
 ('Edo-period Japan and Qing China', [
  ('1603', 'Honinbo Sansa is appointed by Shogun Tokugawa Ieyasu as head of the Go world: the major Japanese Go school system begins.', 'Godokoro', 'HOG+HOF'),
  ('1612', 'The Tokugawa shogunate establishes four hereditary Go houses (Hon\'inbō, Inoue, Yasui and Hayashi) that compete for 300 years, with an annual Castle Game before the shogun.', 'In 1612', 'HOG'),
  ('c. 1650', 'Huang Longshi, probably the strongest Chinese player of the Qing dynasty, is born (c. 1650 – c. 1694).', 'Huang Longshi', 'HOG+HOF'),
  ('Late 17th century', 'The fourth Hon\'inbō, Dōsaku (1645–1702), defeats every top player of his time and is praised as having "thirteen-dan strength".', 'thirteen-dan', 'HOG'),
  ('1694', 'Thomas Hyde writes the first detailed description of Go in a European language, in his treatise on oriental board games.', 'Thomas Hyde', 'HOG'),
  ('1739', 'Shi Xiangxia and Fan Xiping play the "Ten Games at Danghu" in Pinghu, Zhejiang.', 'Dànghú Shí Jú', 'HOG'),
  ('1840', 'The "blood-vomiting game": Hon\'inbō Jōwa beats Akaboshi Intetsu in a week-long match; Akaboshi collapses from exhaustion and dies soon after.', 'blood-vomiting', 'HOG'),
  ('1846', 'The "ear-reddening game": Honinbo Shusaku\'s move 127 stuns Gennan Inseki, and becomes one of the best moves of all time.', 'ear-reddening', 'HOG+HOF'),
 ]),
 ('Modern professional Go', [
  ('1868', 'The Meiji Restoration dissolves the official system of the shogunate; Go loses its patrons and the masters struggle.', 'Meiji Restoration', 'HOG'),
  ('1872', 'The first recorded game of Go in Europe is played between Kido Takayoshi and Ōkubo Toshimichi of the Iwakura Mission.', 'The first recorded game of Go in Europe', 'HOG'),
  ('1880', 'Oskar Korschelt, who learned the game in Japan from Murase Shūho, publishes {i}Das Go Spiel{/i}: the first systematic description in a Western language.', 'Das Go Spiel', 'HOG'),
  ('1924', 'The Nihon Ki-in, Japan\'s professional Go association, is founded, ending the hereditary house system and inaugurating the modern rank and tournament system.', 'established in 1924', 'HOG+HOF'),
  ('1933', 'The "Game of the Century": Go Seigen opens at the three-three, star and center points against Honinbo Shusai, in a controversial three-month game that challenges the old system.', 'game of the century', 'HOG+HOF'),
  ('1936', 'The Nihon Ki-in holds the first Hon\'inbō tournament, after Shūsai hands over the title.', 'first tournaments in 1936', 'HOG'),
  ('1945', 'The "Game Under the Atomic Bomb": the second game of the 3rd Hon\'inbō match, played near Hiroshima on August 6, is finished after the blast.', 'Game Under the Atomic Bomb', 'HOG'),
  ('1950', 'Go Seigen is awarded 9 dan, and becomes the world\'s best player; he wins his ten-game matches against all top rivals until 1956.', 'In 1950', 'HOG+HOF'),
  ('1954', 'The Korea Baduk Association is established.', 'January 28, 1954', 'HOG'),
  ('1959', 'Sakata Eio 9p takes the first place from Go Seigen.', None, 'HOF'),
  ('1960', 'The China–Japan Go Friendship Match starts; it is held every year until 1991.', 'Starting in 1960', 'HOG'),
  ('1976', 'After the "Meijin Incident" of 1974, the Tengen (1975), Kisei and Gosei (1976) titles complete the seven major Japanese titles.', 'Meijin Incident', 'HOG'),
  ('1984', 'Nie Weiping leads China to victory over Japan in the first China–Japan Super Go Matches, a national triumph.', 'first China-Japan Supermatches', 'HOG+HOF'),
  ('1989', 'Cho Hunhyun, the only Korean entrant, wins the first Ing Cup, the "Olympics of Go", beating Nie Weiping.', 'inaugural [[Ing Cup]]', 'HOG+HOF'),
  ('1990', 'Lee Changho, a student of Cho Hunhyun, becomes the world no. 1 at 15 years old.', None, 'HOF'),
 ]),
 ('Go in the West and in space', [
  ('1978', 'Manfred Wimmer becomes the first Westerner to receive a professional certificate from an East Asian Go association.', 'Manfred Wimmer', 'HOG'),
  ('1996', 'Astronauts Daniel Barry and Koichi Wakata become the first people to play Go in space.', 'first people to play Go in space', 'HOG'),
  ('1998–2003', 'The manga {i}Hikaru no Go{/i} (later also an anime) sparks a Go boom among young players in Japan.', 'Hikaru no Go', 'HOG'),
  ('2000', 'The American Michael Redmond is the first Westerner to reach 9 dan. In February, Rui Naiwei, playing for Korea, becomes the first woman to win a major international title.', 'Rui Naiwei', 'HOG'),
 ]),
 ('The AI era', [
  ('2016', 'Google\'s AlphaGo beats Lee Sedol 4–1 in Seoul, the first time an AI beats a top professional. The same year, Iyama Yūta holds all seven Japanese major titles at once.', '4-1 victory', 'HOG+HOF'),
  ('Late 2016 – early 2017', 'A stronger AlphaGo ("Master") wins 60 games in a row, anonymously, online against top professionals.', None, 'HOF'),
  ('May 2017', 'A new and much improved AlphaGo plays Ke Jie.', None, 'HOF'),
  ('June 2018', 'Shin Jinseo 9p, whose style resembles that of the AIs, becomes the world no. 1.', None, 'HOF'),
  ('2019', 'The open-source Go AI KataGo is created by David Wu. Lee Sedol announces his retirement, citing AlphaGo as "an entity that cannot be defeated".', 'retirement announcement in 2019', 'HOG+HOF'),
  ('2026', 'Shin Jinseo defeats a new version of KataGo on a 2-stone handicap, coming back from a first-game defeat to win the next two.', None, 'HOF'),
 ]),
]

# first mention of each person or thing is linked (the titles were checked against the wiki)
LINKS = {
    'Emperor Yao': 'Emperor Yao', 'Honinbo Sansa': "Hon'inbō Sansa|Honinbo Sansa", 'Honinbo Shusaku': "Hon'inbō Shūsaku|Honinbo Shusaku",
    'Honinbo Shusai': "Hon'inbō Shūsai|Honinbo Shusai", 'Go Seigen': 'Go Seigen', 'Sakata Eio': 'Sakata Eio',
    'Nie Weiping': 'Nie Weiping', 'Cho Hunhyun': 'Cho Hun-hyun|Cho Hunhyun', 'Lee Changho': 'Lee Chang-ho|Lee Changho',
    'Shin Jinseo': 'Shin Jin-seo|Shin Jinseo', 'AlphaGo': 'AlphaGo', 'KataGo': 'KataGo', 'Ke Jie': 'Ke Jie',
    'Michael Redmond': 'Michael Redmond', 'Rui Naiwei': 'Rui Naiwei', 'Huang Longshi': 'Huang Longshi',
    'Oskar Korschelt': 'Oskar Korschelt', 'Thomas Hyde': 'Thomas Hyde', 'Kibi no Makibi': 'Kibi no Makibi',
    'Ing Cup': 'Ing Cup', 'Lee Sedol': 'Lee Sedol', 'Nihon Ki-in': 'Nihon Ki-in',
}
linked = set()
def link(text):
    for name, target in LINKS.items():
        if name in linked or '[[%s' % name in text or ('[[' + target.split('|')[0]) in text:
            continue
        if name in text:
            text = text.replace(name, '[[%s]]' % target if '|' in target or target != name else '[[%s]]' % name, 1)
            linked.add(name)
    return text

lines, n = [], 0
for title, events in SECTIONS:
    lines.append('== %s ==' % title)
    for date, text, phrase, src in events:
        n += 1
        text = link(text.replace('{i}', "''").replace('{/i}', "''"))
        refs = ref_text(phrase) if phrase and 'HOG' in src else ''
        lines.append("* '''%s''' %s%s" % (date, text, refs))

body = invoke(MODULE, 'go', '\n'.join(lines), flags=['--switcher', '--no-original'])

sources = re.search(r'^== ?Sources ?==\n(.*?)(?=^==)', hog, re.S | re.M)
sources = sources.group(1).strip() if sources else ''
lead = ("This is a timeline of the history of the board game [[Go (game)|Go]] (Chinese ''weiqi'', Korean ''baduk''), "
        "from its legendary origins in ancient China to the age of AI. For the full story, see [[History of Go]].")
page = (
    '{{User sandbox}}\n'
    '<!-- Draft of a "Timeline of Go" with [[Module:TimelineRail]]. The events and their sources are adapted from [[History of Go]] '
    '(see its history for attribution) and from the Go | Hall of Fame timeline (go-hall-of-fame.vercel.app). -->\n'
    '{{Short description|Chronology of the board game Go}}\n'
    '{{Use dmy dates|date=November 2026}}\n\n'
    + lead + '\n\n== Timeline ==\n' + body +
    '\n\n== See also ==\n* [[History of Go]]\n* [[Go (game)]]\n* [[Timeline of artificial intelligence]]\n'
    '\n== References ==\n'
    '{{Reflist|30em}}\n\n== Sources ==\n' + sources + '\n'
    '\n[[:Category:Go (game)]]\n'
)
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print('%d events -> %s (%d bytes)' % (n, out, len(page)))
