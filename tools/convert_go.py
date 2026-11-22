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

VIDEO = ('<ref name="gomagic">{{cite AV media |people=Go Magic |date= |title=Who Was the Strongest Go Player Every Year? (1950–2026) {{!}} Bar Chart Race '
         '|url=https://www.youtube.com/watch?v=oY50_IKnsMs |medium=Video |publisher=YouTube |access-date=22 November 2026}}</ref>')

GORATINGS = ('<ref name="goratings">{{cite web |title=Go Ratings |url=https://www.goratings.org/en/ |website=goratings.org '
             '|access-date=22 November 2026}}</ref>')

def ref_text(phrase, named=None):
    """Full footnotes; `dedupe` later turns repeats into <ref name="..." />."""
    out = []
    for r in ([FULL[named]] if named else refs_after(phrase)):
        nm = re.match(r'<ref\s+name\s*=\s*"?([^">/\s]+)"?\s*/>', r)
        out.append(FULL.get(nm.group(1), r) if nm else r)     # a reuse in History of Go: bring the definition
    return ''.join(out)

def dedupe(text):
    """The same footnote, wherever it is repeated (the country timelines repeat events), is defined once:
    unnamed ones get a name, later uses are <ref name="..." />."""
    seen, by_body, k = set(), {}, [0]
    def one(m):
        tag, body = m.group(0), None
        nm = re.match(r'<ref\s+name\s*=\s*"?([^">/\s]+)"?\s*(/?)>', tag)
        if nm and nm.group(2):
            return tag
        body = re.sub(r'^<ref[^>]*>|</ref>$', '', tag)
        name = nm.group(1) if nm else by_body.get(body)
        if not name:
            k[0] += 1
            name = by_body[body] = 'go%d' % k[0]
        by_body.setdefault(body, name)
        if name in seen:
            return '<ref name="%s" />' % name
        seen.add(name)
        return '<ref name="%s">%s</ref>' % (name, body)
    return re.sub(r'<ref(?:\s[^>]*)?/>|<ref(?:\s[^>]*)?>.*?</ref>', one, text, flags=re.S)

