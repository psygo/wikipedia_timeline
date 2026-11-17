# wiki_timeline

A vertical event timeline for Wikipedia, built as a template plus TemplateStyles
(no MediaWiki extension, no JavaScript).

## Why a template

+ EasyTimeline renders images; Chart has no timeline type.
+ `{{Timeline-start}}`, `{{Timeline-item}}`, `{{Timeline-end}}` render a plain definition list
  (docs last edited 2009).
+ Codex components need JavaScript; a timeline does not.

## Layout

+ `prototype/`: standalone HTML and CSS.
  + `index.html`: viewer. Shows `article.html` in an iframe with draggable left/right handles (also ← → keys and width presets), so the media queries react to the frame width.
  + `article.html`: mock Wikipedia article (Vector-like chrome, infobox, headings) with three example timelines: simple, several events per dot, parallel timelines, and parallel and grouped timelines.
  + `alone.html`: the timeline alone.
  + `theme-toggle.js`: prototype-only button cycling system / light / dark (sets `data-theme`, remembered in localStorage). The template itself stays JS-free.
  + `timeline.css`: the real stylesheet, written to be portable to TemplateStyles (one root class `wt-timeline`,
    Codex tokens via `var(--token, fallback)` only, no custom properties declared, no `@import`, no external urls).
  + `vector-stub.css`: fake Vector chrome and Codex tokens (light and dark); prototype only.
  + Markup is an `<ol>` of `<li>` items with a `<span>` for the date (`<time>` is not
    something I could confirm the wikitext sanitizer allows).
+ `prototype/images/huang-longshi.png`: photo of a Huang Longshi statue, supplied by the maintainer; source and licence still to be confirmed (see Next steps).
+ `userscript/Timeline-toolbar.js`: WikiEditor toolbar drop-down that inserts the four wikitext skeletons (install steps in the file header). Tested only against a mock of the WikiEditor API, not on a wiki.
+ `.github/workflows/pages.yml`: deploys `prototype/` to GitHub Pages on push to `main`.
+ `template/`: `Template:Timeline`, `Timeline item`, `Timeline event`, `Timeline parallel`, `Timeline gap`, docs, and a copy of the CSS for `Template:Timeline/styles.css`.
  Keep `template/Template_Timeline_styles.css` identical to `prototype/timeline.css`.

## Behaviour

+ Design follows Vector: bold plain-text dates, Codex progressive blue dots, subtle grey rail, thumbnail-style image box.
+ 640 px and up: date column on the left, rail, then title, text and image.
+ Several events on one dot sit side by side and wrap (flex, 14 em minimum each).
+ Collapsible items, **on by default** for every item with content (`collapsible=no` opts out, `collapsed=yes` starts closed, `summary=` is the peek for multi-event items, `id=` overrides the generated id). The id is `{{anchorencode:date_title}}`, so two items with the same date and title on one page collide (use `id=`); anchorencode output with brackets (a wikilink as title) is untested as a class/id. The date row is a toggler (and carries the dot) for a `div.wt-timeline__body` holding the events and any nested timeline. The compact variant makes rows inert (`display: contents`) and always shows the body. Original description: the date row is a toggler (and carries the dot) for a `div.wt-timeline__body` holding the events and any nested timeline. It uses MediaWiki's own collapsible module via a *custom toggler* (`mw-customtoggle-ID` on the row, `mw-collapsible` + `id=mw-customcollapsible-ID` on the body), so the template ships no script, but the toggle needs JS in the reader's browser (without it the item stays open). Collapsed: hollow dot, date inline, title after a `|`. IDs must be unique per page and alphanumeric. `<details>`/`<summary>` was the first idea but English Wikipedia escapes them (checked through the parse API). Prototype: `collapsible-shim.js` emulates the module. Double-click on any dot (collapse/expand all of that timeline) cannot be done by a template, so it is the optional user script `userscript/Timeline-collapse-all.js` (also in the shim). Not for the compact variant.
+ Sections (`Timeline section`, `li.wt-timeline__item--section`): a red dot (`--color-destructive`) and a bold title on the rail, plus a collapsible body (same `mw-collapsible` custom-toggler mechanism as items) holding an `ol.wt-timeline--section`, indented 1.5em. The body has the page background and is positioned so the outer rail does not run through the inner timeline. A section's list can contain sections, so nesting is unlimited (limited in practice by width and by MediaWiki's template expansion limits, untested). In groups and nested `sub` timelines the title uses the compact layout. Nesting of plain items alone is the older `sub` parameter.
+ Compact variant (`wt-timeline--compact`, template `compact=yes`): one dense row per date, a 2em solid bar (one `::before` segment per item) instead of rail and dots, date column right-aligned, text inline in a subtle colour; date-only items allowed. CSS is last in the file so it wins at every width. Inspired by the Elder Scrolls release timeline; not meant for use inside parallel groups.
+ Nested timelines: an `li` can hold an `ol.wt-timeline.wt-timeline--sub` after its events (template: `sub=` parameter of `Timeline item`). It is indented under the parent's events, uses the compact layout (date above, rail on the left, lighter date) and can nest to any depth. Not tested inside grouped timelines.
+ Parallel timelines (`wt-timelines`): several separate timelines, each with its own dates, rail and optional heading, share a row and wrap when there is no horizontal space. They are independent and always use the compact layout (date above events), because the 640 px breakpoint follows the window, not the column.
+ Parallel and grouped (`wt-timelines--grouped`, window ≥ 640 px): the group is one flat grid (`display: contents` on the wrappers, 21 rows). Each heading sits in row 1 and starts a column, items flow down it, so the n-th item of every timeline shares a row and dots line up; `wt-timeline__item--gap` placeholders skip rows. Needs a heading per timeline, max 20 items, no trailing gaps. Columns share the width and do not wrap; under 640 px it falls back to the independent layout. First attempt used `@supports` + subgrid, which the TemplateStyles sanitizer rejects ("Invalid condition for @supports"), so it was removed.
+ Under 640 px: one column, rail on the left, date above the title.
+ Dark mode follows the Codex tokens (the prototype fakes them with `prefers-color-scheme`).

## Checked locally (headless Chrome, prototype only)

+ Wide (1100 px) and narrow (375 px), light and dark: layout holds, dot aligned with the date line.
+ Contrast: Codex blue dots on the base background are fine in both themes; the rail is decorative.
+ Screen readers: dots and rail are CSS only; the `<ol>` conveys order.
+ Wikilinks and templates in `title` and `text` work, since they are plain wikitext.
+ Not checked: real Vector 2022, the mobile skin, TemplateStyles sanitizer, any browser other than Chrome.

## Next steps

+ Confirm the source and licence of `prototype/images/huang-longshi.png` (ideally replace it with a Wikimedia Commons file and credit it).

+ Check the CSS against the TemplateStyles sanitizer on a test wiki.
+ Test the wikitext template in `template/` on a test wiki (not yet run anywhere).
  + Newlines between items inside `{{Timeline}}` may inject stray `<p>`/`<br>` in the `<ol>`; if so, put items on one line or switch to a Lua module.
+ Check Vector 2022 dark mode and the mobile skin, plus print.
+ Discuss at the Village pump and WikiProject Templates; file a Phabricator task.
