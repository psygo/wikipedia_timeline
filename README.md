# Wikipedia Timeline

> See it live on [psygo.github.io/wikipedia_timeline](https://psygo.github.io/wikipedia_timeline/)

A vertical event timeline for Wikipedia, built as a template plus TemplateStyles
(no MediaWiki extension, no JavaScript). See [Docs.md](Docs.md) for design notes and next steps.

Tables are still a great of way of displaying timelines, especially when we have multi-column data. The `TimelineRail` component here seems to be better whenever each event contains a lot of text and multi-type data.

![Timeline of Historic Inventions](/docs/historic_inventions_demo.png)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/screenshot-dark.png">
  <img alt="The timeline in a mock Wikipedia article: sections with red dots, dated events with blue dots, a picture, in the light theme" src="docs/screenshot-light.png">
</picture>

The timeline with sections (red dots) in the prototype article, in the reader's light or dark theme.

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

Needs TemplateStyles and ParserFunctions. The templates are the `TimelineRail` family. `template/` holds one
paste-ready file per wiki page:

| Page                                                              | File                                        | Edit by hand?                        |
| ----------------------------------------------------------------- | ------------------------------------------- | ------------------------------------ |
| `Template:TimelineRail/styles.css` (content model: Sanitized CSS) | `template/TimelineRail__styles.css`         | no: copy of `prototype/timeline.css` |
| `Template:TimelineRail/event`                                     | `template/TimelineRail__event.wikitext`     | yes                                  |
| `Template:TimelineRail/gap`                                       | `template/TimelineRail__gap.wikitext`       | yes                                  |
| `Template:TimelineRail/item`                                      | `template/TimelineRail__item.wikitext`      | yes                                  |
| `Template:TimelineRail/section`                                   | `template/TimelineRail__section.wikitext`   | yes                                  |
| `Template:TimelineRail/parallel`                                  | `template/TimelineRail__parallel.wikitext`  | yes                                  |
| `Template:TimelineRail`                                           | `template/TimelineRail.wikitext`            | yes                                  |
| `Template:TimelineRail/doc`                                       | `template/TimelineRail__doc.wikitext`       | no: from `tools/doc_source.wikitext` |
| `Template:TimelineRail/testcases`                                 | `template/TimelineRail__testcases.wikitext` | no: demo text in `tools/build.py`    |

After changing the stylesheet, the doc or the demo, run `python3 tools/build.py` to regenerate the three generated files.
Usage for one event per dot, several events per dot, nested timelines, collapsible items, sections and parallel timelines is in
`tools/doc_source.wikitext` (what becomes the `/doc` page). For a quick start:

    {{TimelineRail
    |{{TimelineRail/item |date=1612 |title=The Go academy |text=Text.}}
    {{TimelineRail/item |date=March 2016 |title=AlphaGo defeats Lee Sedol}}
    }}

## Other packagings

The same stylesheet, class names and behaviour, outside Wikipedia (the stylesheet is copied from `prototype/timeline.css` by `python3 tools/sync_css.py`, which `tools/build.py` also runs):

- [web-component/](web-component/) is a `<timeline-rail>` custom element, no dependencies, no build step.
- [react/](react/) is a set of React components (Vite library build, TypeScript types).
- [lua/](lua/) is `Module:TimelineRail`, a Scribunto module that writes the same markup (with an `outline` entry point that avoids the post-expand size problem); locally tested only.

## User script (optional)

`userscript/Timeline-toolbar.js` adds a **Timeline** drop-down to the edit toolbar that inserts
skeletons for the simple, multi-event, parallel and grouped timelines. Copy it to
`User:<YourName>/Timeline-toolbar.js` and add `importScript( 'User:<YourName>/Timeline-toolbar.js' );`
to `User:<YourName>/common.js`. Needs the WikiEditor toolbar. Untested on a live wiki.

## Demo on a Wikipedia user subpage

`python3 tools/build.py --sandbox <WikipediaUsername>` writes `sandbox/<username>/` (not tracked): one file per wiki page,
with all template names rewritten to subpages of `User:<username>/Timeline sandbox`, a demo page
`User:<username>/Timeline demo`, and the stylesheet at `Template:<username>/Timeline sandbox/styles.css`
(created by page title; `Special:ChangeContentModel` is limited to admins and template editors).