# ---------------------------------------------------------------- the events
# (date, text, phrase of History of Go whose footnote is used or None, source)
# Section titles are level-2 headings.
GO = '[[Go (game)|Go]]'
SECTIONS = [
 ('Legends and first records', [
  ('Unknown', 'The "Rotten Handle" legend of the origin of the game: a carpenter in Zhejiang watches deities playing a mysterious game and loses track of time.', None, 'HOF'),
  ('c. 2356–2255 BCE', 'According to legend, Emperor Yao creates the game to teach discipline and balance to his son Danzhu. Another legend has Shun, his successor, invent it for his own son.', 'According to legend, the game was created', 'HOG+HOF+SL'),
  ('548 BCE', 'The earliest written reference to the game is usually taken to be the historical annal Zuo Zhuan, about an event of this year; it is also mentioned in the Analects of Confucius and in the books of Mencius.', 'The earliest written reference', 'HOG+HOF'),
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
  ('1924', 'The Nihon Ki-in, Japan\'s professional Go association, is founded, ending the hereditary house system and inaugurating the modern rank and tournament system.', 'established in 1924', 'HOG+HOF+SL'),
  ('1933', 'The "Game of the Century": Go Seigen opens at the three-three, star and center points against Honinbo Shusai, in a controversial three-month game that challenges the old system.', 'game of the century', 'HOG+HOF'),
  ('1935', 'A game of Go is broadcast on radio for the first time.', None, 'SL'),
  ('1936–1938', 'Shūsai hands the Hon\'inbō title to the Nihon Ki-in (1936) and retires in 1938 after a game against Kitani Minoru that inspires the novel {i}The Master of Go{/i} by Yasunari Kawabata.', 'first tournaments in 1936', 'HOG+SL'),
  ('1941', 'Sekiyama Riichi wins the first Hon\'inbō title tournament, one of the first major modern tournaments with komi (4.5 points).', None, 'SL'),
  ('1945', 'The "Game Under the Atomic Bomb": the second game of the 3rd Hon\'inbō match, played near Hiroshima on August 6, is finished after the blast.', 'Game Under the Atomic Bomb', 'HOG'),
  ('1949', 'Fujisawa Hōsai becomes the first player to reach 9 dan under the Oteai promotion system.', None, 'SL'),
  ('1950', 'Go Seigen is awarded 9 dan, and becomes the world\'s best player; he wins his ten-game matches against all top rivals until 1956.', 'In 1950', 'HOG+HOF'),
  ('1954', 'The Korea Baduk Association (Hankuk Kiwon) is established, on 28 January. The first NHK Cup is broadcast on radio; it moves to television in 1962.', 'January 28, 1954', 'HOG+SL'),
  ('1956', 'The first professional tournament in Korea, the Kuksu Cup, starts.', None, 'SL'),
  ('1960', 'The China–Japan Go Friendship Match starts; it is held every year until 1991.', 'Starting in 1960', 'HOG'),
  ('1962', 'Fujisawa Shūkō wins the first Meijin title tournament.', None, 'HOG+SL'),
  ('1976', 'After the "Meijin Incident" of 1974, the Tengen (1975), Kisei and Gosei (1976) titles complete the seven major Japanese titles. Fujisawa Shūkō wins the first Kisei in 1977.', 'Meijin Incident', 'HOG+SL'),
  ('1984', 'Nie Weiping leads China to victory over Japan in the first China–Japan Super Go Matches, a national triumph.', 'first China-Japan Supermatches', 'HOG+HOF'),
  ('1988', 'Takemiya Masaki wins the first Fujitsu Cup, one of the first international tournaments.', None, 'SL'),
  ('1989', 'Cho Hunhyun, the only Korean entrant, wins the first Ing Cup, the "Olympics of Go", beating Nie Weiping.', 'inaugural [[Ing Cup]]', 'HOG+HOF+SL'),
  ('1995', 'Ma Xiaochun is the first Chinese player to win an international tournament, taking both the Fujitsu Cup and the Tongyang Securities Cup.', None, 'SL'),
  ('1996', 'Lee Changho wins the first LG Cup.', None, 'SL'),
  ('1998–2003', 'The manga {i}Hikaru no Go{/i} (later also an anime) sparks a Go boom among young players in Japan.', 'Hikaru no Go', 'HOG+SL'),
  ('2000', 'Rui Naiwei, playing for Korea, wins the 43rd Kuksu in February and becomes the first woman to win a major title.', 'Rui Naiwei', 'HOG+SL'),
  ('2003', 'The Oteai promotion system is discontinued in Japan and a new one introduced.', None, 'SL'),
 ]),
 ('World no. 1 players', [
  ('January 1950', '{{Flag icon|China}}{{Flag icon|Japan}} Go Seigen becomes the world no. 1.', None, 'VID'),
  ('January 1959', '{{Flag icon|Japan}} Sakata Eio becomes the world no. 1.', None, 'VID'),
  ('January 1969', '{{Flag icon|Taiwan}}{{Flag icon|Japan}} Rin Kaiho becomes the world no. 1.', None, 'VID'),
  ('June 1975', '{{Flag icon|Japan}} Kato Masao becomes the world no. 1.', None, 'VID'),
  ('November 1979', '{{Flag icon|South Korea}}{{Flag icon|Japan}} Cho Chikun becomes the world no. 1.', None, 'VID'),
  ('July 1982', '{{Flag icon|South Korea}} Cho Hunhyun becomes the world no. 1.', None, 'VID'),
  ('October 1990', '{{Flag icon|South Korea}} Lee Changho, a student of Cho Hunhyun, becomes the world no. 1 at 15 years old.', None, 'VID+HOF'),
  ('January 2006', '{{Flag icon|China}} Gu Li becomes the world no. 1.', None, 'VID'),
  ('July 2006', '{{Flag icon|South Korea}} Lee Sedol becomes the world no. 1.', None, 'VID'),
  ('July 2011', '{{Flag icon|South Korea}} Park Junghwan becomes the world no. 1.', None, 'VID'),
  ('May 2015', '{{Flag icon|China}} Ke Jie becomes the world no. 1.', None, 'VID'),
  ('August 2017', '{{Flag icon|South Korea}} Park Junghwan becomes the world no. 1 for the second time.', None, 'VID'),
  ('May 2018', '{{Flag icon|South Korea}} Shin Jinseo, whose style resembles that of the AIs, becomes the world no. 1.', None, 'VID+HOF'),
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
  ('October 2015', 'AlphaGo, made by Google\'s DeepMind, beats the European champion Fan Hui (2p) 5–0 in even games: the first time a program beats a professional.', None, 'SL'),
  ('2016', 'DeepMind\'s AlphaGo beats Lee Sedol 4–1 in Seoul, the first time an AI beats a top professional. The same year, Iyama Yūta holds all seven Japanese major titles at once.', '4-1 victory', 'HOG+HOF+SL'),
  ('Late 2016 – early 2017', 'A stronger version of DeepMind\'s AlphaGo ("Master") wins 60 games in a row, anonymously, online against top professionals.', None, 'HOF'),
  ('May 2017', 'DeepMind\'s new and much improved AlphaGo plays Ke Jie and wins all three games; Ke Jie says its play is "like a god of Go".', None, 'HOF+SL'),
  ('2019', 'The open-source Go AI KataGo is created by David Wu.', None, 'HOF'),
  ('2019', 'Lee Sedol announces his retirement, citing AlphaGo as "an entity that cannot be defeated".', 'retirement announcement in 2019', 'HOG+HOF'),
  ('2026', 'Shin Jinseo defeats a new version of KataGo on a 2-stone handicap, coming back from a first-game defeat to win the next two.', None, 'HOF'),
 ]),
]

