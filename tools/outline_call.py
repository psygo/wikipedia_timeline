"""The wikitext call for one outline, shared by the converters: Module:TimelineRail alone, or wrapped in
Module:ViewSwitcher (--switcher or --switcher=ViewSwitcher/sandbox) so the reader can switch between
the timeline, a list and a table of the same data."""
import sys

def invoke(module, id, body, flags=None):
    flags = flags if flags is not None else [a for a in sys.argv[1:] if a.startswith('--')]
    sw = next((f.split('=', 1)[1] if '=' in f else 'ViewSwitcher' for f in flags if f.startswith('--switcher')), None)
    if sw is None:
        return '{{#invoke:%s|outline |id=%s\n|text=\n%s\n}}' % (module, id, body)
    suffix = module[len('TimelineRail'):]          # '' or '/sandbox': the other modules follow the same sandbox
    views = 'Timeline=%s.outline; List=OutlineList%s.list; Table=OutlineTable%s.table' % (module, suffix, suffix)
    parser = '\n|parser=' + module if suffix else ''
    return '{{#invoke:%s|switch |views=%s%s\n|id=%s\n|text=\n%s\n}}' % (sw, views, parser, id, body)
