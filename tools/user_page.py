"""Draft of User:Fanaro009 with a TimelineRail timeline (account creation, then the software contributions).

Keeps the live page up to its "Wikipedia Software Contributions" section and replaces that list.
Writes drafts/User_Fanaro009__lua.wikitext.
"""
import pathlib, subprocess

root = pathlib.Path(__file__).resolve().parent.parent
cur = subprocess.run(['curl', '-s', '--max-time', '60', 'https://en.wikipedia.org/w/index.php?title=User:Fanaro009&action=raw'],
                     capture_output=True, text=True).stdout
for marker in ('=Wikipedia Software Contributions=', '=Wikipedia timeline='):
    cur = cur.split(marker)[0]
head = cur.rstrip() + '\n\n'

# The outline module has one level of sub-points, so each group of links is one line.
# A | inside the invoke would end the text argument: {{!}}.
timeline = """=Wikipedia timeline=

{{#invoke:TimelineRail|outline |id=fanaro009 |toc=no
|text=
* August 7, 2012 ;; Account created ;; I created the account Fanaro009.
* November 2026 ;; Wikipedia software contributions ;; The <code>TimelineRail</code> component.
** '''Documentation:''' [https://github.com/psygo/wikipedia_timeline @psygo/wikipedia_timeline] · [https://neofanaro.io/articles/wikipedia-timeline A Wikipedia Timeline Component {{!}} neofanaro.io] · [[Module:TimelineRail|<code>TimelineRail</code> Lua Module]] · [[Wikipedia:Village pump (proposals)#Timeline Visual Component|Timeline Component Proposal]] · [[Wikipedia talk:Gadget#ViewSwitcher for Timelines|<code>ViewSwitcher</code> Gadget Proposal]]
** '''Articles using it:''' [[Timeline of first images of Earth from space]] · [[Timeline of Go]]
** '''Drafts:''' [[User:Fanaro009/Timeline of historic inventions|Timeline of historic inventions]] · [[User:Fanaro009/Timeline of artificial intelligence|Timeline of artificial intelligence]] · [[User:Fanaro009/Timeline of mathematics|Timeline of mathematics]]
}}
"""
(root / 'drafts' / 'User_Fanaro009__lua.wikitext').write_text(head + timeline)
