# wiki_timeline

A vertical event timeline for Wikipedia, built as a template plus TemplateStyles
(no MediaWiki extension, no JavaScript).

## Why a template

+ EasyTimeline renders images; Chart has no timeline type.
+ `{{Timeline-start}}`, `{{Timeline-item}}`, `{{Timeline-end}}` render a plain definition list
  (docs last edited 2009).
+ Codex components need JavaScript; a timeline does not.

## Layout

+ `prototype/`: standalone HTML and CSS, open `prototype/index.html` in a browser.
  + `timeline.css` is written to be portable to TemplateStyles (one root class `wt-timeline`,
    Codex colour tokens with fallbacks, no `@import`, no external urls).
  + Markup is an `<ol>` of `<li>` items with a `<span>` for the date (`<time>` is not
    something I could confirm the wikitext sanitizer allows).
+ `template/`: `Template:Timeline`, `Template:Timeline item`, docs, and a copy of the CSS for `Template:Timeline/styles.css`.

## Behaviour

+ Under 720 px: one column, rail on the left.
+ 720 px and up: rail in the centre, events alternate sides.
+ Dots alternate filled and hollow.
+ Dark mode follows the Codex tokens (the prototype fakes them with `prefers-color-scheme`).

## Next steps

+ Check the CSS against the TemplateStyles sanitizer on a test wiki.
+ Test the wikitext template in `template/` on a test wiki (not yet run anywhere).
  + Newlines between items inside `{{Timeline}}` may inject stray `<p>`/`<br>` in the `<ol>`; if so, put items on one line or switch to a Lua module.
+ Check Vector 2022 dark mode and the mobile skin, plus print.
+ Discuss at the Village pump and WikiProject Templates; file a Phabricator task.
