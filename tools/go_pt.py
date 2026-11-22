"""Portuguese (Brazil) text for tools/convert_go.py --lang=pt.

TEXTS has one entry per event of SECTIONS, in the same order. Names of people are the same in both languages; the words
that differ (periods, places, titles) are in NAMES, which turns the link list of the English version into the Portuguese one.
Links go to the Portuguese article when the English one has a language link to it (tools/pt_titles.json), else to the
English article ([[:en:...]]).
"""
import json, pathlib, re

here = pathlib.Path(__file__).resolve().parent
PT_TITLES = json.loads((here / 'pt_titles.json').read_text())

# ------------------------------------------------------------------ dates
MONTHS = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
EN_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
ROMAN = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII',
         13: 'XIII', 14: 'XIV', 15: 'XV', 16: 'XVI', 17: 'XVII', 18: 'XVIII', 19: 'XIX', 20: 'XX'}

def pt_date(d):
    if d == 'Unknown': return 'Desconhecido'
    if d == 'Ming dynasty': return 'Dinastia Ming'
    if d == 'Around 500': return 'Por volta de 500'
    if d == 'Late 2016 – early 2017': return 'Final de 2016 – início de 2017'
    if 'century' in d:
        nums = [int(x) for x in re.findall(r'(\d+)(?:st|nd|rd|th)', d)]
        rom = '–'.join(ROMAN[n] for n in nums)
        bce = ' a.C.' if 'BCE' in d else ''
        pre = 'início do ' if d.startswith('Early') else 'final do ' if d.startswith('Late') else ''
        word = 'séculos' if len(nums) > 1 else 'século'
        if pre:
            return pre + word + ' ' + rom + bce
        return word.capitalize() if False else word + ' ' + rom + bce
    d = d.replace(' BCE', ' a.C.').replace(' CE', ' d.C.')
    m = re.match(r'^(\d+) (\w+) (\d{4})$', d)
    if m and m.group(2) in EN_MONTHS:
        return '%s de %s de %s' % (m.group(1), MONTHS[EN_MONTHS.index(m.group(2))], m.group(3))
    m = re.match(r'^(\w+) (\d{4})$', d)
    if m and m.group(1) in EN_MONTHS:
        return '%s de %s' % (MONTHS[EN_MONTHS.index(m.group(1))], m.group(2))
    return d

def pt_paren(p):
    if p is None: return None
    p = p.replace(' BCE', ' a.C.')
    if p.startswith('born '): p = 'n. ' + p[5:]
    return p

# ------------------------------------------------------------------ words
# English name in the link list -> the Portuguese words (several = several spellings in the text)
NAMES = {
    'Emperor Yao': ['imperador Yao'], 'Analects': ['Analectos'], 'Confucius': ['Confúcio'], 'Mencius': ['Mêncio'],
    'Eastern Han': ['Han Oriental'], 'Western Han': ['Han Ocidental'], 'Emperor Wu of Liang': ['imperador Wu de Liang'],
    'Tang dynasty': ['Dinastia Tang', 'dinastia Tang'], 'Tibet': ['Tibete'], 'Mongolia': ['Mongólia'], 'Taihō Code': ['Código Taihō'],
    'Song dynasty': ['Dinastia Song', 'dinastia Song'], 'Yuan dynasty': ['Dinastia Yuan', 'dinastia Yuan'],
    'Hongwu Emperor': ['imperador Hongwu'], 'Qing dynasty': ['dinastia Qing', 'Dinastia Qing'], 'Kyoto': ['Quioto'],
    'Tokugawa shogunate': ['xogunato Tokugawa'], 'Meiji Restoration': ['Restauração Meiji'], 'Iwakura Mission': ['Missão Iwakura'],
    'Seoul': ['Seul'], 'Berlin': ['Berlim'], 'New York': ['Nova Iorque'], 'Augsburg': ['Augsburgo'], 'Jesuit': ['jesuíta'],
    'teletype': ['teletipo'], 'The Master of Go': ['O Mestre de Go'], 'Korea Baduk Association': ['Associação Coreana de Baduk'],
    'Korean Baduk Association': ['Associação Coreana de Baduk'], 'Ing Cup': ['Copa Ing'], 'Fujitsu Cup': ['Copa Fujitsu'],
    'LG Cup': ['Copa LG'], 'NHK Cup': ['NHK Cup'], 'American Go Association': ['Associação Americana de Go'],
    'European Go Federation': ['Federação Europeia de Go'], 'Monte Carlo tree search': ['busca em árvore Monte Carlo'],
    'Computer Olympiad': ['Olimpíada de Computadores'],
}
TITLE_OVERRIDE = {                      # Portuguese titles the language links do not give
    'Emperor Yao': 'Yao (imperador)', 'Kyoto': 'Quioto', 'Han dynasty': 'Dinastia Han',
}

