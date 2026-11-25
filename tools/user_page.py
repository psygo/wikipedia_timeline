"""Draft of User:Fanaro009: the live page with its timeline written in the !! syntax.

The live page is the source (its wording and sections are the user's). Inside the TimelineRail outline,
from the original syntax to the !! syntax:
  ==, ===  (sections)      become  !!==, !!===
  *        (an event)      becomes !!*
  **       (a list in it)  becomes *    ***  becomes **   and so on: one * less, as plain wikitext lists
  [[File:  (a picture)     becomes !![[File:
A page already in the !! syntax is left as it is.
The infobox gets an Education row (electrical engineering, USP) after the professions.
The timeline is wrapped in Module:ViewSwitcher (the View button): Timeline (default), List and Table. Writes drafts/User_Fanaro009__lua.wikitext.
"""
import pathlib, re, subprocess

root = pathlib.Path(__file__).resolve().parent.parent
cur = subprocess.run(['curl', '-s', '--max-time', '60', 'https://en.wikipedia.org/w/index.php?title=User:Fanaro009&action=raw'],
                     capture_output=True, text=True).stdout


def convert(block):
    if re.search(r'^!!', block, re.M):
        return block
    out = []
    for line in block.split('\n'):
        m = re.match(r'^(\*+)(.*)$', line)
        if m:
            stars = m.group(1)
            line = '!!*' + m.group(2) if len(stars) == 1 else stars[1:] + m.group(2)
        elif re.match(r'^=+.*=+$|^\[\[File:', line):
            line = '!!' + line
        out.append(line)
    return '\n'.join(out)


def fix(m):
    return m.group(1) + convert(m.group(2)) + m.group(3)




def add_education(page):
    """An Education row after Professions (row 6); the rows below it move down one number."""
    end = page.index('\n}}')
    box, rest = page[:end], page[end:]
    if 'Education' in box:
        return page
    box = re.sub(r'\| (header|label|data)(\d+)(\s*=)',
                 lambda m: '| %s%d%s' % (m.group(1), int(m.group(2)) + (1 if int(m.group(2)) >= 7 else 0), m.group(3)), box)
    row = ('| label7  = Education\n'
           '| data7   = [[Electrical engineering]] graduate<br/>[[University of São Paulo|University of São Paulo (USP)]]\n')
    box = box.replace('\n\n| header8', '\n' + row + '\n| header8', 1)
    return box + rest


cur = add_education(cur)
SWITCH = '{{#invoke:ViewSwitcher|switch |views=*Timeline=TimelineRail.outline; List=OutlineList.list; Table=OutlineTable.table\n|id='
cur = re.sub(r'\{\{#invoke:TimelineRail\|outline \|id=', lambda m: SWITCH, cur)

# the text of each outline: from "|text=" to the closing }} on a line of its own
page = re.sub(r'(\{\{#invoke:(?:TimelineRail\|outline|ViewSwitcher\|switch)[^\n]*\n(?:\|[^\n]*\n)*?\|text=\n)(.*?)(\n\}\})', fix, cur, flags=re.S)
(root / 'drafts' / 'User_Fanaro009__lua.wikitext').write_text(page.rstrip('\n') + '\n')
