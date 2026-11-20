"""The wikitext call for one outline, shared by the converters.

Without --switcher: {{#invoke:TimelineRail|outline ...}}.
With --switcher (or --switcher=ViewSwitcher/sandbox): the outline inside Module:ViewSwitcher, three views,
the timeline first (the default). If the article's original text is given, it is one of the three views
as it is (the list or table the article has today); the other two are made from the outline.
"""
import sys

def protect_pipes(text):
    """Every | that would end a template argument becomes {{!}}: the original text is passed as an
    argument. A | inside [[ ]], {{ }} or <ref> stays as it is."""
    out, i, depth, in_ref = [], 0, 0, False
    while i < len(text):
        two = text[i:i + 2]
        if text.startswith('<ref', i) and not in_ref:
            j = text.find('>', i)
            if j != -1 and text[j - 1] != '/':
                in_ref = True
            out.append(text[i:j + 1]); i = j + 1; continue
        if text.startswith('</ref>', i):
            in_ref = False; out.append('</ref>'); i += 6; continue
        if not in_ref and two in ('[[', '{{'):
            depth += 1; out.append(two); i += 2; continue
        if not in_ref and two in (']]', '}}'):
            depth -= 1; out.append(two); i += 2; continue
        if text[i] == '|' and depth == 0 and not in_ref:
            out.append('{{!}}')
        else:
            out.append(text[i])
        i += 1
    return ''.join(out)

def invoke(module, id, body, original=None, original_as='table', flags=None):
    flags = flags if flags is not None else [a for a in sys.argv[1:] if a.startswith('--')]
    sw = next((f.split('=', 1)[1] if '=' in f else 'ViewSwitcher' for f in flags if f.startswith('--switcher')), None)
    if sw is None:
        return '{{#invoke:%s|outline |id=%s\n|text=\n%s\n}}' % (module, id, body)
    suffix = module[len('TimelineRail'):]          # '' or '/sandbox': the other modules follow the same sandbox
    views = ['*Timeline=%s.outline' % module]
    for label, kind in (('List', 'list'), ('Table', 'table')):
        if original and original_as == kind:
            views.append('%s=@original' % label)
        else:
            views.append('%s=%s%s.%s' % (label, 'OutlineList' if kind == 'list' else 'OutlineTable', suffix, kind))
    parser = '\n|parser=' + module if suffix else ''
    orig = '\n|original=\n%s' % protect_pipes(original.strip('\n')) if original else ''
    return '{{#invoke:%s|switch |views=%s%s\n|id=%s\n|text=\n%s%s\n}}' % (sw, '; '.join(views), parser, id, body, orig)