def target(t):
    """The link target for an English title: the Portuguese article if there is one, else the English one."""
    if t.startswith('http'):
        return t
    pt = TITLE_OVERRIDE.get(t) or PT_TITLES.get(t)
    return pt if pt else ':en:' + t

def localize_links(links):
    out = []
    for name, tgt, paren in links:
        for nm in NAMES.get(name, [name]):
            out.append((nm, tgt, pt_paren(paren)))
    return out

CAP_EXTRA = [("Hon'inbō Sansa", "Hon'inbō Sansa"), ("Hon'inbō Dōsaku", "Hon'inbō Dōsaku"), ("Hon'inbō Shūsai", "Hon'inbō Shūsai"),
             ("Hon'inbō Shūsaku", "Hon'inbō Shūsaku"), ('imperador Meiji', 'Emperor Meiji'), ('Biblioteca Britânica', 'British Library'),
             ('Nagasaki', 'Nagasaki'), ('Rubens', 'Peter Paul Rubens'), ('Ryōgen-in', 'Ryōgen-in'), ('dinastia Han', 'Han dynasty'),
             ('Museu da Mongólia Interior', 'Inner Mongolia Museum')]

SECTION_PT = {
    'Legends and first records': 'Lendas e primeiros registros', 'Ancient and medieval East Asia': 'Leste Asiático antigo e medieval',
    'Edo-period Japan and Qing China': 'Japão do período Edo e China Qing', 'Modern professional Go': 'Go profissional moderno',
    'World no. 1 players': 'Jogadores número 1 do mundo', 'Go in the West and in space': 'Go no Ocidente e no espaço',
    'Go online and computer Go': 'Go online e Go de computador', 'The AI era': 'A era da IA',
}
TITLES = {'C': 'Go na China', 'K': 'Go na Coreia', 'J': 'Go no Japão', 'W': 'Go em países não asiáticos', 'I': 'Go na internet',
          'P': 'Go de computador', 'A': 'A era da IA', 'N': 'Jogadores número 1 do mundo'}
LABELS = ('Linha do tempo', 'Lista', 'Tabela')

