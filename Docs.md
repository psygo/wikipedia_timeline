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
  + `article.html`: mock Wikipedia article (Vector-like chrome, infobox, headings) with the timeline in a section.
  + `alone.html`: the timeline alone.
  + `theme-toggle.js`: prototype-only button cycling system / light / dark (sets `data-theme`, remembered in localStorage). The template itself stays JS-free.
  + `timeline.css`: the real stylesheet, written to be portable to TemplateStyles (one root class `wt-timeline`,
    Codex tokens via `var(--token, fallback)` only, no custom properties declared, no `@import`, no external urls).
  + `vector-stub.css`: fake Vector chrome and Codex tokens (light and dark); prototype only.
  + Markup is an `<ol>` of `<li>` items with a `<span>` for the date (`<time>` is not
    something I could confirm the wikitext sanitizer allows).
+ `prototype/images/huang-longshi.png`: photo of a Huang Longshi statue, supplied by the maintainer; source and licence still to be confirmed (see Next steps).
+ `.github/workflows/pages.yml`: deploys `prototype/` to GitHub Pages on push to `main`.
+ `template/`: `Template:Timeline`, `Template:Timeline item`, docs, and a copy of the CSS for `Template:Timeline/styles.css`.
  Keep `template/Template_Timeline_styles.css` identical to `prototype/timeline.css`.

## Behaviour

+ Design follows Vector: bold plain-text dates, Codex progressive blue dots, subtle grey rail, thumbnail-style image box.
+ 640 px and up: date column on the left, rail, then title, text and image.
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
