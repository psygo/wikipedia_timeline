#!/usr/bin/env python3
"""Draft: "Timeline of Go" built with the live modules (TimelineRail, OutlineList, OutlineTable, ViewSwitcher).

Usage: python3 tools/convert_go.py [--module=TimelineRail/sandbox] [out.wikitext]

The events come from two places:
  * [[History of Go]] on English Wikipedia (CC BY-SA 4.0). Each event below names a phrase ("ref") of that
    article; the footnote that follows the phrase in its wikitext is copied to the event. The wording of the
    events is a condensed rewrite, not a copy.
  * the Go | Hall of Fame timeline (https://go-hall-of-fame.vercel.app/timeline), the author's own project:
    the events marked HOF below. Those that the History of Go does not cover have no footnote.
  * the Go History page of Sensei's Library (https://senseis.xmp.net/?GoHistory): the events marked SL. Its text
    is not copied, the facts are put in new words; the footnote is the one History of Go already uses for that page.
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
def ref_text(phrase, named=None):
    out = []
    for r in ([FULL[named]] if named else refs_after(phrase)):
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
  ('c. 2356–2255 BCE', 'According to legend, Emperor Yao creates the game to teach discipline and balance to his son Danzhu. Another legend has Shun, his successor, invent it for his own son.', 'According to legend, the game was created', 'HOG+HOF+SL'),
  ('548 BCE', 'The earliest written reference to the game is usually taken to be the historical annal [[Zuo Zhuan]], about an event of this year; it is also mentioned in the [[Analects]] of Confucius and in the books of [[Mencius]].', 'The earliest written reference', 'HOG+HOF'),
  ('3rd century BCE', 'Mencius mentions a famous player called Yi Qiu.', None, 'SL'),
  ('206 BCE – 24 CE', 'Western Han: a broken piece of a pottery board, the earliest board found in China, is later unearthed in Shaanxi.', 'Chinese archaeologists have discovered a broken piece', 'HOG'),
  ('1st–3rd century', 'Eastern Han: Ban Gu writes {i}Yì Zhǐ{/i} ("The Essentials of Go"), the oldest surviving text devoted to Go, and boards have 17 × 17 lines.', 'Ban Gu', 'HOG+SL'),
  ('c. 250', 'The "Wu Diagrams" record the earliest known game of Go.', None, 'SL'),
 ]),
 ('Ancient and medieval East Asia', [
  ('3rd–6th century', 'The board grows from 17 × 17 to 19 × 19 lines. The {i}Dunhuang Go Manual{/i}, the first book devoted to Go on the larger board, dates to this period.', 'The board expanded to 19x19', 'HOG'),
  ('475', 'In the rivalry between Goguryeo and Baekje, the Goguryeo priest To-lim uses the game of Go to spy on King Yogyong; the invasion of Baekje follows.', 'To-lim', 'HOG'),
  ('Around 500', 'Emperor Wu of Liang promotes the game and holds the first documented national tournament; 278 players receive a rank.', 'Emperor Wu also organized', 'HOG'),
  ('Early 7th century', 'Chinese chronicles (the Records of the Sui) report that the Japanese enjoy Go.', None, 'SL'),
  ('618–907', 'Tang dynasty: the court creates the post of Go attendant ("Qídàizhào") for players who play against the emperor, and players are ranked. Wang Jixin is credited with the "Ten Golden Rules of Go".', 'Qídàizhào', 'HOG+SL'),
  ('Early 8th century', 'The game reaches Tibet and Mongolia, where the 17 × 17 board survives.', 'early eighth century', 'HOG'),
  ('8th century', 'Go reaches Japan, traditionally brought back from the Tang court by Kibi no Makibi; the Taihō Code of 701 already describes it.', 'Kibi no Makibi', 'HOG+SL'),
  ('737', 'The Chinese player Yang Jiying travels to Korea as an envoy and no player of Silla can match him.', 'Yang Jiying', 'HOG'),
  ('c. 1050', 'Song dynasty: a major treatise in thirteen chapters, the {i}Classic of Go{/i} ({i}Qíjīng Shísān Piān{/i}), is written; the Song era also produces many other treatises on strategy.', 'Wang Ni', 'HOG+SL'),
  ('c. 1100', 'The {i}Wangyou Qingle Ji{/i}, compiled by Li Yimin, is the oldest surviving Go book. It collects essays, old game records and the first set of tsumego problems, among them a game between a Japanese prince and Gu Shiyan, the first recorded double-ladder breaker.', 'Gu Shiyan played against', 'HOG+HOF+SL'),
  ('1349', 'Yuan dynasty: Yan Defu and Yan Tianzhang compile the {i}Xuanxuan Qijing{/i} ("Gateway to All Marvels"), six volumes with 376 problems, essays and game records; it inspires problem books around the world.', 'Xuánxuán Qí Jīng', 'HOG+HOF+SL'),
  ('Ming dynasty', 'Chinese scoring changes from territory to stone scoring. The Hongwu Emperor issues an "Edict Banning Weiqi" in the face of widespread gambling on the game.', 'Edict Banning', 'HOG+SL'),
  ('1582', 'Honinbo Sansa plays a triple ko against Kashio Rigen at a monastery in Kyoto in the presence of Oda Nobunaga; the game is suspended. The next day Nobunaga is killed, and a triple ko is considered bad luck ever after.', None, 'HOF'),
  ('1588', 'Toyotomi Hideyoshi organizes the first Japanese Go tournament; Hon\'inbō (Sansa) wins and is granted a salary.', 'first Japanese Go tournament', 'HOG'),
 ]),
 ('Edo-period Japan and Qing China', [
  ('1603', 'Honinbo Sansa is appointed by Shogun Tokugawa Ieyasu as head of the Go world (Meijin Godokoro): the major Japanese Go school system begins.', 'Godokoro', 'HOG+HOF+SL'),
  ('1612', 'The Tokugawa shogunate establishes four hereditary Go houses (Hon\'inbō, Inoue, Yasui and Hayashi) and pays them stipends; they compete for 250–300 years.', 'In 1612', 'HOG+SL'),
  ('1626–1628', 'The first castle game, played before the shogun, takes place in 1626; in 1628 the castle games become an official yearly ceremony.', None, 'SL'),
  ('1645–1653', 'The first official challenge match (sōgo) to decide the Meijin, between Hon\'inbō Sanetsu and Yasui Sanchi.', 'The first such challenge match', 'HOG+SL'),
  ('c. 1650', 'Huang Longshi, probably the strongest Chinese player of the Qing dynasty, is born (c. 1650 – c. 1694).', 'Huang Longshi', 'HOG+HOF'),
  ('Late 17th century', 'The fourth Hon\'inbō, Dōsaku (1645–1702), defeats every top player of his time and is praised as having "thirteen-dan strength".', 'thirteen-dan', 'HOG'),
  ('1713', 'The {i}Igo Hatsuyoron{/i}, a collection of very hard problems, is created.', None, 'SL'),
  ('1739', 'Shi Xiangxia and Fan Xiping play the "Ten Games at Danghu" in Pinghu, Zhejiang.', 'Dànghú Shí Jú', 'HOG+SL'),
  ('1840', 'The "blood-vomiting game": Hon\'inbō Jōwa beats Akaboshi Intetsu in a week-long match; Akaboshi collapses from exhaustion and dies soon after.', 'blood-vomiting', 'HOG+SL'),
  ('1846', 'The "ear-reddening game": Honinbo Shusaku\'s move 127 stuns Gennan Inseki, and becomes one of the best moves of all time.', 'ear-reddening', 'HOG+HOF'),
  ('1863', 'The last castle games are played as the crisis of the shogunate disrupts the ceremonies.', None, 'SL'),
 ]),
 ('Modern professional Go', [
  ('1868', 'The Meiji Restoration ends the official stipends of the Go houses; Go loses its patrons and the masters struggle.', 'Meiji Restoration', 'HOG+SL'),
  ('1878', 'The first newspaper Go column appears in Japan, on 1 April. In 1879 the Hoensha society forms; its journal {i}Igo Shinpo{/i} is the first Go magazine.', None, 'SL'),
  ('1909–1910', 'The Japanese professional Takabe Dōhei visits China and introduces play without fixed starting stones.', None, 'SL'),
  ('1924', 'The [[Nihon Ki-in]], Japan\'s professional Go association, is founded, ending the hereditary house system and inaugurating the modern rank and tournament system.', 'established in 1924', 'HOG+HOF+SL'),
  ('1933', 'The "Game of the Century": Go Seigen opens at the three-three, star and center points against Honinbo Shusai, in a controversial three-month game that challenges the old system.', 'game of the century', 'HOG+HOF'),
  ('1935', 'A game of Go is broadcast on radio for the first time.', None, 'SL'),
  ('1936–1938', 'Shūsai hands the Hon\'inbō title to the Nihon Ki-in (1936) and retires in 1938 after a game against Kitani Minoru that inspires Kawabata\'s novel {i}The Master of Go{/i}.', 'first tournaments in 1936', 'HOG+SL'),
  ('1941', 'Sekiyama Riichi wins the first Hon\'inbō title tournament, one of the first major modern tournaments with komi (4.5 points).', None, 'SL'),
  ('1945', 'The "Game Under the Atomic Bomb": the second game of the 3rd Hon\'inbō match, played near Hiroshima on August 6, is finished after the blast.', 'Game Under the Atomic Bomb', 'HOG'),
  ('1949', 'Fujisawa Hōsai becomes the first player to reach 9 dan under the Oteai promotion system.', None, 'SL'),
  ('1950', 'Go Seigen is awarded 9 dan, and becomes the world\'s best player; he wins his ten-game matches against all top rivals until 1956.', 'In 1950', 'HOG+HOF'),
  ('1954', 'The Korea Baduk Association (Hankuk Kiwon) is established, on 28 January. The first NHK Cup is broadcast on radio; it moves to television in 1962.', 'January 28, 1954', 'HOG+SL'),
  ('1956', 'The first professional tournament in Korea, the Kuksu Cup, starts.', None, 'SL'),
  ('1959', 'Sakata Eio 9p takes the first place from Go Seigen.', None, 'HOF'),
  ('1960', 'The China–Japan Go Friendship Match starts; it is held every year until 1991.', 'Starting in 1960', 'HOG'),
  ('1962', 'Fujisawa Shūkō wins the first Meijin title tournament.', None, 'HOG+SL'),
  ('1976', 'After the "Meijin Incident" of 1974, the Tengen (1975), Kisei and Gosei (1976) titles complete the seven major Japanese titles. Fujisawa Shūkō wins the first Kisei in 1977.', 'Meijin Incident', 'HOG+SL'),
  ('1984', 'Nie Weiping leads China to victory over Japan in the first China–Japan Super Go Matches, a national triumph.', 'first China-Japan Supermatches', 'HOG+HOF'),
  ('1988', 'Takemiya Masaki wins the first Fujitsu Cup, one of the first international tournaments.', None, 'SL'),
  ('1989', 'Cho Hunhyun, the only Korean entrant, wins the first Ing Cup, the "Olympics of Go", beating Nie Weiping.', 'inaugural [[Ing Cup]]', 'HOG+HOF+SL'),
  ('1990', 'Lee Changho, a student of Cho Hunhyun, becomes the world no. 1 at 15 years old.', None, 'HOF'),
  ('1995', 'Ma Xiaochun is the first Chinese player to win an international tournament, taking both the Fujitsu Cup and the Tongyang Securities Cup.', None, 'SL'),
  ('1996', 'Lee Changho wins the first LG Cup.', None, 'SL'),
  ('1998–2003', 'The manga {i}Hikaru no Go{/i} (later also an anime) sparks a Go boom among young players in Japan.', 'Hikaru no Go', 'HOG+SL'),
  ('2000', 'Rui Naiwei, playing for Korea, wins the 43rd Kuksu in February and becomes the first woman to win a major title.', 'Rui Naiwei', 'HOG+SL'),
  ('2003', 'The Oteai promotion system is discontinued in Japan and a new one introduced.', None, 'SL'),
 ]),
 ('Go in the West and in space', [
  ('1615', 'Nicolas Trigault publishes in Augsburg the diaries of the Jesuit Matteo Ricci, which explain the game of weiqi; the book goes through at least 16 editions in European languages.', None, 'SL'),
  ('1694', 'Thomas Hyde writes the first detailed description of Go in a European language, in his treatise on oriental board games.', 'Thomas Hyde', 'HOG+SL'),
  ('17th–18th century', 'The philosopher Leibniz publishes an article on Go with a picture of a game, saying he does not know all the rules.', 'Leibniz', 'HOG+SL'),
  ('1872', 'The first recorded game of Go in Europe is played between Kido Takayoshi and Ōkubo Toshimichi of the Iwakura Mission.', 'The first recorded game of Go in Europe', 'HOG'),
  ('1880', 'Oskar Korschelt, who learned the game in Japan from Murase Shūho, publishes {i}Das Go Spiel{/i}: the first systematic description in a Western language.', 'Das Go Spiel', 'HOG+SL'),
  ('1905–1908', 'Edward Lasker learns Go in Berlin (1905) and later founds the New York Go Club; in 1908 Arthur Smith publishes the first Go book in English, {i}The Game of Go{/i}.', 'In 1905', 'HOG+SL'),
  ('1934–1937', 'Lasker\'s {i}Go and Go-moku{/i} (1934) helps popularize the game in the US; the American Go Association is formed in 1935 and the German Go Association in 1937.', 'Lasker\'s book', 'HOG+SL'),
  ('1978', 'Manfred Wimmer becomes the first Westerner to receive a professional certificate from an East Asian Go association (Kansai Ki-in); James Kerwin is the first at the Nihon Ki-in.', 'Manfred Wimmer', 'HOG+SL'),
  ('1996', 'Astronauts Daniel Barry and Koichi Wakata become the first people to play Go in space.', 'first people to play Go in space', 'HOG'),
  ('2000', 'The American Michael Redmond is the first Westerner to reach 9 dan.', 'Michael Redmond', 'HOG+SL'),
  ('2011–2014', 'The American Go Association signs an agreement with the Korean Baduk Association to promote its own professional system (2011); the European Go Federation creates its own (2014).', None, 'SL'),
 ]),
 ('Go online and computer Go', [
  ('1968', 'Albert Zobrist writes the first program that plays complete games of Go.', None, 'SL'),
  ('19 December 1976', 'A friendship match between Taiwan and the United States is played by teletype; in 1978 the UK and the USSR play one by telephone.', None, 'SL'),
  ('1984', 'The first computer Go event, the Acornsoft tournament for the BBC Micro, is held. Greg Hale writes {i}inetgo{/i}, probably the first program to play Go over the internet.', None, 'SL'),
  ('1985', 'The Ing Prize for computer programs starts; it expires in 2000, when the last challenge was won by HandTalk at an 11-stone handicap against a young professional.', None, 'SL'),
  ('2 February 1992', 'The Internet Go Server (IGS), the first server dedicated to Go, starts.', None, 'SL'),
  ('1993', 'Bruegmann\'s Gobble is the first Go program based on random playouts (Monte Carlo).', None, 'SL'),
  ('2006', 'The UCT algorithm, a Monte Carlo tree search, is developed; a program using it, CrazyStone, wins the Computer Olympiad 9×9 Go event the same year.', None, 'SL'),
  ('2008', 'MoGo wins one of three games against the professional Catalin Taranu on 9×9 and later beats an 8-dan Korean professional on 19×19 with a 9-stone handicap.', None, 'SL'),
  ('2012', 'The program Zen beats Takemiya Masaki in games with 5 and 4 handicap stones.', None, 'SL'),
 ]),
 ('The AI era', [
  ('October 2015', 'AlphaGo, made by Google, beats the European champion Fan Hui (2p) 5–0 in even games: the first time a program beats a professional.', None, 'SL'),
  ('2016', 'Google\'s AlphaGo beats Lee Sedol 4–1 in Seoul, the first time an AI beats a top professional. The same year, Iyama Yūta holds all seven Japanese major titles at once.', '4-1 victory', 'HOG+HOF+SL'),
  ('Late 2016 – early 2017', 'A stronger AlphaGo ("Master") wins 60 games in a row, anonymously, online against top professionals.', None, 'HOF'),
  ('May 2017', 'A new and much improved AlphaGo plays Ke Jie and wins all three games; Ke Jie says its play is "like a god of Go".', None, 'HOF+SL'),
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

# Pictures on Wikimedia Commons, the ones History of Go uses: (date, a part of the event's text, file)
IMAGES = [
    ('1st–3rd century', 'Ban Gu', 'Go Board Han dynasty.JPG'),
    ('3rd–6th century', 'Dunhuang', 'British Library Dunhuang Go Manual.jpg'),
    ('475', 'To-lim', 'Baekje Game of Baduk (Copy) (30079340202).jpg'),
    ('618–907', 'Tang', 'Early Go stones.jpeg'),
    ('Early 8th century', 'Tibet', 'TibetGoBoard.png'),
    ('1349', 'Xuanxuan', 'Inner Mongolia Museum weiqi stones.jpg'),
    ('Ming dynasty', 'Hongwu', 'Go Ming Court.jpg'),
    ('1588', 'Hideyoshi', 'Go board Hideyoshi Ieyasu Ryogenin M1868.jpg'),
    ('1603', 'Sansa', 'Sansa.jpg'),
    ('Late 17th century', 'Dōsaku', 'Honinbo Dosaku.png'),
    ('1846', 'ear-reddening', 'Kulak_kizartan_go.png'),
    ('1933', 'Game of the Century', 'Game_of_the_Century_-_Honinbo_Shusai_(W)_vs_Go_Seigen_(B)_no_text.svg'),
    ('1936–1938', 'Shūsai', 'Honinbo Shusai.jpg'),
    ('1950', 'Go Seigen', 'Go_Seigen_and_Kitani_Minoru.jpg'),
    ('1959', 'Sakata', 'Sakata-Eio-1.jpg'),
    ('2000', 'Redmond', 'Michael Redmond in 2018.png'),
    ('October 2015', 'AlphaGo', 'AlphaGo_computer_rack.jpg'),
    ('2016', 'Lee Sedol', 'LG전자, 이세돌 9단과 함께 학생들의 꿈 그린다.jpg'),
    ('2019', 'KataGo', 'KataGoanalisis.png'),
]
for _d, _t, _f in IMAGES:       # a typo here would silently drop a picture
    assert any(d == _d and _t in t for _, evs in SECTIONS for d, t, *_ in evs), (_d, _t)

lines, n = [], 0
for title, events in SECTIONS:
    lines.append('== %s ==' % title)
    for date, text, phrase, src in events:
        n += 1
        text = link(text.replace('{i}', "''").replace('{/i}', "''"))
        refs = ref_text(phrase) if phrase and 'HOG' in src else ''
        if 'SL' in src:
            refs += ref_text(None, named=':11')
        for d, t, f in IMAGES:
            if d == date and t in text:
                lines.append('[[File:%s|200px]]' % f)
        lines.append("* '''%s''' %s%s" % (date, text, refs))

body = invoke(MODULE, 'go', '\n'.join(lines), flags=['--switcher', '--no-original'])

sources = re.search(r'^== ?Sources ?==\n(.*?)(?=^==)', hog, re.S | re.M)
sources = sources.group(1).strip() if sources else ''
lead = ("This is a timeline of the history of the board game [[Go (game)|Go]] (Chinese ''weiqi'', Korean ''baduk''), "
        "from its legendary origins in ancient China to the age of AI. For the full story, see [[History of Go]].")
page = (
    '{{User sandbox}}\n'
    '<!-- Draft of a "Timeline of Go" with [[Module:TimelineRail]]. The events and their sources are adapted from [[History of Go]] '
    '(see its history for attribution), the Go | Hall of Fame timeline (go-hall-of-fame.vercel.app) and, as facts put in new words, '
    'the Go History page of Sensei\'s Library (senseis.xmp.net/?GoHistory). -->\n'
    '{{Short description|Chronology of the board game Go}}\n'
    '{{Use dmy dates|date=November 2026}}\n\n'
    + "[[File:MET DP135836.jpg|thumb|right|upright=1.3|''Outfit for the Go Game'', woodblock print (''surimono''), 19th century, [[Metropolitan Museum of Art]].]]\n"
    + lead + '\n{{clear}}\n\n== Timeline ==\n' + body +
    '\n\n== See also ==\n* [[History of Go]]\n* [[Go (game)]]\n* [[Timeline of artificial intelligence]]\n'
    '\n== References ==\n'
    '{{Reflist|30em}}\n\n== Sources ==\n' + sources + '\n'
    '\n[[:Category:Go (game)]]\n'
)
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print('%d events -> %s (%d bytes)' % (n, out, len(page)))