# First mention of each person, place, period or thing (on a timeline) is linked, and people and periods get their dates in
# parentheses: (name, Wikipedia title or an external URL, the parenthesis). The titles were checked against the wiki.
# The parenthesis is left out when the event's date already says it, or when the text has one there.
LINKS = [
    ('Emperor Yao', 'Emperor Yao', None), ('Zuo Zhuan', 'Zuo Zhuan', None), ('Analects', 'Analects', None),
    ('Confucius', 'Confucius', 'c. 551 – c. 479 BCE'), ('Mencius', 'Mencius', 'c. 371 – c. 289 BCE'), ('Ban Gu', 'Ban Gu', '32–92'),
    ('Eastern Han', 'Han dynasty', '25–220'), ('Western Han', 'Han dynasty', None),
    ('Goguryeo', 'Goguryeo', '37 BCE – 668'), ('Baekje', 'Baekje', '18 BCE – 660'), ('Silla', 'Silla', '57 BCE – 935'),
    ('Emperor Wu of Liang', 'Emperor Wu of Liang', '464–549'), ('Tang dynasty', 'Tang dynasty', '618–907'),
    ('Tibet', 'Tibet', None), ('Mongolia', 'Mongolia', None), ('Kibi no Makibi', 'Kibi no Makibi', '695–775'),
    ('Taihō Code', 'Taihō Code', None), ('Song dynasty', 'Song dynasty', '960–1279'), ('Yuan dynasty', 'Yuan dynasty', '1271–1368'),
    ('Hongwu Emperor', 'Hongwu Emperor', '1328–1398'), ('Qing dynasty', 'Qing dynasty', '1644–1912'),
    ('Oda Nobunaga', 'Oda Nobunaga', '1534–1582'), ('Kyoto', 'Kyoto', None), ('Kashio Rigen', 'https://senseis.xmp.net/?KashioRigen', '1565–?'),
    ('Toyotomi Hideyoshi', 'Toyotomi Hideyoshi', '1537–1598'), ('Tokugawa Ieyasu', 'Tokugawa Ieyasu', '1543–1616'),
    ('Tokugawa shogunate', 'Tokugawa shogunate', '1603–1868'),
    ('Honinbo Sansa', "Hon'inbō Sansa", '1559–1623'), ("Hon'inbō Sanetsu", "Hon'inbō San'etsu", '1611–1658'),
    ('Yasui Sanchi', 'Yasui Sanchi', '1617–1703'), ('Dōsaku', "Hon'inbō Dōsaku", None), ("Hon'inbō Jōwa", "Hon'inbō Jōwa", '1787–1847'),
    ('Akaboshi Intetsu', 'Akaboshi Intetsu', '1810–1835'), ('Honinbo Shusaku', "Hon'inbō Shūsaku", '1829–1862'),
    ('Gennan Inseki', 'Inoue Gennan Inseki', '1798–1859'), ('Huang Longshi', 'Huang Longshi', None),
    ('Meiji Restoration', 'Meiji Restoration', '1866–1869'), ('Hoensha', 'Hoensha', None), ('Takabe Dōhei', 'Dohei Takabe', '1881–1951'),
    ('Nihon Ki-in', 'Nihon Ki-in', None), ('Go Seigen', 'Go Seigen', '1914–2014'), ('Honinbo Shusai', "Hon'inbō Shūsai", '1874–1940'),
    ('Shūsai', "Hon'inbō Shūsai", '1874–1940'), ('Kitani Minoru', 'Minoru Kitani', '1909–1975'),
    ('The Master of Go', 'The Master of Go', None), ('Yasunari Kawabata', 'Yasunari Kawabata', '1899–1972'),
    ('Sekiyama Riichi', 'Riichi Sekiyama', '1909–1970'), ('Hiroshima', 'Hiroshima', None),
    ('Fujisawa Hōsai', 'Hosai Fujisawa', '1919–1993'), ('Oteai', 'Oteai', None), ('Korea Baduk Association', 'Korea Baduk Association', None),
    ('Korean Baduk Association', 'Korea Baduk Association', None), ('NHK Cup', 'NHK Cup (Go)', None),
    ('Fujisawa Shūkō', 'Hideyuki Fujisawa', '1925–2009'), ('Meijin', 'Meijin (Go)', None),
    ('Tengen', 'Tengen (Go)', None), ('Kisei', 'Kisei (Go)', None), ('Nie Weiping', 'Nie Weiping', '1952–2026'),
    ('Takemiya Masaki', 'Takemiya Masaki', 'born 1951'), ('Fujitsu Cup', 'Fujitsu Cup', None), ('Ing Cup', 'Ing Cup', None),
    ('Cho Hunhyun', 'Cho Hun-hyun', 'born 1953'), ('Lee Changho', 'Lee Chang-ho', 'born 1975'), ('Ma Xiaochun', 'Ma Xiaochun', 'born 1964'),
    ('LG Cup', 'LG Cup (Go)', None), ('Hikaru no Go', 'Hikaru no Go', None), ('manga', 'Manga', None), ('anime', 'Anime', None),
    ('Rui Naiwei', 'Rui Naiwei', 'born 1963'), ('Iyama Yūta', 'Yuta Iyama', 'born 1989'), ('Sakata Eio', 'Sakata Eio', '1920–2010'),
    ('Rin Kaiho', 'Rin Kaiho', 'born 1942'), ('Kato Masao', 'Kato Masao', '1947–2004'), ('Cho Chikun', 'Cho Chikun', 'born 1956'),
    ('Gu Li', 'Gu Li (Go player)', 'born 1983'), ('Lee Sedol', 'Lee Sedol', 'born 1983'), ('Park Junghwan', 'Park Junghwan', 'born 1993'),
    ('Ke Jie', 'Ke Jie', 'born 1997'), ('Shin Jinseo', 'Shin Jin-seo', 'born 2000'), ('Fan Hui', 'Fan Hui', 'born 1981'),
    ('Michael Redmond', 'Michael Redmond (Go player)', 'born 1963'), ('Albert Zobrist', 'Albert Lindsey Zobrist', 'born 1942'),
    ('Manfred Wimmer', 'Manfred Wimmer', '1944–1995'), ('Daniel Barry', 'Daniel T. Barry', 'born 1953'),
    ('Koichi Wakata', 'Koichi Wakata', 'born 1963'), ('Matteo Ricci', 'Matteo Ricci', '1552–1610'),
    ('Nicolas Trigault', 'Nicolas Trigault', '1577–1628'), ('Augsburg', 'Augsburg', None), ('Jesuit', 'Jesuits', None),
    ('Thomas Hyde', 'Thomas Hyde', '1636–1703'), ('Leibniz', 'Gottfried Wilhelm Leibniz', '1646–1716'),
    ('Kido Takayoshi', 'Kido Takayoshi', '1833–1877'), ('Ōkubo Toshimichi', 'Ōkubo Toshimichi', '1830–1878'),
    ('Iwakura Mission', 'Iwakura Mission', '1871–1873'), ('Oskar Korschelt', 'Oskar Korschelt', '1853–1940'),
    ('Edward Lasker', 'Edward Lasker', '1885–1981'), ('American Go Association', 'American Go Association', None),
    ('European Go Federation', 'European Go Federation', None), ('Kansai Ki-in', 'Kansai Ki-in', None),
    ('Acornsoft', 'Acornsoft', None), ('BBC Micro', 'BBC Micro', None), ('Internet Go Server', 'Internet Go server', None),
    ('teletype', 'Teleprinter', None), ('tsumego', 'Tsumego', None), ('komi', 'Komi (Go)', None),
    ('Monte Carlo tree search', 'Monte Carlo tree search', None), ('Monte Carlo', 'Monte Carlo method', None),
    ('CrazyStone', 'Crazy Stone (software)', None), ('Computer Olympiad', 'Computer Olympiad', None), ('Zen', 'Zen (software)', None),
    ('DeepMind', 'Google DeepMind', None), ('Google', 'Google', None), ('AlphaGo', 'AlphaGo', None), ('KataGo', 'KataGo', None),
]

