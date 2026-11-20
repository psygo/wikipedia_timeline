import type { ReactNode } from 'react';
import { flatten, readModel, type ViewNode } from './model';
import { Figure } from './OutlineList';

export type TableColumn = 'date' | 'title' | 'text' | 'image';
const LABELS: Record<TableColumn, string> = { date: 'Date', title: 'Title', text: 'Description', image: 'Image' };

export interface OutlineTableProps {
  /** The same TimelineItems / TimelineSections / TimelineColumns a TimelineRail takes. */
  children?: ReactNode;
  /** Which columns, in this order; by default those that have data. */
  columns?: TableColumn[];
}

/** The data as a table. */
export function OutlineTable({ children, columns }: OutlineTableProps) {
  return (
    <div className="tlv tlv-table">
      {readModel(children).map((col, ci) => {
        const rows = flatten(col.nodes);
        const leaves = rows.filter((r) => r.node.kind === 'item').map((r) => r.node);
        const any = (f: (x: { title?: ReactNode; text?: ReactNode; image?: unknown }) => unknown) =>
          leaves.some((n) => f(n) || n.events.some(f));
        const has: Record<TableColumn, boolean> = {
          date: leaves.some((n) => n.date), title: any((x) => x.title), text: any((x) => x.text), image: any((x) => x.image),
        };
        const cols = columns ?? (Object.keys(LABELS) as TableColumn[]).filter((c) => has[c]);
        if (!cols.length) return null;
        const cell = (c: TableColumn, src: ViewNode | NonNullable<ViewNode['events'][number]>, sub: boolean, key: string) => {
          if (c === 'date') return <td key={key} className="tlv__date">{(src as ViewNode).date}</td>;
          if (c === 'title') return <td key={key} className={'tlv__title' + (sub ? ' tlv__sub' : '')}>{src.title}</td>;
          if (c === 'image') return <td key={key}><Figure image={src.image} /></td>;
          return <td key={key} className={sub && !cols.includes('title') ? 'tlv__sub' : undefined}>{src.text}</td>;
        };
        return (
          <div key={ci}>
            {col.title ? <div className="tlv__col-title">{col.title}</div> : null}
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead><tr>{cols.map((c) => <th key={c} scope="col">{LABELS[c]}</th>)}</tr></thead>
                <tbody>
                  {rows.map(({ node, depth, parent }, i) => {
                    if (node.kind === 'section') {
                      return (
                        <tr key={i}>
                          <th colSpan={cols.length} scope="colgroup" style={depth ? { paddingLeft: `${0.6 + depth * 1.2}em` } : undefined}>
                            {node.title}
                            {node.text ? <div style={{ fontWeight: 'normal' }}>{node.text}</div> : null}
                          </th>
                        </tr>
                      );
                    }
                    const sub = !!parent && parent.kind === 'item';
                    if (node.events.length) {
                      return node.events.map((ev, k) => (
                        <tr key={`${i}-${k}`}>
                          {cols.map((c) => c === 'date'
                            ? (k === 0 ? <td key={c} className="tlv__date" rowSpan={node.events.length}>{node.date}</td> : null)
                            : cell(c, ev, sub, c))}
                        </tr>
                      ));
                    }
                    return <tr key={i}>{cols.map((c) => cell(c, node, sub, c))}</tr>;
                  })}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}
