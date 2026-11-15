# Wikipedia Timeline

> See it live on [psygo.github.io/wikipedia_timeline](https://psygo.github.io/wikipedia_timeline/)

A vertical event timeline for Wikipedia, built as a template plus TemplateStyles
(no MediaWiki extension, no JavaScript). See [Docs.md](Docs.md) for design notes and next steps.

## Try the prototype

    open prototype/index.html

`index.html` is a viewer: drag the handles on the left and right edges (or focus one and use the arrow keys)
to change the page width, and use the Theme button (system / light / dark). The timeline switches layout at 640 px.
`article.html` is the mock article itself; `alone.html` shows the timeline alone.
The prototype is also published with GitHub Pages (see `.github/workflows/pages.yml`).

## Try the template (untested on a wiki)

Needs TemplateStyles and ParserFunctions. Create these pages, pasting the files from `template/`:

| Page                                                          | File                              |
| ------------------------------------------------------------- | --------------------------------- |
| `Template:Timeline`                                           | `Template_Timeline.wikitext`      |
| `Template:Timeline item`                                      | `Template_Timeline_item.wikitext` |
| `Template:Timeline/styles.css` (content model: Sanitized CSS) | `Template_Timeline_styles.css`    |

Names are placeholders (`Template:Timeline` is already taken on English Wikipedia). Usage for one event per dot,
several events per dot and parallel timelines is in `template/Template_Timeline_doc.wikitext`. For a quick start:

    {{Timeline
    |{{Timeline item |date=1612 |title=The Go academy |text=Text.}}
    {{Timeline item |date=March 2016 |title=AlphaGo defeats Lee Sedol}}
    }}

## User script (optional)

`userscript/Timeline-toolbar.js` adds a **Timeline** drop-down to the edit toolbar that inserts
skeletons for the simple, multi-event, parallel and grouped timelines. Copy it to
`User:<YourName>/Timeline-toolbar.js` and add `importScript( 'User:<YourName>/Timeline-toolbar.js' );`
to `User:<YourName>/common.js`. Needs the WikiEditor toolbar. Untested on a live wiki.