def link(text, seen, date=''):
    """Link each LINKS entry in the event (once per event) and add its dates the first time on a timeline (`seen`)."""
    toks = []
    here = set()
    def put(piece):
        toks.append(piece)
        return '\x02%d\x03' % (len(toks) - 1)
    text = re.sub(r'\[\[[^\]]*\]\]|\{\{[^{}]*\}\}', lambda m: put(m.group(0)), text)      # what is already a link or a template
    for name, target, paren in LINKS:
        if target in here:
            continue
        m = re.search(r'(?<![\w\x02\x03])' + re.escape(name) + r'(?![\w\x02\x03])', text)
        if not m:
            continue
        here.add(target)
        first = target not in seen
        seen.add(target)
        shown = name
        if target.startswith('http'):
            piece = '[%s %s]' % (target, shown)
        else:
            piece = '[[%s]]' % shown if target == shown else '[[%s|%s]]' % (target, shown)
        after = text[m.end():m.end() + 2]
        if first and paren and paren not in date and not after.startswith((' (', '(')):
            piece += ' (%s)' % paren
        text = text[:m.start()] + put(piece) + text[m.end():]
    return re.sub('\x02(\\d+)\x03', lambda m: toks[int(m.group(1))], text)

# Names that only occur in picture captions
CAP_EXTRA = [("Hon'inbō Sansa", "Hon'inbō Sansa"), ("Hon'inbō Dōsaku", "Hon'inbō Dōsaku"), ("Hon'inbō Shūsai", "Hon'inbō Shūsai"),
             ("Hon'inbō Shūsaku", "Hon'inbō Shūsaku"), ('Emperor Meiji', 'Emperor Meiji'), ('British Library', 'British Library'),
             ('Nagasaki', 'Nagasaki'), ('Rubens', 'Peter Paul Rubens'), ('Ryōgen-in', 'Ryōgen-in'), ('Han dynasty', 'Han dynasty'),
             ('Inner Mongolia Museum', 'Inner Mongolia Museum')]

def cap_link(caption):
    """A caption links the people and things it names (each once), without dates."""
    toks, seen = [], set()
    entries = sorted([(n, t) for n, t, _ in LINKS if not t.startswith('http')] + CAP_EXTRA, key=lambda e: -len(e[0]))
    for name, target in entries:
        if target in seen:
            continue
        m = re.search(r'(?<![\w\x02\x03])' + re.escape(name) + r'(?![\w\x02\x03])', caption)
        if not m:
            continue
        seen.add(target)
        piece = '[[%s]]' % name if target == name else '[[%s|%s]]' % (target, name)
        toks.append(piece)
        caption = caption[:m.start()] + '\x02%d\x03' % (len(toks) - 1) + caption[m.end():]
    return re.sub('\x02(\\d+)\x03', lambda m: toks[int(m.group(1))], caption)

