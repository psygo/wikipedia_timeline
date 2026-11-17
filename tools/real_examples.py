"""Data for the 'examples from real articles' section (used by make_sandbox.py and
for the prototype article). Content is transcribed from English Wikipedia
(CC BY-SA 4.0); attribution is in the section text. Markup: [[X]] link, ''x'' italic."""

# Timeline of historic inventions, "Paleolithic" section: (date, title, text)
INVENTIONS = [
 ('3.3 Mya – 2.6 Mya', '[[Stone tools]]', 'Found in modern-day [[Kenya]] are older and only found on the archetype road. Ancient stone tools from [[Ethiopia]] ([[Oldowan]]) were hand-crafted by [[Australopithecus]] or related people.'),
 ('1.76 Mya', 'Advanced ([[Acheulean]]) stone tools', 'In [[Kenya]] by \'\'[[Homo erectus]]\'\'.'),
 ('1.75 Mya – 150 kya', '[[Origin of language]]', 'Varying estimates.'),
 ('1.5 Mya', '[[Control of fire]]', 'Earliest likely, by \'\'[[Homo erectus]]\'\'.'),
 ('1.5 Mya', '[[Bone tools]]', 'In Africa by \'\'[[Homo erectus]]\'\' and/or \'\'[[Paranthropus boisei]]\'\'.'),
 ('1 Mya – 780 kya', '[[Cooking]]', 'In the Middle East by [[Homo erectus]].'),
 ('900 kya – 40 kya', '[[Rafts]]', ''),
 ('500 kya', '[[Hafting]]', 'In South Africa by \'\'[[Homo heidelbergensis]]\'\'.'),
 ('500 kya – 450 kya', '[[Woodworking]] construction', 'In Zambia by \'\'[[Homo heidelbergensis]]\'\'. (The [[oldest known surviving buildings]] are made from stone and date back no more than 9,500 years.)'),
 ('420 kya – 200 kya', '[[Food storage]]', 'In the form of uncracked bones saved for their marrow in [[Qesem cave]], [[Israel]].'),
 ('400 kya', '[[Hide and leather]]', 'Clothing, footwear and shelter.'),
 ('400 kya', '[[Pigments]]', 'In Zambia by \'\'[[Homo heidelbergensis]]\'\'.'),
 ('337 kya – 300 kya', '[[Schöningen spears]]', 'In [[Germany]], likely by \'\'[[Homo heidelbergensis]]\'\' or early Neanderthals.'),
 ('320 kya', '[[Trade]]', 'Long-distance (up to 50 miles) [[transportation]] of resources (e.g. [[obsidian]]), use of pigments, and possible making of projectile points in Kenya.'),
]

# The Elder Scrolls, "Release timeline": (year, main series entries, other entries)
# Sections of the list above: (title, index of its first entry)
INVENTION_SECTIONS = [('3.3 Mya – 1 Mya', 0), ('1 Mya and later', 5)]

SCROLLS = [
 ('1994', ['Arena'], []), ('1995', [], []), ('1996', ['II: Daggerfall'], []),
 ('1997', [], ['Battlespire']), ('1998', [], ['Adventures: Redguard']), ('1999–2001', [], []),
 ('2002', ['III: Morrowind'], ['III: Tribunal']), ('2003', [], ['III: Bloodmoon', 'Travels: Stormhold']),
 ('2004', [], ['Travels: Dawnstar', 'Travels: Shadowkey']), ('2005', [], []),
 ('2006', ['IV: Oblivion'], ['IV: Knights of the Nine']), ('2007', [], ['IV: Shivering Isles']),
 ('2008–2010', [], []), ('2011', ['V: Skyrim'], []),
 ('2012', [], ['V: Dawnguard', 'V: Hearthfire', 'V: Dragonborn']), ('2013', [], []),
 ('2014', [], ['Online']), ('2015', [], []), ('2016', [], ['V: Special Edition']),
 ('2017', [], ['Legends', 'V VR', 'Online Morrowind']), ('2018', [], ['Online Summerset']),
 ('2019', [], ['Online Elsweyr']), ('2020', [], ['Blades', 'Online Greymoor']),
 ('2021', [], ['Online Blackwood', 'V Anniversary']), ('2022', [], ['Online High Isle']),
 ('2023', [], ['Online Necrom']), ('2024', [], ['Online Gold Road', 'Castles']),
 ('2025', [], ['IV: Oblivion Remastered']), ('TBA', ['VI: Sentinel'], []),
]

def wikitext(base):
    """Wikitext for both examples, using template names under `base`."""
    o = ["{{%s |compact=yes" % base, ]
    # (main entries use title= so they are bold; the others text= in italics)
    for y, main, other in SCROLLS:
        evs = [("title", "''%s''" % m) for m in main] + [("text", "''%s''" % x) for x in other]
        if not evs: o.append("|{{%s/item |date=%s}}" % (base, y) if len(o) == 1 else "{{%s/item |date=%s}}" % (base, y))
        elif len(evs) == 1:
            o.append(("|" if len(o) == 1 else "") + "{{%s/item |date=%s |%s=%s}}" % (base, y, *evs[0]))
        else:
            o.append(("|" if len(o) == 1 else "") + "{{%s/item |date=%s |events=" % (base, y))
            o += ["{{%s/event |%s=%s}}" % (base, k, v) for k, v in evs]
            o.append("}}")
    o.append("}}")
    scrolls = "\n".join(o)
    o = ["{{%s" % base]
    bounds = [s for _, s in INVENTION_SECTIONS] + [len(INVENTIONS)]
    for k, (title, start) in enumerate(INVENTION_SECTIONS):
        o.append(("|" if k == 0 else "") + "{{%s/section |title=%s" % (base, title))
        for n, (d, ti, x) in enumerate(INVENTIONS[start:bounds[k + 1]]):
            body = "{{%s/item |date=%s |title=%s%s}}" % (base, d, ti, (" |text=" + x) if x else "")
            o.append(("|" if n == 0 else "") + body)
        o.append("}}")
    o.append("}}")
    return "\n".join(o), scrolls
