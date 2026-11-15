# Wikipedia Timeline

> See it live on [psygo.github.io/wikipedia_timeline](https://psygo.github.io/wikipedia_timeline/)

A vertical event timeline for Wikipedia, built as a template plus TemplateStyles
(no MediaWiki extension, no JavaScript). See [Docs.md](Docs.md) for design notes and next steps.

## Try the prototype

    open prototype/index.html

`index.html` is a mock article with the timeline in a section; `alone.html` shows it alone.
Resize the window (breakpoint at 640 px) and use the Theme button (system / light / dark).
The prototype is also published with GitHub Pages (see `.github/workflows/pages.yml`).

## Try the template (untested on a wiki)

Needs TemplateStyles and ParserFunctions. Create these pages, pasting the files from `template/`:

| Page                                                          | File                              |
| ------------------------------------------------------------- | --------------------------------- |
| `Template:Timeline`                                           | `Template_Timeline.wikitext`      |
| `Template:Timeline item`                                      | `Template_Timeline_item.wikitext` |
| `Template:Timeline/styles.css` (content model: Sanitized CSS) | `Template_Timeline_styles.css`    |

Then:

    {{Timeline
    |{{Timeline item |date=1612 |title=The Go academy |text=Text.}}
    {{Timeline item |date=March 2016 |title=AlphaGo defeats Lee Sedol}}
    }}