# Pictures on Wikimedia Commons: (date, a part of the event's text, file, caption). An event with several pictures shows
# them all, in the order given here, in one row that wraps.
IMAGES = [
    ('c. 2356–2255 BCE', 'Yao', 'EmperorYao.jpg', 'Emperor Yao'),
    ('548 BCE', 'Zuo', 'Li Yuanyang Zuo zhuan first page.png', 'First page of an edition of the Zuo Zhuan'),
    ('3rd century BCE', 'Mencius', 'Half Portraits of the Great Sage and Virtuous Men of Old - Meng Ke (孟軻).jpg', 'Mencius'),
    ('1st–3rd century', 'Ban Gu', 'Go Board Han dynasty.JPG', 'A Han dynasty Go board'),
    ('3rd–6th century', 'Dunhuang', 'British Library Dunhuang Go Manual.jpg', 'The Dunhuang Go Manual, British Library'),
    ('475', 'To-lim', 'Baekje Game of Baduk (Copy) (30079340202).jpg', 'A copy of a Baekje game of baduk'),
    ('Around 500', 'Wu of Liang', 'Liang Wudi.jpg', 'Emperor Wu of Liang'),
    ('618–907', 'Tang', 'Early Go stones.jpeg', 'Early Go stones'),
    ('Early 8th century', 'Tibet', 'TibetGoBoard.png', 'A Tibetan Go board'),
    ('8th century', 'Kibi', 'Kibino Makibi.jpg', 'Kibi no Makibi'),
    ('1349', 'Xuanxuan', 'Inner Mongolia Museum weiqi stones.jpg', 'Weiqi stones, Inner Mongolia Museum'),
    ('Ming dynasty', 'Hongwu', 'Go Ming Court.jpg', 'Go at the Ming court'),
    ('1582', 'Nobunaga', 'Odanobunaga.jpg', 'Oda Nobunaga'),
    ('1582', 'Sansa', 'Sansa.jpg', "Hon'inbō Sansa"),
    ('1588', 'Hideyoshi', 'Go board Hideyoshi Ieyasu Ryogenin M1868.jpg', 'The Go board of Hideyoshi and Ieyasu, Ryōgen-in'),
    ('1588', 'Hideyoshi', 'Toyotomi_Hideyoshi_c1598_Kodai-ji_Temple.png', 'Toyotomi Hideyoshi'),
    ('1603', 'Sansa', 'Sansa.jpg', "Hon'inbō Sansa"),
    ('1603', 'Ieyasu', 'Tokugawa Ieyasu2.JPG', 'Tokugawa Ieyasu'),
    ('1612', 'Tokugawa', 'Tokugawa Ieyasu2.JPG', 'Tokugawa Ieyasu, founder of the Tokugawa shogunate'),
    ('1615', 'Trigault', 'Portrait of Nicolas Trigault by Peter Paul Rubens.png', 'Nicolas Trigault, by Rubens'),
    ('1615', 'Ricci', '利玛窦像，游文辉绘.jpg', 'Matteo Ricci'),
    ('1694', 'Thomas Hyde', 'Thomas-Hyde.jpg', 'Thomas Hyde'),
    ('17th–18th century', 'Leibniz', 'Christoph Bernhard Francke - Bildnis des Philosophen Leibniz (ca. 1695).jpg', 'Gottfried Wilhelm Leibniz'),
    ('Late 17th century', 'Dōsaku', 'Honinbo Dosaku.png', "Hon'inbō Dōsaku"),
    ('1713', 'Hatsuyoron', 'Hatsuyoron - problem 76.png', 'Problem 76 of the Igo Hatsuyoron'),
    ('1846', 'ear-reddening', 'Kulak_kizartan_go.png', 'The "ear-reddening" game'),
    ('1846', 'Shusaku', 'Honinbo_Shusaku.jpg', "Hon'inbō Shūsaku"),
    ('1868', 'Meiji', 'Emperor Meiji by Takahashi Yuichi.jpg', 'Emperor Meiji'),
    ('1872', 'Kido', 'Takayoshi_Kido_suit.jpg', 'Kido Takayoshi'),
    ('1872', 'Ōkubo', 'Ōkubo_Toshimichi_1872_(cropped).jpg', 'Ōkubo Toshimichi'),
    ('1872', 'Iwakura', 'Iwakura mission.jpg', 'Members of the Iwakura Mission'),
    ('1880', 'Korschelt', 'Oscar Korschelt.jpg', 'Oskar Korschelt'),
    ('1905–1908', 'Lasker', 'Edward Lasker.jpg', 'Edward Lasker'),
    ('1924', 'Nihon Ki-in', 'Nihon Ki-in Headquarter (2016-05-05) 5.jpg', 'The Nihon Ki-in headquarters'),
    ('1933', 'Game of the Century', 'Game_of_the_Century_-_Honinbo_Shusai_(W)_vs_Go_Seigen_(B)_no_text.svg', 'The "Game of the Century": Shūsai (white) against Go Seigen (black)'),
    ('1933', 'Go Seigen', 'Go_Seigen_01.jpg', 'Go Seigen'),
    ('1933', 'Honinbo Shusai', 'Honinbo Shusai.jpg', "Hon'inbō Shūsai"),
    ('1936–1938', 'Shūsai', 'Honinbo Shusai.jpg', "Hon'inbō Shūsai"),
    ('1936–1938', 'Kitani', 'Kitani_Minoru_1955.jpg', 'Kitani Minoru'),
    ('1936–1938', 'Kawabata', 'Yasunari_Kawabata_1938.jpg', 'Yasunari Kawabata'),
    ('1945', 'Atomic', 'Atomic bombing of Japan.jpg', 'The atomic bombings of Hiroshima (left) and Nagasaki (right)'),
    ('1950', 'Go Seigen', 'Go_Seigen_and_Kitani_Minoru.jpg', 'Go Seigen and Kitani Minoru'),
    ('1984', 'Nie Weiping', 'Nie Weiping 2023.jpg', 'Nie Weiping'),
    ('1984', 'Acornsoft', 'BBC Micro Front Restored.jpg', 'A BBC Micro'),
    ('1988', 'Takemiya', 'Takemiya Masaki.jpg', 'Takemiya Masaki'),
    ('1989', 'Cho Hunhyun', 'Chohunhyun1.jpg', 'Cho Hunhyun'),
    ('1989', 'Nie Weiping', 'Nie Weiping 2023.jpg', 'Nie Weiping'),
    ('1996', 'Barry', 'Daniel Thomas Barry.jpg', 'Daniel Barry'),
    ('1996', 'Wakata', 'Koichi_Wakata_Official_Portrait_(cropped)_2.jpg', 'Koichi Wakata'),
    ('2000', 'Rui Naiwei', '圍棋九段選手芮迺偉女士 (cropped).jpg', 'Rui Naiwei'),
    ('2000', 'Redmond', 'Michael Redmond in 2018.png', 'Michael Redmond in 2018'),
    ('2012', 'Takemiya', 'Takemiya Masaki.jpg', 'Takemiya Masaki'),
    ('October 2015', 'AlphaGo', 'AlphaGo_computer_rack.jpg', 'An AlphaGo computer rack'),
    ('October 2015', 'AlphaGo', 'Alphago logo Reversed.svg', 'Logo of AlphaGo'),
    ('October 2015', 'DeepMind', 'DeepMind logo.png', 'Logo of DeepMind'),
    ('October 2015', 'Fan Hui', 'FanHui.jpg', 'Fan Hui'),
    ('Late 2016 – early 2017', 'AlphaGo', 'Alphago logo Reversed.svg', 'Logo of AlphaGo'),
    ('2016', 'Lee Sedol', 'LG전자, 이세돌 9단과 함께 학생들의 꿈 그린다.jpg', 'Lee Sedol in 2016'),
    ('2016', 'Iyama', '20180213eiyo07 Yuta Iyama.jpg', 'Iyama Yūta'),
    ('May 2017', 'Ke Jie', 'Ke Jie (柯洁) 2019 (cropped).png', 'Ke Jie'),
    ('May 2017', 'AlphaGo', 'Alphago logo Reversed.svg', 'Logo of AlphaGo'),
    ('2019', 'KataGo', 'KataGoanalisis.png', "A game analysed with KataGo"),
    ('2019', 'Lee Sedol', 'Lee Se-Dol - 2016 (cropped).jpg', 'Lee Sedol'),
    ('January 1950', 'Go Seigen', 'Go_Seigen_01.jpg', 'Go Seigen'),
    ('January 1959', 'Sakata', 'Sakata-Eio-1.jpg', 'Sakata Eio'),
    ('January 1969', 'Rin Kaiho', 'Go Seigen teaching to a young Rin Kaiho.jpg', 'Go Seigen teaching a young Rin Kaiho'),
    ('November 1979', 'Cho Chikun', 'Cho Chikun at World Go Festival20190630.jpg', 'Cho Chikun'),
    ('July 1982', 'Cho Hunhyun', 'Chohunhyun1.jpg', 'Cho Hunhyun'),
    ('October 1990', 'Lee Changho', 'Lee ChangHo.JPG', 'Lee Changho'),
    ('January 2006', 'Gu Li', 'Gu Li 2024.jpg', 'Gu Li'),
    ('July 2006', 'Lee Sedol', 'Lee Se-Dol - 2016 (cropped).jpg', 'Lee Sedol'),
    ('July 2011', 'Park Junghwan', '(청주MBC뉴스) 청남대 바둑전쟁 박정환 9단 웃다.jpg', 'Park Junghwan'),
    ('May 2015', 'Ke Jie', 'Ke Jie (柯洁) 2019 (cropped).png', 'Ke Jie'),
]
for _d, _t, _f, _c in IMAGES:       # a typo here would silently drop a picture
    assert any(d == _d and _t in t for _, evs in SECTIONS for d, t, *_ in evs), (_d, _t)

