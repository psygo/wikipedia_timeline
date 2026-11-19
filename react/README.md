# TimelineRail for React

The vertical timeline of this project as React components. Same markup and class names as the
Wikipedia template, styled by the same stylesheet (`prototype/timeline.css`).

```tsx
import { TimelineRail, TimelineItem, TimelineSection } from 'timeline-rail-react';
import 'timeline-rail-react/style.css';
import 'timeline-rail-react/theme.css';   // optional: colour tokens, light and dark

<TimelineRail>
  <TimelineItem date="1612" title="The Go academy">The Tokugawa shogunate ...</TimelineItem>
  <TimelineSection title="Modern era" id="modern">
    <TimelineItem date="2016" title="AlphaGo" image="a.jpg" caption="Game 4">...</TimelineItem>
  </TimelineSection>
</TimelineRail>
```

Develop: `npm install`, then `npm run dev` (demo app in `demo/`), `npm run typecheck`, `npm run build` (library into `dist/`).

| Component | Props |
|---|---|
| `TimelineRail` | `grouped`; children are items and sections, or `TimelineColumn`s for timelines side by side |
| `TimelineItem` | `date`, `title`, `summary`, `image`, `imageAlt`, `imageWidth`, `caption`, `id`, `collapsed`, `open` + `onOpenChange` (controlled), `collapsible={false}`, `last`, `events` (several events on one dot), `sub` (a nested timeline); the text is the children |
| `TimelineSection` | `title`, `id`, `collapsed`, `open` + `onOpenChange`, `intro` or `text`, `image`, `caption`; children are items and sections, to any depth |
| `TimelineColumn` | `title`; items |
| `TimelineGap` | none; fills a slot so grouped columns line up |
| `TimelineEvent` | `title`, `text`, `image`, `imageAlt`, `imageWidth`, `caption` (used inside; exported for custom layouts) |

* **Interaction.** Same as the template: click or Enter on a row toggles it; double-click an item's
  dot to collapse or expand all items of that timeline; double-click a section's dot to keep it open
  and close its sibling sections.
* **Not implemented:** opening an item or section from `location.hash` (the web component and the
  wiki user script do this).
* **Theming.** Colours come from CSS custom properties with light fallbacks (see `src/theme.css`).
  The styles are global (class names `wt-timeline*`), not scoped; use the web component if the page's
  own CSS might clash.
* **The stylesheet** `src/timeline.css` is generated from `prototype/timeline.css` by
  `python3 tools/sync_css.py` (also run by `tools/build.py`). Do not edit it.
* Each timeline renders its items as it is given them, so very long ones (hundreds of items) are
  better paged or virtualised by the host app.
