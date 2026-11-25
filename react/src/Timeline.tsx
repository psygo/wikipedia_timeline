import {
  Children, createContext, isValidElement, useCallback, useContext, useEffect, useId, useMemo, useReducer, useRef, useState,
  type KeyboardEvent, type MouseEvent, type ReactNode,
} from 'react';

/*
 * TimelineRail for React. Same markup and class names as the Wikipedia template, so the one
 * stylesheet (src/timeline.css, copied from prototype/timeline.css) styles both.
 *
 *   <TimelineRail>
 *     <TimelineItem date="1612" title="The Go academy">The Tokugawa shogunate ...</TimelineItem>
 *     <TimelineSection title="Modern era" id="modern">
 *       <TimelineItem date="2016" title="AlphaGo" image="a.jpg" caption="Game 4">...</TimelineItem>
 *     </TimelineSection>
 *   </TimelineRail>
 *
 * Props mirror the template's parameters (text is the children; sub timelines go in `sub`;
 * several events on one dot go in `events`). Each item and section is collapsible by clicking
 * its row (or Enter/Space); `collapsed` is the initial state, `open`/`onOpenChange` control it.
 * Double-click an item's dot: collapse or expand every item of the timeline. Double-click a
 * section's dot: keep it open and close its sibling sections.
 */

// ---------------------------------------------------------------- bulk commands (double-click)
// A bus carries the bulk command of a double-click and a registry of the open state of its
// members, so the one that was double-clicked can decide between "close the others" and "open all".
type Command =
  | { n: number; kind: 'all'; open: boolean }
  | { n: number; kind: 'only'; keep: string; open: boolean }
  | { n: 0; kind: 'none' };
type Send = { kind: 'all'; open: boolean } | { kind: 'only'; keep: string; open: boolean };
interface Bus { command: Command; send: (c: Send) => void; states: Map<string, boolean> }

function useBus(): Bus {
  const [command, dispatch] = useReducer((prev: Command, c: Send): Command => ({ ...c, n: prev.n + 1 }), { n: 0, kind: 'none' } as Command);
  const states = useRef(new Map<string, boolean>()).current;
  return useMemo(() => ({ command, send: dispatch, states }), [command, states]);
}

/** The whole timeline (rail or column): "collapse/expand all items" commands. */
const RootBus = createContext<Bus | null>(null);
/** One list: "keep this section, close the others" commands. */
const ListBus = createContext<Bus | null>(null);

/** Keep a member's open state in the registry of its bus. */
function useRegister(bus: Bus | null, key: string, open: boolean, active = true) {
  useEffect(() => {
    if (!bus || !active) return;
    bus.states.set(key, open);
    return () => { bus.states.delete(key); };
  }, [bus, key, open, active]);
}

function useOpen(initial: boolean, controlled?: boolean, onChange?: (open: boolean) => void) {
  const [state, setState] = useState(initial);
  const open = controlled ?? state;
  const set = useCallback((v: boolean) => { setState(v); onChange?.(v); }, [onChange]);
  return [open, set] as const;
}

// ---------------------------------------------------------------- events
export interface EventData {
  title?: ReactNode;
  /** The text; the same as children on TimelineItem. */
  text?: ReactNode;
  image?: string;
  imageAlt?: string;
  /** Width of the picture in px. */
  imageWidth?: number;
  caption?: ReactNode;
}
export interface TimelineEventProps extends EventData { children?: ReactNode }