CAPTIONS = {
    'Emperor Yao': 'Imperador Yao', 'First page of an edition of the Zuo Zhuan': 'Primeira página de uma edição do Zuo Zhuan',
    'Mencius': 'Mêncio', 'A Han dynasty Go board': 'Um tabuleiro de Go da dinastia Han',
    'The Dunhuang Go Manual, British Library': 'O Manual de Go de Dunhuang, Biblioteca Britânica',
    'A copy of a Baekje game of baduk': 'Cópia de um jogo de baduk de Baekje', 'Emperor Wu of Liang': 'Imperador Wu de Liang',
    'Early Go stones': 'Pedras de Go antigas', 'A Tibetan Go board': 'Um tabuleiro de Go tibetano', 'Kibi no Makibi': 'Kibi no Makibi',
    'Weiqi stones, Inner Mongolia Museum': 'Pedras de weiqi, Museu da Mongólia Interior', 'Go at the Ming court': 'Go na corte Ming',
    'Oda Nobunaga': 'Oda Nobunaga', "Hon'inbō Sansa": "Hon'inbō Sansa",
    'The Go board of Hideyoshi and Ieyasu, Ryōgen-in': 'O tabuleiro de Go de Hideyoshi e Ieyasu, Ryōgen-in',
    'Toyotomi Hideyoshi': 'Toyotomi Hideyoshi', 'Tokugawa Ieyasu': 'Tokugawa Ieyasu',
    'Tokugawa Ieyasu, founder of the Tokugawa shogunate': 'Tokugawa Ieyasu, fundador do xogunato Tokugawa',
    'Nicolas Trigault, by Rubens': 'Nicolas Trigault, por Rubens', 'Matteo Ricci': 'Matteo Ricci', 'Thomas Hyde': 'Thomas Hyde',
    'Gottfried Wilhelm Leibniz': 'Gottfried Wilhelm Leibniz', "Hon'inbō Dōsaku": "Hon'inbō Dōsaku",
    'Problem 76 of the Igo Hatsuyoron': 'Problema 76 do Igo Hatsuyoron', 'The "ear-reddening" game': 'O jogo das "orelhas vermelhas"',
    "Hon'inbō Shūsaku": "Hon'inbō Shūsaku", 'Emperor Meiji': 'Imperador Meiji', 'Kido Takayoshi': 'Kido Takayoshi',
    'Ōkubo Toshimichi': 'Ōkubo Toshimichi', 'Members of the Iwakura Mission': 'Membros da Missão Iwakura',
    'Oskar Korschelt': 'Oskar Korschelt', 'Edward Lasker': 'Edward Lasker', 'The Nihon Ki-in headquarters': 'A sede da Nihon Ki-in',
    'The "Game of the Century": Shūsai (white) against Go Seigen (black)': 'O "Jogo do Século": Shūsai (branco) contra Go Seigen (preto)',
    'Go Seigen': 'Go Seigen', "Hon'inbō Shūsai": "Hon'inbō Shūsai", 'Kitani Minoru': 'Kitani Minoru', 'Yasunari Kawabata': 'Yasunari Kawabata',
    'The atomic bombings of Hiroshima (left) and Nagasaki (right)': 'Os bombardeios atômicos de Hiroshima (esquerda) e Nagasaki (direita)',
    'Go Seigen and Kitani Minoru': 'Go Seigen e Kitani Minoru', 'Nie Weiping': 'Nie Weiping', 'A BBC Micro': 'Um BBC Micro',
    'Takemiya Masaki': 'Takemiya Masaki', 'Cho Hunhyun': 'Cho Hunhyun', 'Lee Changho': 'Lee Changho', 'Daniel Barry': 'Daniel Barry',
    'Koichi Wakata': 'Koichi Wakata', 'Rui Naiwei': 'Rui Naiwei', 'Michael Redmond in 2018': 'Michael Redmond em 2018',
    'An AlphaGo computer rack': 'Um rack de computadores do AlphaGo', 'Logo of AlphaGo': 'Logotipo do AlphaGo',
    'Logo of DeepMind': 'Logotipo da DeepMind', 'Fan Hui': 'Fan Hui', 'Lee Sedol in 2016': 'Lee Sedol em 2016', 'Iyama Yūta': 'Iyama Yūta',
    'Ke Jie': 'Ke Jie', 'A game analysed with KataGo': 'Uma partida analisada com o KataGo', 'Lee Sedol': 'Lee Sedol',
    'Sakata Eio': 'Sakata Eio', 'Go Seigen teaching a young Rin Kaiho': 'Go Seigen ensinando o jovem Rin Kaiho',
    'Cho Chikun': 'Cho Chikun', 'Gu Li': 'Gu Li', 'Park Junghwan': 'Park Junghwan',
}

