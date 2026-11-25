"""Rewrite the outline texts in the given files from the original syntax to the !! syntax.

Usage: python3 tools/migrate_outline.py FILE...

An outline text is what follows a line "|text=" up to a line that starts "|original=" or "}}".
  == Title ==  ->  !!== Title ==        * event  ->  !!* event        ** list  ->  * list
  [[File:...]] ->  !![[File:...]]       (one * less on every list line)
A text that already has a line starting with !! is left as it is, so the script can run twice.
"""
import re, sys, pathlib

BLOCK = re.compile(r'(^\|text=[ \t]*\n)(.*?)(?=^\|original=|^\}\})', re.M | re.S)


def convert(text):
    if re.search(r'^!!', text, re.M):
        return text
    out = []
    for line in text.split('\n'):
        m = re.match(r'^(\*+)(.*)$', line)
        if m:
            stars = m.group(1)
            line = '!!*' + m.group(2) if len(stars) == 1 else stars[1:] + m.group(2)
        elif re.match(r'^=+.*=+\s*$|^\[\[File:', line):
            line = '!!' + line
        out.append(line)
    return '\n'.join(out)


def migrate(src):
    return BLOCK.sub(lambda m: m.group(1) + convert(m.group(2)), src)


if __name__ == '__main__':
    for name in sys.argv[1:]:
        p = pathlib.Path(name)
        old = p.read_text()
        new = migrate(old)
        if new != old:
            p.write_text(new)
            print('migrated', name)