export function TimelineEvent({ title, text, children, image, imageAlt = '', imageWidth, caption }: TimelineEventProps) {
  const body = text ?? children;
  return (
    <div className="wt-timeline__event">
      <span className="wt-timeline__title">{title}</span>
      {body ? <div className="wt-timeline__text">{body}</div> : null}
      {image ? (
        <span className="wt-timeline__image">
          <img src={image} alt={imageAlt} width={imageWidth} loading="lazy" />
          {caption ? <><br />{caption}</> : null}
        </span>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------- rows
function useRowHandlers(toggle: () => void, onDouble: () => void, dotOnly = false) {
  return {
    onClick: (e: MouseEvent) => {
      const t = e.target as HTMLElement;
      if (t.closest('a[href]') || t.closest('.wt-timeline__section-extra')) return;
      if (dotOnly && !t.closest('.wt-timeline__dot')) return;   // a section reacts to its dot only
      toggle();
    },
    onKeyDown: (e: KeyboardEvent) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      if ((e.target as HTMLElement).closest('a[href]')) return;
      e.preventDefault();
      toggle();
    },
    onDoubleClick: (e: MouseEvent) => {
      if (dotOnly && !(e.target as HTMLElement).closest('.wt-timeline__dot')) return;
      e.preventDefault();
      onDouble();
    },
  };
}

// ---------------------------------------------------------------- item
export interface TimelineItemProps extends EventData {
  date: ReactNode;
  /** Shown beside the date when the item is closed. */
  summary?: ReactNode;
  /** Initial state: closed. */
  collapsed?: boolean;
  /** Controlled state. */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  /** false: always open, the title shows in the body. */
  collapsible?: boolean;
  /** Last item of the timeline: the rail stops at its dot. */
  last?: boolean;
  id?: string;
  /** Several events on the same dot; replaces text/image. */
  events?: EventData[];
  /** A nested timeline: TimelineItems (or sections). */
  sub?: ReactNode;
  /** The text. */
  children?: ReactNode;
}

export function TimelineItem(props: TimelineItemProps) {
  const { date, title, summary, collapsed, open: controlled, onOpenChange, collapsible = true, last, id, events, sub, children } = props;
  const [open, setOpen] = useOpen(!collapsed, controlled, onOpenChange);
  const root = useContext(RootBus);
  const key = useId();
  const hasContent = Boolean(title || props.text || children || props.image || events?.length || sub);
  const canCollapse = collapsible && hasContent;

  useRegister(root, key, open, collapsible && Boolean(title || props.text || children || props.image || events?.length || sub));
  // "Collapse/expand all" from the dot of any item.
  const seen = useRef(0);
  useEffect(() => {
    const c = root?.command;
    if (!c || c.n === seen.current) return;
    seen.current = c.n;
    if (c.kind === 'all' && canCollapse) setOpen(c.open);
  }, [root?.command, canCollapse, setOpen]);

  const h = useRowHandlers(() => setOpen(!open), () => {
    if (!root) return;
    // Same rule as the template's script: if any item is open, close all; otherwise open all.
    const anyOpen = [...root.states.values()].some(Boolean);
    root.send({ kind: 'all', open: !anyOpen });
  });

  const eventList = events?.length ? events : [{ title, text: props.text, image: props.image, imageAlt: props.imageAlt, imageWidth: props.imageWidth, caption: props.caption }];
  const body = (
    <>
      <div className="wt-timeline__events">
        {eventList.map((e, i) => (
          <TimelineEvent key={i} {...e} title={canCollapse ? undefined : e.title} text={e.text ?? (i === 0 && !events?.length ? children : undefined)} />
        ))}
      </div>
      {sub ? <TimelineList className="wt-timeline wt-timeline--sub">{sub}</TimelineList> : null}
    </>
  );
  const cls = 'wt-timeline__item'
    + (canCollapse ? ' wt-timeline__item--collapsible mw-collapsible' : '')
    + (canCollapse && !open ? ' mw-collapsed' : '')
    + (last ? ' wt-timeline__item--last' : '');

  if (!canCollapse) {
    return <li className={cls} id={id}><span className="wt-timeline__date">{date}</span>{body}</li>;
  }
  return (
    <li className={cls} id={id}>
      <div className="wt-timeline__row" role="button" tabIndex={0} aria-expanded={open} {...h}>
        <span className="wt-timeline__date">{date}</span>
        {events?.length
          ? <span className="wt-timeline__peek">{summary ?? title}</span>
          : <span className="wt-timeline__peek wt-timeline__peek--title">{title}</span>}
      </div>
      <div className="wt-timeline__body" hidden={!open}>{body}</div>
    </li>
  );
}

// ---------------------------------------------------------------- section
export interface TimelineSectionProps extends Omit<EventData, 'title'> {
  title: ReactNode;
  collapsed?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  id?: string;
  /** Introduction in the row, beside the title (the template's text=). */
  intro?: ReactNode;
  /** Items and sections, nested to any depth. */
  children?: ReactNode;
}

export function TimelineSection({ title, collapsed, open: controlled, onOpenChange, id, intro, text, image, imageAlt, imageWidth, caption, children }: TimelineSectionProps) {
  const [open, setOpen] = useOpen(!collapsed, controlled, onOpenChange);
  const list = useContext(ListBus);
  const me = useId();

  const seen = useRef(0);
  useEffect(() => {
    const c = list?.command;
    if (!c || c.n === seen.current) return;
    seen.current = c.n;
    if (c.kind === 'only') setOpen(c.keep === me ? true : c.open);
  }, [list?.command, me, setOpen]);

  useRegister(list, me, open);
  const h = useRowHandlers(() => setOpen(!open), () => {
    // Keep this section open and close its siblings; if they are all closed already, open them.
    if (!list) return;
    const someOpen = [...list.states].some(([k, v]) => k !== me && v);
    list.send({ kind: 'only', keep: me, open: !someOpen });
  }, true);

  const extraBody = text ?? intro;
  const extra = extraBody || image
    ? <div className="wt-timeline__section-extra"><TimelineEvent text={extraBody} image={image} imageAlt={imageAlt} imageWidth={imageWidth} caption={caption} /></div>
    : null;
  return (
    <li className={'wt-timeline__item wt-timeline__item--section mw-collapsible' + (open ? '' : ' mw-collapsed')}>
      <div className="wt-timeline__row" id={id} role="button" tabIndex={0} aria-expanded={open} {...h}>
        <span className="wt-timeline__dot" aria-hidden="true" />
        <span className="wt-timeline__section-title">{title}</span>
        {extra}
      </div>
      <div className="wt-timeline__body" hidden={!open}>
        <TimelineList className="wt-timeline wt-timeline--section">{children}</TimelineList>
      </div>
    </li>
  );
}

export function TimelineGap() {
  return <li className="wt-timeline__item wt-timeline__item--gap" aria-hidden="true" />;
}

// ---------------------------------------------------------------- lists, columns, rail
function TimelineList({ className, children }: { className: string; children?: ReactNode }) {
  const bus = useBus();
  return (
    <ListBus.Provider value={bus}>
      <ol className={className}>{children}</ol>
    </ListBus.Provider>
  );
}

export interface TimelineColumnProps { title?: ReactNode; children?: ReactNode }

/** One timeline of several side by side (children of a TimelineRail). */
export function TimelineColumn({ title, children }: TimelineColumnProps) {
  const root = useBus();
  return (
    <RootBus.Provider value={root}>
      <div className="wt-timelines__col">
        {title ? <div className="wt-timeline__heading">{title}</div> : null}
        <TimelineList className="wt-timeline">{children}</TimelineList>
      </div>
    </RootBus.Provider>
  );
}

export interface TimelineRailProps {
  /** Align the dots of side-by-side columns (TimelineColumn children), at 640 px and wider. */
  grouped?: boolean;
  /** TimelineItems and TimelineSections, or TimelineColumns for timelines side by side. */
  children?: ReactNode;
}

export function TimelineRail({ grouped, children }: TimelineRailProps) {
  const root = useBus();
  const isColumns = Children.toArray(children).some((c) => isValidElement(c) && c.type === TimelineColumn);
  if (isColumns) {
    return <div className={'wt-timelines' + (grouped ? ' wt-timelines--grouped' : '')}>{children}</div>;
  }
  return (
    <RootBus.Provider value={root}>
      <TimelineList className="wt-timeline">{children}</TimelineList>
    </RootBus.Provider>
  );
}