TEXTS = [
 # Lendas e primeiros registros
 'A lenda do "Cabo Apodrecido" sobre a origem do jogo: um carpinteiro em Zhejiang observa divindades jogando um jogo misterioso e perde a noção do tempo.',
 'Segundo a lenda, o imperador Yao cria o jogo para ensinar disciplina e equilíbrio a seu filho Danzhu. Outra lenda diz que Shun, seu sucessor, o inventou para o próprio filho.',
 'A referência escrita mais antiga ao jogo costuma ser atribuída à crônica histórica Zuo Zhuan, a respeito de um evento deste ano; ele também é mencionado nos Analectos de Confúcio e nos livros de Mêncio.',
 'Mêncio menciona um jogador famoso chamado Yi Qiu.',
 'Han Ocidental: um fragmento de tabuleiro de cerâmica, o mais antigo já encontrado na China, é desenterrado mais tarde em Shaanxi.',
 'Han Oriental: Ban Gu escreve o {i}Yì Zhǐ{/i} ("A Essência do Go"), o texto mais antigo que sobreviveu dedicado ao Go, e os tabuleiros têm 17 × 17 linhas.',
 'Os "Diagramas de Wu" registram a partida de Go mais antiga que se conhece.',
 # Leste Asiático antigo e medieval
 'O tabuleiro passa de 17 × 17 para 19 × 19 linhas. O {i}Manual de Go de Dunhuang{/i}, o primeiro livro dedicado ao Go no tabuleiro maior, data desse período.',
 'Na rivalidade entre Goguryeo e Baekje, o monge de Goguryeo To-lim usa o jogo de Go para espionar o rei Yogyong; segue-se a invasão de Baekje.',
 'O imperador Wu de Liang promove o jogo e realiza o primeiro torneio nacional documentado; 278 jogadores recebem uma graduação.',
 'Crônicas chinesas (os Registros de Sui) relatam que os japoneses apreciam o Go.',
 'Dinastia Tang: a corte cria o cargo de atendente de Go ("Qídàizhào") para os jogadores que jogam com o imperador, e os jogadores passam a ser graduados. Atribuem-se a Wang Jixin as "Dez Regras de Ouro do Go".',
 'O jogo chega ao Tibete e à Mongólia, onde o tabuleiro de 17 × 17 sobrevive.',
 'O Go chega ao Japão, tradicionalmente trazido da corte Tang por Kibi no Makibi; o Código Taihō, de 701, já o descreve.',
 'O jogador chinês Yang Jiying viaja à Coreia como enviado e nenhum jogador de Silla consegue igualá-lo.',
 'Dinastia Song: é escrito um grande tratado em treze capítulos, o {i}Clássico do Go{/i} ({i}Qíjīng Shísān Piān{/i}); a era Song também produz muitos outros tratados de estratégia.',
 'O {i}Wangyou Qingle Ji{/i}, compilado por Li Yimin, é o livro de Go mais antigo que sobreviveu. Reúne ensaios, registros de partidas antigas e o primeiro conjunto de problemas de tsumego, entre eles uma partida entre um príncipe japonês e Gu Shiyan, o primeiro registro de uma quebra da escada dupla.',
 'Dinastia Yuan: Yan Defu e Yan Tianzhang compilam o {i}Xuanxuan Qijing{/i} ("Portal para Todas as Maravilhas"), seis volumes com 376 problemas, ensaios e registros de partidas; ele inspira livros de problemas em todo o mundo.',
 'A contagem chinesa passa de território para contagem por pedras. O imperador Hongwu emite um "Édito Proibindo o Weiqi" diante da prática generalizada de apostas no jogo.',
 'Honinbo Sansa joga um ko triplo contra Kashio Rigen em um mosteiro de Quioto, na presença de Oda Nobunaga; a partida é suspensa. No dia seguinte Nobunaga é morto, e o ko triplo passa a ser considerado de mau agouro.',
 'Toyotomi Hideyoshi organiza o primeiro torneio japonês de Go; Hon\'inbō (Sansa) vence e recebe um salário.',
 # Japão do período Edo e China Qing
 'Honinbo Sansa é nomeado pelo xogum Tokugawa Ieyasu chefe do mundo do Go (Meijin Godokoro): começa o grande sistema de escolas de Go do Japão.',
 'O xogunato Tokugawa estabelece quatro casas hereditárias de Go (Hon\'inbō, Inoue, Yasui e Hayashi) e lhes paga estipêndios; elas competem por 250 a 300 anos.',
 'O primeiro jogo no castelo, disputado diante do xogum, acontece em 1626; em 1628 os jogos no castelo se tornam uma cerimônia anual oficial.',
 'A primeira partida oficial de desafio (sōgo) para decidir o Meijin, entre Hon\'inbō Sanetsu e Yasui Sanchi.',
 'Huang Longshi, provavelmente o jogador chinês mais forte da dinastia Qing, nasce (c. 1650 – c. 1694).',
 'O quarto Hon\'inbō, Dōsaku (1645–1702), derrota todos os melhores jogadores de seu tempo e é elogiado por ter "força de treze dan".',
 'É criado o {i}Igo Hatsuyoron{/i}, uma coleção de problemas muito difíceis.',
 'Shi Xiangxia e Fan Xiping disputam os "Dez Jogos de Danghu" em Pinghu, Zhejiang.',
 'O "jogo do vômito de sangue": Hon\'inbō Jōwa vence Akaboshi Intetsu em uma partida de uma semana; Akaboshi desmaia de exaustão e morre pouco depois.',
 'O "jogo das orelhas vermelhas": o lance 127 de Honinbo Shusaku deixa Gennan Inseki atônito e se torna um dos melhores lances de todos os tempos.',
 'Os últimos jogos no castelo são disputados enquanto a crise do xogunato perturba as cerimônias.',
 # Go profissional moderno
 'A Restauração Meiji acaba com os estipêndios oficiais das casas de Go; o Go perde seus patronos e os mestres passam dificuldades.',
 'A primeira coluna de Go em um jornal aparece no Japão, em 1º de abril. Em 1879 forma-se a sociedade Hoensha; seu periódico {i}Igo Shinpo{/i} é a primeira revista de Go.',
 'O profissional japonês Takabe Dōhei visita a China e introduz o jogo sem pedras iniciais fixas.',
 'É fundada a Nihon Ki-in, a associação profissional de Go do Japão, que encerra o sistema de casas hereditárias e inaugura o sistema moderno de graduações e torneios.',
 'O "Jogo do Século": Go Seigen abre nos pontos san-san, estrela e centro contra Honinbo Shusai, em uma partida controversa de três meses que desafia o sistema antigo.',
 'Uma partida de Go é transmitida pelo rádio pela primeira vez.',
 'Shūsai entrega o título de Hon\'inbō à Nihon Ki-in (1936) e se aposenta em 1938 após uma partida contra Kitani Minoru que inspira o romance {i}O Mestre de Go{/i}, de Yasunari Kawabata.',
 'Sekiyama Riichi vence o primeiro torneio do título Hon\'inbō, um dos primeiros grandes torneios modernos com komi (4,5 pontos).',
 'O "Jogo sob a Bomba Atômica": a segunda partida da 3ª disputa do Hon\'inbō, jogada perto de Hiroshima em 6 de agosto, é concluída após a explosão.',
 'Fujisawa Hōsai se torna o primeiro jogador a alcançar o 9º dan pelo sistema de promoção Oteai.',
 'Go Seigen recebe o 9º dan e se torna o melhor jogador do mundo; vence suas partidas de dez jogos contra todos os principais rivais até 1956.',
 'A Associação Coreana de Baduk (Hankuk Kiwon) é fundada, em 28 de janeiro. A primeira NHK Cup é transmitida pelo rádio; passa para a televisão em 1962.',
 'Começa o primeiro torneio profissional da Coreia, a Copa Kuksu.',
 'Começa a Partida Amistosa de Go entre China e Japão; ela é realizada todos os anos até 1991.',
 'Fujisawa Shūkō vence o primeiro torneio do título Meijin.',
 'Depois do "Incidente do Meijin" de 1974, os títulos Tengen (1975), Kisei e Gosei (1976) completam os sete grandes títulos japoneses. Fujisawa Shūkō vence o primeiro Kisei em 1977.',
 'Nie Weiping leva a China à vitória sobre o Japão nas primeiras Super Partidas de Go China–Japão, um triunfo nacional.',
 'Takemiya Masaki vence a primeira Copa Fujitsu, um dos primeiros torneios internacionais.',
 'Cho Hunhyun, o único coreano inscrito, vence a primeira Copa Ing, as "Olimpíadas do Go", derrotando Nie Weiping.',
 'Ma Xiaochun é o primeiro jogador chinês a vencer um torneio internacional, levando a Copa Fujitsu e a Copa Tongyang Securities.',
 'Lee Changho vence a primeira Copa LG.',
 'O mangá {i}Hikaru no Go{/i} (depois também um anime) provoca um boom do Go entre jovens no Japão.',
 'Rui Naiwei, jogando pela Coreia, vence o 43º Kuksu em fevereiro e se torna a primeira mulher a ganhar um grande título.',
 'O sistema de promoção Oteai é descontinuado no Japão e um novo é introduzido.',
 # Jogadores número 1 do mundo
 '{{Flag icon|China}}{{Flag icon|Japan}} Go Seigen se torna o número 1 do mundo.',
 '{{Flag icon|Japan}} Sakata Eio se torna o número 1 do mundo.',
 '{{Flag icon|Taiwan}}{{Flag icon|Japan}} Rin Kaiho se torna o número 1 do mundo.',
 '{{Flag icon|Japan}} Kato Masao se torna o número 1 do mundo.',
 '{{Flag icon|South Korea}}{{Flag icon|Japan}} Cho Chikun se torna o número 1 do mundo.',
 '{{Flag icon|South Korea}} Cho Hunhyun se torna o número 1 do mundo.',
 '{{Flag icon|South Korea}} Lee Changho, aluno de Cho Hunhyun, se torna o número 1 do mundo aos 15 anos.',
 '{{Flag icon|China}} Gu Li se torna o número 1 do mundo.',
 '{{Flag icon|South Korea}} Lee Sedol se torna o número 1 do mundo.',
 '{{Flag icon|South Korea}} Park Junghwan se torna o número 1 do mundo.',
 '{{Flag icon|China}} Ke Jie se torna o número 1 do mundo.',
 '{{Flag icon|South Korea}} Park Junghwan se torna o número 1 do mundo pela segunda vez.',
 '{{Flag icon|South Korea}} Shin Jinseo, cujo estilo lembra o das IAs, se torna o número 1 do mundo.',
 # Go no Ocidente e no espaço
 'Nicolas Trigault publica em Augsburgo os diários do jesuíta Matteo Ricci, que explicam o jogo de weiqi; o livro tem pelo menos 16 edições em línguas europeias.',
 'Thomas Hyde escreve a primeira descrição detalhada do Go em uma língua europeia, em seu tratado sobre jogos de tabuleiro orientais.',
 'O filósofo Leibniz publica um artigo sobre o Go com a imagem de uma partida, dizendo que não conhece todas as regras.',
 'A primeira partida de Go registrada na Europa é jogada entre Kido Takayoshi e Ōkubo Toshimichi, da Missão Iwakura.',
 'Oskar Korschelt, que aprendeu o jogo no Japão com Murase Shūho, publica {i}Das Go Spiel{/i}: a primeira descrição sistemática em uma língua ocidental.',
 'Edward Lasker aprende Go em Berlim (1905) e depois funda o Clube de Go de Nova Iorque; em 1908 Arthur Smith publica o primeiro livro de Go em inglês, {i}The Game of Go{/i}.',
 'O livro {i}Go and Go-moku{/i} (1934), de Lasker, ajuda a popularizar o jogo nos EUA; a Associação Americana de Go é formada em 1935 e a Associação Alemã de Go em 1937.',
 'Manfred Wimmer se torna o primeiro ocidental a receber um certificado profissional de uma associação de Go do Leste Asiático (Kansai Ki-in); James Kerwin é o primeiro na Nihon Ki-in.',
 'Os astronautas Daniel Barry e Koichi Wakata se tornam as primeiras pessoas a jogar Go no espaço.',
 'O americano Michael Redmond é o primeiro ocidental a alcançar o 9º dan.',
 'A Associação Americana de Go assina um acordo com a Associação Coreana de Baduk para promover seu próprio sistema profissional (2011); a Federação Europeia de Go cria o seu (2014).',
 # Go online e Go de computador
 'Albert Zobrist escreve o primeiro programa que joga partidas completas de Go.',
 'Uma partida amistosa entre Taiwan e os Estados Unidos é jogada por teletipo; em 1978 o Reino Unido e a URSS jogam uma por telefone.',
 'Realiza-se o primeiro evento de Go de computador, o torneio da Acornsoft para o BBC Micro. Greg Hale escreve o {i}inetgo{/i}, provavelmente o primeiro programa a jogar Go pela internet.',
 'Começa o Prêmio Ing para programas de computador; ele expira em 2000, quando o último desafio foi vencido pelo HandTalk com 11 pedras de handicap contra um jovem profissional.',
 'O Internet Go Server (IGS), o primeiro servidor dedicado ao Go, entra no ar.',
 'O Gobble, de Bruegmann, é o primeiro programa de Go baseado em simulações aleatórias (Monte Carlo).',
 'É desenvolvido o algoritmo UCT, uma busca em árvore Monte Carlo; um programa que o usa, o CrazyStone, vence no mesmo ano o evento de Go 9×9 da Olimpíada de Computadores.',
 'O MoGo vence uma de três partidas contra o profissional Catalin Taranu em 9×9 e depois derrota um profissional coreano de 8º dan em 19×19 com handicap de 9 pedras.',
 'O programa Zen derrota Takemiya Masaki em partidas com handicap de 5 e 4 pedras.',
 # A era da IA
 'O AlphaGo, criado pela DeepMind do Google, vence o campeão europeu Fan Hui (2p) por 5–0 em partidas sem handicap: a primeira vez que um programa derrota um profissional.',
 'O AlphaGo, da DeepMind, vence Lee Sedol por 4–1 em Seul, a primeira vez que uma IA derrota um profissional de elite. No mesmo ano, Iyama Yūta detém ao mesmo tempo os sete grandes títulos japoneses.',
 'Uma versão mais forte do AlphaGo, da DeepMind ("Master"), vence 60 partidas seguidas, anonimamente, online, contra profissionais de elite.',
 'O novo e muito melhorado AlphaGo, da DeepMind, enfrenta Ke Jie e vence as três partidas; Ke Jie diz que seu jogo é "como um deus do Go".',
 'A IA de Go de código aberto KataGo é criada por David Wu.',
 'Lee Sedol anuncia sua aposentadoria, citando o AlphaGo como "uma entidade que não pode ser derrotada".',
 'Shin Jinseo derrota uma nova versão do KataGo com handicap de 2 pedras, voltando de uma derrota na primeira partida para vencer as duas seguintes.',
]

