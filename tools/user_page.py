"""Draft of User:Fanaro009: the live page with its timeline written in the !* style.

The live page is the source (its wording and sections are the user's). Inside the TimelineRail outline:
  *   (an event)           becomes  !*
  **  (a list in it)       becomes  *
  *** (a nested list)      becomes  **   and so on: one * less, as plain wikitext lists.
A page already in the !* style is left as it is. Writes drafts/User_Fanaro009__lua.wikitext.
"""
import pathlib, re, subprocess

root = pathlib.Path(__file__).resolve().parent.parent
cur = subprocess.run(['curl', '-s', '--max-time', '60', 'https://en.wikipedia.org/w/index.php?title=User:Fanaro009&action=raw'],
                     capture_output=True, text=True).stdout


def convert(block):
    if re.search(r'^!\*', block, re.M):
        return block
    out = []
    for line in block.split('\n'):
        m = re.match(r'^(\*+)(.*)$', line)
        if m:
            stars = m.group(1)
            line = '!*' + m.group(2) if len(stars) == 1 else stars[1:] + m.group(2)
        out.append(line)
    return '\n'.join(out)


def fix(m):
    return m.group(1) + convert(m.group(2)) + m.group(3)


# the text of each outline: from "|text=" to the closing }} on a line of its own
page = re.sub(r'(\{\{#invoke:TimelineRail\|outline[^\n]*\n\|text=\n)(.*?)(\n\}\})', fix, cur, flags=re.S)
(root / 'drafts' / 'User_Fanaro009__lua.wikitext').write_text(page.rstrip('\n') + '\n')