# Which country's solo timeline an event belongs to: (date, part of the text, letters C = China, K = Korea, J = Japan)
TAGS = [
 ('Unknown', 'Rotten', 'C'), ('c. 2356–2255 BCE', 'Yao', 'C'), ('548 BCE', 'Zuo', 'C'), ('3rd century BCE', 'Yi Qiu', 'C'),
 ('206 BCE – 24 CE', 'Han', 'C'), ('1st–3rd century', 'Ban Gu', 'C'), ('c. 250', 'Wu Diagrams', 'C'),
 ('3rd–6th century', 'Dunhuang', 'C'), ('475', 'To-lim', 'K'), ('Around 500', 'Wu of Liang', 'C'),
 ('Early 7th century', 'Japanese', 'J'), ('618–907', 'Tang', 'C'), ('Early 8th century', 'Tibet', 'C'),
 ('8th century', 'Kibi', 'J'), ('737', 'Yang Jiying', 'CK'), ('c. 1050', 'Classic of Go', 'C'), ('c. 1100', 'Wangyou', 'C'),
 ('1349', 'Xuanxuan', 'C'), ('Ming dynasty', 'Hongwu', 'C'), ('1582', 'Sansa', 'J'), ('1588', 'Hideyoshi', 'J'),
 ('1603', 'Sansa', 'J'), ('1612', 'Tokugawa', 'J'), ('1626–1628', 'castle', 'J'), ('1645–1653', 'Sanetsu', 'J'),
 ('c. 1650', 'Huang Longshi', 'C'), ('Late 17th century', 'Dōsaku', 'J'), ('1713', 'Hatsuyoron', 'J'),
 ('1739', 'Danghu', 'C'), ('1840', 'blood', 'J'), ('1846', 'ear-reddening', 'J'), ('1863', 'castle', 'J'),
 ('1868', 'Meiji', 'J'), ('1878', 'newspaper', 'J'), ('1909–1910', 'Takabe', 'JC'), ('1924', 'Nihon Ki-in', 'J'),
 ('1933', 'Game of the Century', 'J'), ('1935', 'radio', 'J'), ('1936–1938', 'Shūsai', 'J'), ('1941', 'Sekiyama', 'J'),
 ('1945', 'Atomic', 'J'), ('1949', 'Fujisawa', 'J'), ('1950', 'Go Seigen is awarded', 'JC'),
 ('1954', 'Korea Baduk', 'KJ'), ('1956', 'Kuksu', 'K'), ('1960', 'Friendship', 'CJ'), ('1962', 'Meijin', 'J'),
 ('1976', 'Tengen', 'J'), ('1984', 'Nie Weiping', 'CJ'), ('1988', 'Fujitsu', 'J'), ('1989', 'Ing Cup', 'KC'),
 ('1995', 'Ma Xiaochun', 'C'), ('1996', 'LG Cup', 'K'), ('1998–2003', 'Hikaru', 'J'), ('2000', 'Rui Naiwei', 'KC'),
 ('2003', 'Oteai', 'J'), ('1615', 'Ricci', 'C'), ('1872', 'Kido', 'J'), ('1880', 'Korschelt', 'J'),
 ('1978', 'Wimmer', 'J'), ('1996', 'Wakata', 'J'), ('2000', 'Redmond', 'J'), ('2011–2014', 'Korean', 'K'),
 ('2016', 'Lee Sedol 4', 'KJ'), ('May 2017', 'Ke Jie', 'C'), ('2019', 'Lee Sedol announces', 'K'), ('2026', 'Shin Jinseo defeats', 'K'),
 ('January 1950', 'Go Seigen', 'CJ'), ('January 1959', 'Sakata', 'J'), ('January 1969', 'Rin', 'J'), ('June 1975', 'Kato', 'J'),
 ('November 1979', 'Cho Chikun', 'KJ'), ('July 1982', 'Cho Hunhyun', 'K'), ('October 1990', 'Lee Changho', 'K'),
 ('January 2006', 'Gu Li', 'C'), ('July 2006', 'Lee Sedol', 'K'), ('July 2011', 'Park', 'K'), ('May 2015', 'Ke Jie', 'C'),
 ('May 2018', 'Shin', 'K'), ('August 2017', 'Park', 'K'),
 ('October 2015', 'AlphaGo', 'P'), ('2016', 'Lee Sedol 4', 'P'), ('Late 2016 – early 2017', 'Master', 'PI'), ('May 2017', 'Ke Jie', 'P'),
 ('2019', 'KataGo', 'P'), ('2026', 'Shin Jinseo defeats', 'P'), ('19 December 1976', 'teletype', 'I'), ('1984', 'inetgo', 'I'),
 ('2 February 1992', 'Internet Go Server', 'I'),
]
EVENTS = [(t, d, tx, ph, sr) for t, evs in SECTIONS for d, tx, ph, sr in evs]
tag_of = {}
for d, frag, letters in TAGS:
    hits = [i for i, (t, dd, tx, ph, sr) in enumerate(EVENTS) if dd == d and frag in tx]
    if len(hits) != 1:
        print('TAG', d, frag, 'matches', len(hits))
        continue
    tag_of.setdefault(hits[0], '')
    tag_of[hits[0]] += letters

