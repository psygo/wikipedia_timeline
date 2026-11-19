# Wikipedia Timeline

> See it live on [psygo.github.io/wikipedia_timeline](https://psygo.github.io/wikipedia_timeline/)

A vertical event timeline for Wikipedia, built as a template plus TemplateStyles
(no MediaWiki extension, no JavaScript). See [Docs.md](Docs.md) for design notes and next steps.

## References

- [Wikipedia Proposal](<https://en.wikipedia.org/wiki/Wikipedia:Village_pump_(proposals)#Timeline_Visual_Component%3E>)
- [Go | Hall of Fame](https://go-hall-of-fame.vercel.app)

## Try the prototype

    open prototype/index.html

`index.html` is a viewer: drag the handles on the left and right edges (or focus one and use the arrow keys)
to change the page width, and use the Theme button (system / light / dark). The timeline switches layout at 640 px.
`article.html` is the mock article itself; `alone.html` shows the timeline alone.
The prototype is also published with GitHub Pages (see `.github/workflows/pages.yml`).

## Try the template (untested on a wiki)

Needs TemplateStyles and ParserFunctions. The templates are the `TimelineRail` family. `python3 tools/make_sandbox.py --release`
writes paste-ready files into `release/`, one per page:

| Page                                                              | File                                |
| ----------------------------------------------------------------- | ----------------------------------- |
| `Template:TimelineRail/styles.css` (content model: Sanitized CSS) | `TimelineRail__styles.css`          |
| `Template:TimelineRail/event`                                     | `TimelineRail__event.wikitext`      |
| `Template:TimelineRail/gap`                                       | `TimelineRail__gap.wikitext`        |
| `Template:TimelineRail/item`                                      | `TimelineRail__item.wikitext`       |
| `Template:TimelineRail/section`                                   | `TimelineRail__section.wikitext`    |
| `Template:TimelineRail/parallel`                                  | `TimelineRail__parallel.wikitext`   |
| `Template:TimelineRail`                                           | `TimelineRail.wikitext`             |
| `Template:TimelineRail/doc`                                       | `TimelineRail__doc.wikitext`        |
| `Template:TimelineRail/testcases`                                 | `TimelineRail__testcases.wikitext`  |

The sources are in `template/` (`Template_TimelineRail*.wikitext`, `Template_TimelineRail_styles.css`); `release/` is generated.
Usage for one event per dot, several events per dot, nested timelines, collapsible items, sections and parallel timelines is in
`template/Template_TimelineRail_doc.wikitext`. For a quick start:

    {{TimelineRail
    |{{TimelineRail/item |date=1612 |title=The Go academy |text=Text.}}
    {{TimelineRail/item |date=March 2016 |title=AlphaGo defeats Lee Sedol}}
    }}

## User script (optional)

`userscript/Timeline-toolbar.js` adds a **Timeline** drop-down to the edit toolbar that inserts
skeletons for the simple, multi-event, parallel and grouped timelines. Copy it to
`User:<YourName>/Timeline-toolbar.js` and add `importScript( 'User:<YourName>/Timeline-toolbar.js' );`
to `User:<YourName>/common.js`. Needs the WikiEditor toolbar. Untested on a live wiki.

## Demo on a Wikipedia user subpage

`python3 tools/make_sandbox.py <WikipediaUsername>` writes `sandbox/<username>/`: one file per wiki page,
with all template names rewritten to subpages of `User:<username>/Timeline sandbox`, a demo page
`User:<username>/Timeline demo`, and the stylesheet at `Template:<username>/Timeline sandbox/styles.css`
(created by page title; `Special:ChangeContentModel` is limited to admins and template editors). Page titles are printed by the script; see Docs.md for the steps.
