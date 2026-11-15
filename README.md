# Wikipedia Timeline

A vertical event timeline for Wikipedia, built as a template plus TemplateStyles
(no MediaWiki extension, no JavaScript). See [Docs.md](Docs.md) for design notes and next steps.

## Try the prototype

    open prototype/article.html

`article.html` is a mock article with the timeline in a section; `index.html` shows it alone.
Resize the window (breakpoint at 640 px) and switch the OS between light and dark.

## Try the template (untested on a wiki)

Needs TemplateStyles and ParserFunctions. Create these pages, pasting the files from `template/`:

| Page | File |
| --- | --- |
| `Template:Timeline` | `Template_Timeline.wikitext` |
| `Template:Timeline item` | `Template_Timeline_item.wikitext` |
| `Template:Timeline/styles.css` (content model: Sanitized CSS) | `Template_Timeline_styles.css` |

Then:

    {{Timeline
    |{{Timeline item |date=1612 |title=The Go academy |text=Text.}}
    {{Timeline item |date=March 2016 |title=AlphaGo defeats Lee Sedol}}
    }}