AUTO = {'Go in the West and in space': 'W', 'Go online and computer Go': 'P', 'The AI era': 'A', 'World no. 1 players': 'N'}      # whole sections
for i, ev in enumerate(EVENTS):
    if ev[0] in AUTO:
        tag_of[i] = tag_of.get(i, '') + AUTO[ev[0]]

def outline(select, pictures, headings=True, order=None):
    """Outline lines of the selected events (indices), grouped by section."""
    lines, last, mine = [], None, set()
    local = set()
    for i in (order if order is not None else range(len(EVENTS))):
        title, date, text, phrase, src = EVENTS[i]
        if not select(i):
            continue
        if title != last:
            if headings:
                lines.append('== %s ==' % title)
            last = title
        raw = text
        text = link(text.replace('{i}', "''").replace('{/i}', "''"), local, date)
        refs = ref_text(phrase) if phrase and 'HOG' in src else ''
        if 'SL' in src:
            refs += ref_text(None, named=':11')
        if 'VID' in src:
            refs += VIDEO + GORATINGS
        if pictures and (pictures != 'vid' or 'VID' in src):      # 'vid': only the world no. 1 events have their picture
            shown = [(f, c) for d, t, f, c in IMAGES if d == date and t in raw]
            for k, (f, c) in enumerate(shown):
                if (f, c) in shown[:k]:
                    continue
                lines.append('[[File:%s|%s|%s]]' % (f, '200px', cap_link(c)))
        lines.append("* '''%s''' %s%s" % (date, text, refs))
    return lines

