/**
 * The data of a timeline, read from the same elements the timeline draws:
 *   const items = <><TimelineItem date="1612" title="...">text</TimelineItem>...</>;
 *   <TimelineRail>{items}</TimelineRail>  <OutlineList>{items}</OutlineList>
 * The list and the table do not render those components; they read their props.
 */
import { Children, Fragment, isValidElement, type ReactElement, type ReactNode } from 'react';
import {
  TimelineItem, TimelineSection, TimelineColumn,
  type EventData, type TimelineItemProps, type TimelineSectionProps, type TimelineColumnProps,
} from './Timeline';

export interface ViewImage { src: string; alt: string; width?: number; caption?: ReactNode }
export interface ViewEvent { title?: ReactNode; text?: ReactNode; image?: ViewImage }
export interface ViewNode extends ViewEvent {
  kind: 'item' | 'section';
  id?: string;
  date?: ReactNode;
  summary?: ReactNode;
  /** several events on one dot */
  events: ViewEvent[];
  /** sub items of an item, or the items and sections of a section */
  children: ViewNode[];
}
export interface ViewColumn { title?: ReactNode; nodes: ViewNode[] }

/** Children as a flat array, fragments opened. */
function flat(children: ReactNode): ReactNode[] {
  return Children.toArray(children).flatMap((c) =>
    isValidElement(c) && c.type === Fragment ? flat((c as ReactElement<{ children?: ReactNode }>).props.children) : [c]);
}

const event = (d: EventData & { children?: ReactNode }): ViewEvent => ({
  title: d.title,
  text: d.text ?? d.children,
  image: d.image ? { src: d.image, alt: d.imageAlt ?? '', width: d.imageWidth, caption: d.caption } : undefined,
});

function readNodes(children: ReactNode): ViewNode[] {
  const out: ViewNode[] = [];
  for (const c of flat(children)) {
    if (!isValidElement(c)) continue;
    if (c.type === TimelineItem) {
      const p = c.props as TimelineItemProps;
      out.push({ kind: 'item', id: p.id, date: p.date, summary: p.summary, ...event(p),
        events: (p.events ?? []).map((e) => event(e)), children: readNodes(p.sub) });
    } else if (c.type === TimelineSection) {
      const p = c.props as TimelineSectionProps;
      out.push({ kind: 'section', id: p.id, ...event({ ...p, title: p.title, text: p.intro ?? p.text }),
        events: [], children: readNodes(p.children) });
    }
  }
  return out;
}

/** One column, or one per TimelineColumn. */
export function readModel(children: ReactNode): ViewColumn[] {
  const cols = flat(children).filter((c): c is ReactElement<TimelineColumnProps> => isValidElement(c) && c.type === TimelineColumn);
  return cols.length
    ? cols.map((c) => ({ title: c.props.title, nodes: readNodes(c.props.children) }))
    : [{ nodes: readNodes(children) }];
}

export interface FlatRow { node: ViewNode; depth: number; parent: ViewNode | null }
/** The nodes in reading order. */
export function flatten(nodes: ViewNode[], depth = 0, parent: ViewNode | null = null, out: FlatRow[] = []): FlatRow[] {
  for (const n of nodes) { out.push({ node: n, depth, parent }); flatten(n.children, depth + 1, n, out); }
  return out;
}
