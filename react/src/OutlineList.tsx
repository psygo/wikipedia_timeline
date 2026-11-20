import type { ReactNode } from 'react';
import { readModel, type ViewEvent, type ViewImage, type ViewNode } from './model';

export function Figure({ image }: { image?: ViewImage }) {
  if (!image) return null;
  return (
    <span className="tlv__figure">
      <img src={image.src} alt={image.alt} width={image.width} loading="lazy" />
      {image.caption ? <span>{image.caption}</span> : null}
    </span>
  );
}

function EventLi({ ev }: { ev: ViewEvent }) {
  return <li>{ev.title ? <b>{ev.title}</b> : null}{ev.title && ev.text ? '. ' : null}{ev.text}<Figure image={ev.image} /></li>;
}

function Items({ nodes }: { nodes: ViewNode[] }) {
  return (
    <ul>
      {nodes.map((n, i) => {
        const sub = n.children.filter((c) => c.kind === 'item');
        return (
          <li key={i}>
            {n.date ? <><b>{n.date}</b>{n.title || n.text || n.events.length ? ' – ' : ''}</> : null}
            {n.events.length ? (
              <ul>{n.events.map((e, k) => <EventLi key={k} ev={e} />)}</ul>
            ) : (
              <>{n.title ? <><b>{n.title}</b>{n.text ? '. ' : ''}</> : null}{n.text}<Figure image={n.image} /></>
            )}
            {sub.length ? <Items nodes={sub} /> : null}
          </li>
        );
      })}
    </ul>
  );
}

function Walk({ nodes, level }: { nodes: ViewNode[]; level: number }) {
  const out: ReactNode[] = [];
  let run: ViewNode[] = [];
  const flush = () => { if (run.length) { out.push(<Items key={'r' + out.length} nodes={run} />); run = []; } };
  nodes.forEach((n, i) => {
    if (n.kind === 'section') {
      flush();
      out.push(<div key={'s' + i} className="tlv__heading" role="heading" aria-level={Math.min(level + 2, 6)} data-level={Math.min(level, 3)}>{n.title}</div>);
      if (n.text || n.image) out.push(<div key={'t' + i} className="tlv__lead">{n.text}<Figure image={n.image} /></div>);
      out.push(<Walk key={'w' + i} nodes={n.children} level={level + 1} />);
    } else run.push(n);
  });
  flush();
  return <>{out}</>;
}

export interface OutlineListProps {
  /** The same TimelineItems / TimelineSections / TimelineColumns a TimelineRail takes. */
  children?: ReactNode;
}

/** The data as a plain bulleted list, the way an article has it today. */
export function OutlineList({ children }: OutlineListProps) {
  return (
    <div className="tlv tlv-list">
      {readModel(children).map((col, i) => (
        <div key={i}>
          {col.title ? <div className="tlv__col-title">{col.title}</div> : null}
          <Walk nodes={col.nodes} level={1} />
        </div>
      ))}
    </div>
  );
}