n = len(EVENTS)
def year_key(date):
    """Rough year of a date label, to place the events of the West / online / computer / AI sections among the eras."""
    d = date
    m = re.search(r'(\d+)(?:st|nd|rd|th)', d)
    if 'century' in d and m:
        c = (int(m.group(1)) - 1) * 100 + 50
        c += -40 if d.startswith('Early') else 30 if d.startswith('Late') else 0
        return -c if 'BCE' in d else c
    if 'Unknown' in d: return -9999
    if 'Ming' in d: return 1368
    m = re.search(r'\b(\d{3,4})\b', d)
    mo = next((k for k, name in enumerate(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']) if name in d), 0)
    return (-1 if 'BCE' in d else 1) * int(m.group(1)) + mo / 13 if m else 0

SPLICED = ('Go in the West and in space', 'Go online and computer Go', 'The AI era', 'World no. 1 players')
ERAS = [t for t, _ in SECTIONS if t not in SPLICED]
eras = {t: [i for i, e in enumerate(EVENTS) if e[0] == t] for t in ERAS}
eras['The AI era'] = []
extra = sorted((i for i, e in enumerate(EVENTS) if e[0] in SPLICED), key=lambda i: year_key(EVENTS[i][1]))
def era_of(i):
    y = year_key(EVENTS[i][1])
    return 'The AI era' if y >= 2015.6 else ERAS[2] if y < 1868 else ERAS[3]          # Edo-period / Modern professional Go / AI era
for i in extra:                                       # splice by year: before the first event of the era that is later
    lst = eras[era_of(i)]
    pos = next((j for j, o in enumerate(lst) if year_key(EVENTS[o][1]) > year_key(EVENTS[i][1])), len(lst))
    lst.insert(pos, i)
# the main timeline: one timeline whose sections (TimelineRail sections, not wiki headings) are the eras
ls = []
for title in ERAS + ['The AI era']:
    ls.append('== %s ==' % title)
    ls += outline(lambda i: True, 'main', headings=False, order=eras[title])
body = '\n' + invoke(MODULE, 'go', '\n'.join(ls), flags=['--switcher', '--no-original']) + '\n'
solo = ''
TITLES = {'C': 'Go in China', 'K': 'Go in Korea', 'J': 'Go in Japan', 'W': 'Go in non-Asian countries', 'I': 'Internet Go', 'P': 'Computer Go', 'A': 'The AI era', 'N': 'World no. 1 players'}
for code, name in (('N', 'world no. 1 players'), ('C', 'China'), ('K', 'Korea'), ('J', 'Japan'), ('W', 'non-Asian countries'), ('I', 'internet Go'), ('P', 'computer Go'), ('A', 'the AI era')):
    pick = lambda i, c=code: c in tag_of.get(i, '')
    pics = True if code == 'N' else 'vid' if code in 'CKJ' else False
    if code in 'CKJ':
        # a country: the eras of the main timeline (the World no. 1 players and the later events are spliced into them by date)
        ls = []
        for title in ERAS:
            idx = [i for i in eras[title] if pick(i)] + ([i for i in eras['The AI era'] if pick(i)] if title == ERAS[-1] else [])
            if idx:
                ls.append('== %s ==' % title)
                ls += outline(pick, pics, headings=False, order=idx)
    else:
        # a subject: one flat chronology, the heading of the page names it
        ls = outline(pick, pics, headings=False, order=[i for t in ERAS + ['The AI era'] for i in eras[t]])
    cnt = sum(1 for l in ls if l.startswith('*'))
    print(name, cnt, 'events')
    call = invoke(MODULE, 'go' + code.lower(), '\n'.join(ls), flags=['--switcher', '--no-original'])
    # the eras inside a solo timeline are not headings of the page (they would repeat the main timeline's in the table of contents)
    if code == 'N':       # the list of world no. 1 players is not finished: the rail goes on after the last dot
        call = call.replace('\n|id=gon\n', '\n|id=gon |open=yes\n', 1)
    note = ("The data on who became the world no. 1, and when, comes from [https://www.goratings.org/en/ Go Ratings]." + GORATINGS + "\n\n") if code == 'N' else ''
    solo += '\n\n== %s ==\n%s%s' % (TITLES[code], note, call.replace('\n|id=go%s\n' % code.lower(), '\n|id=go%s |toc=no\n' % code.lower(), 1))

# Sensei's Library: its own timeline (section 7 of its Go History page, facts in new words) and the list of timelines elsewhere (section 8)
SL_EVENTS = [
 ('21 October 2000', 'Two enthusiasts, Arno and Morten, start a [[wiki]] meant as an online repository of all Go knowledge: [[Sensei\'s Library]].'),
 ('5 January 2001', 'Sensei\'s Library opens to the public, announced on the Usenet group rec.games.go.'),
 ('11 January 2004', 'A French version, EncyGoPédie, is released.'),
 ('11 November 2004', 'The 10,000th page is added.'),
 ('3 November 2007', 'The first full-board (19×19) position search.'),
 ('22 April 2009', 'A customised board search is added.'),
 ('28 May 2010', 'The 20,000th page is created, by Dave Sigaty.'),
]
sl_lines = ["* \'\'\'%s\'\'\' %s%s" % (d, t, ref_text(None, named=':11')) for d, t in SL_EVENTS]
solo += '\n\n== Sensei\'s Library ==\n' + invoke(MODULE, 'gosl', '\n'.join(sl_lines), flags=['--switcher', '--no-original'])
ELSEWHERE = (
 '\n== Timelines elsewhere ==\n'
 '* Milton N. Bradley, [http://users.eniinternet.com/bradleym/America.html "How Go came to America"]\n'
 '* Jan van der Steen\'s [http://gobase.org/history/ history pages] on GoBase\n'
 '* Extensive timelines are included on the GoGoD CD (Go Game Database)\n'
 '* [https://senseis.xmp.net/?HistoryOfGoInFrance19652007 "History of Go in France 1965–2007"] at Sensei\'s Library\n'
 '* The book \'\'Eurogo\'\'\n'
)

sources = re.search(r'^== ?Sources ?==\n(.*?)(?=^==)', hog, re.S | re.M)
sources = sources.group(1).strip() if sources else ''
lead = ("This is a timeline of the history of the board game [[Go (game)|Go]] (Chinese ''weiqi'', Korean ''baduk''), "
        "from its legendary origins in ancient China to the age of AI. For the full story, see [[History of Go]].")
page = (
    '<!-- Draft of a "Timeline of Go" with [[Module:TimelineRail]]. The events and their sources are adapted from [[History of Go]] '
    '(see its history for attribution), the Go | Hall of Fame timeline (go-hall-of-fame.vercel.app) and, as facts put in new words, '
    'the Go History page of Sensei\'s Library (senseis.xmp.net/?GoHistory). -->\n'
    '{{Short description|Chronology of the board game Go}}\n'
    '{{Use dmy dates|date=November 2026}}\n\n'
    + "[[File:MET DP135836.jpg|thumb|right|upright=1.3|''Outfit for the Go Game'', woodblock print (''surimono''), 19th century, [[Metropolitan Museum of Art]].]]\n"
    + lead + '\n{{clear}}\n\n__TOC__\n\n== Timeline ==' + body + solo +
    '\n\n== See also ==\n* [[History of Go]]\n* [[Go (game)]]\n* [[Timeline of artificial intelligence]]\n'
    '\n== References ==\n'
    '{{Reflist|30em}}\n\n== Sources ==\n' + sources + '\n'
    + ELSEWHERE + '\n[[Category:History of Go|Timeline]]\n'
)
out.parent.mkdir(exist_ok=True)
page = dedupe(page)
out.write_text(page)
print('%d events -> %s (%d bytes)' % (n, out, len(page)))