SL_EVENTS = [
 ('21 de outubro de 2000', 'Dois entusiastas, Arno e Morten, criam um [[wiki]] pensado como repositório on-line de todo o conhecimento sobre Go: a [[:en:Sensei\'s Library|Sensei\'s Library]].'),
 ('5 de janeiro de 2001', 'A Sensei\'s Library abre ao público, anunciada no grupo da Usenet rec.games.go.'),
 ('11 de janeiro de 2004', 'É lançada uma versão em francês, a EncyGoPédie.'),
 ('11 de novembro de 2004', 'A 10.000ª página é adicionada.'),
 ('3 de novembro de 2007', 'A primeira busca por posição em tabuleiro completo (19×19).'),
 ('22 de abril de 2009', 'É adicionada uma busca de tabuleiro personalizada.'),
 ('28 de maio de 2010', 'A 20.000ª página é criada, por Dave Sigaty.'),
]

ELSEWHERE = (
 '\n== Linhas do tempo em outros sites ==\n'
 '* Milton N. Bradley, [http://users.eniinternet.com/bradleym/America.html "How Go came to America"] (Como o Go chegou à América)\n'
 '* [http://gobase.org/history/ Páginas de história] de Jan van der Steen no GoBase\n'
 '* Linhas do tempo extensas estão incluídas no CD GoGoD (Go Game Database)\n'
 '* [https://senseis.xmp.net/?HistoryOfGoInFrance19652007 "History of Go in France 1965–2007"] na Sensei\'s Library\n'
 '* O livro \'\'Eurogo\'\'\n'
)

NOTE_N = 'Os dados sobre quem se tornou o número 1 do mundo, e quando, vêm do [https://www.goratings.org/en/ Go Ratings].'
