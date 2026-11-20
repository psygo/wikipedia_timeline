# `<timeline-rail>`: web component

The vertical timeline of this project as a custom element. No dependencies, no build step.
It draws into a shadow root with the project's own stylesheet (`prototype/timeline.css`, the
same class names as the Wikipedia template), so it looks and behaves like the template.

```html
<link rel="stylesheet" href="src/theme.css">             <!-- optional: colour tokens, light and dark -->
<script type="module" src="src/timeline-rail.js"></script>

<timeline-rail>
  <timeline-item date="1612" title="The Go academy">The Tokugawa shogunate ...</timeline-item>
  <timeline-section title="Modern era" id="modern">
    <timeline-item date="2016" title="AlphaGo" image="a.jpg" caption="Game 4">...</timeline-item>
  </timeline-section>
</timeline-rail>
```

Open `demo/index.html` through a local server (modules do not load from `file://`):
`npm start` here, then http://localhost:8080/web-component/demo/.

| Element | Attributes | Content |
|---|---|---|
| `<timeline-rail>` | `grouped` (align the dots of side-by-side columns) | items, sections, gaps, or columns |
| `<timeline-item>` | `date`, `title`, `summary`, `image`, `image-alt`, `image-width`, `caption`, `id`, `collapsed`, `collapsible="false"`, `last` | the text (any HTML); nested `<timeline-item>`s are a sub timeline; `<timeline-event>`s put several events on one dot |
| `<timeline-section>` | `title`, `id`, `collapsed`, `text`, `image`, `caption` | items and sections, to any depth; other content is the introduction in the row |
| `<timeline-event>` | `title`, `text`, `image`, `image-alt`, `image-width`, `caption` | the text |
| `<timeline-column>` | `title` | items; several columns make timelines side by side |
| `<timeline-gap>` | | nothing; fills a slot so grouped columns line up |

* **Interaction.** Click or Enter on a row toggles it. Double-click an item's dot to collapse or
  expand every item of that timeline; double-click a section's dot to keep it open and close
  its sibling sections. A `timeline-toggle` event bubbles with `{ id, open }`. `rail.toggle(id, open)` and
  `rail.reveal(id)` work from script, and the rail opens the item or section named by `location.hash`.
* **Views.** A **View** dropdown at the top right switches the same data between `timeline`, `list` (a plain
  bulleted list, like Wikipedia today) and `table`. Attributes on `<timeline-rail>`: `view="list"` (the view
  to start in; also set when the reader chooses), `views="timeline,table"` (which views to offer, in order),
  `switcher="false"` (no button), `table-columns="date, text"` (columns of the table: `date`, `title`, `text`,
  `image`; by default those that have data). The button is hidden when only one view is offered. Script:
  `rail.view`, `rail.views`, and a `timeline-view` event with `{ view }`. Open and closed items are kept across views.
  `demo/views.html` shows it, with a before (list) and after (timeline) side by side.
* **Your own views.** A view is `{ label, render( model, ctx ) }`; `render` returns a DOM node.
  `rail.addView( id, def )` adds it to one rail, `TimelineRail.registerView( id, def )` to every rail
  (and replaces a built-in one of the same id, so you can also redo the list or the table).

  ```js
  rail.addView( 'cards', { label: 'Cards', render( model, { h, flatten } ) {
      const box = h( 'div' );
      for ( const { node } of flatten( model.columns[ 0 ].nodes ) ) {
          box.append( h( 'p', '', null, node.date + ': ' + node.title ), node.content() );
      }
      return box;
  } } );
  ```

  `model.columns` is `[ { title, nodes } ]` (one column, no title, unless the rail has `<timeline-column>`s).
  A node is `{ kind: 'item' | 'section', id, date, title, summary, text, content(), image, events, children }`
  (`text` is plain, `content()` a fresh fragment with its links, `image` is `{ src, alt, width, caption }`,
  `events` are the events on one dot, `children` the sub items or the items of a section).
  `ctx` is `{ h( tag, class, attrs, ...kids ), flatten( nodes ) → [ { node, depth, parent } ], rail }`.
* **Theming.** Colours are CSS custom properties (`--color-progressive`, `--color-base`, ...) with light
  fallbacks; they pass through the shadow root, so set them on any ancestor. `src/theme.css` has Wikipedia's
  light and dark values.
* **Editing the children later** re-draws the timeline (a MutationObserver); open and closed
  states are kept by `id`, or by position when there is none.
* **The stylesheet** is generated: `src/timeline.css.js` is a copy of `prototype/timeline.css`,
  refreshed by `python3 tools/sync_css.py` (also run by `tools/build.py`). Do not edit it.
* **Limits.** The data elements are read, not displayed, so the text is not found by in-page
  search from the light DOM before it renders, and without JavaScript nothing shows. The wikitext
  template does not have that limit.
