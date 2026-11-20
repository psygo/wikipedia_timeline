import { Children, isValidElement, useEffect, useId, useRef, useState, type KeyboardEvent, type ReactNode } from 'react';

export interface ViewProps {
  /** The name in the menu. */
  label: string;
  /** The view shown first. */
  default?: boolean;
  children?: ReactNode;
}

/** One view of a ViewSwitcher: any content. */
export function View({ children }: ViewProps) {
  return <>{children}</>;
}

export interface ViewSwitcherProps {
  /** <View>s. */
  children?: ReactNode;
  /** The label of the view shown first (or a View with the default prop). Without either, the first. */
  defaultView?: string;
  /** Controlled: the label of the current view. */
  view?: string;
  onViewChange?: (label: string) => void;
}

/**
 * A "View" dropdown at the top right that shows one of its <View>s at a time. It knows nothing about
 * timelines. The views stay mounted while hidden, so a timeline keeps which items are open.
 */
export function ViewSwitcher({ children, defaultView, view: controlled, onViewChange }: ViewSwitcherProps) {
  const views = Children.toArray(children).filter((c): c is React.ReactElement<ViewProps> => isValidElement(c) && c.type === View);
  const labels = views.map((v) => v.props.label);
  const first = labels.indexOf(defaultView ?? '') >= 0 ? defaultView! : (views.find((v) => v.props.default)?.props.label ?? labels[0]);
  const [state, setState] = useState(first);
  const current = labels.includes(controlled ?? '') ? controlled! : (labels.includes(state) ? state : first);
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const items = useRef<(HTMLButtonElement | null)[]>([]);
  const button = useRef<HTMLButtonElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;
    const away = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('click', away);
    items.current[labels.indexOf(current)]?.focus();
    return () => document.removeEventListener('click', away);
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  const choose = (label: string) => {
    setState(label); setOpen(false); button.current?.focus();
    if (label !== current) onViewChange?.(label);
  };
  const onKey = (e: KeyboardEvent) => {
    const at = items.current.findIndex((b) => b === document.activeElement);
    const n = labels.length;
    const go = ({ ArrowDown: (at + 1) % n, ArrowUp: (at - 1 + n) % n, Home: 0, End: n - 1 } as Record<string, number>)[e.key];
    if (go !== undefined) { e.preventDefault(); items.current[go]?.focus(); }
    else if (e.key === 'Escape' || e.key === 'Tab') { setOpen(false); if (e.key === 'Escape') button.current?.focus(); }
  };

  if (views.length < 2) return <>{views}</>;
  return (
    <div className="tlv-switcher" ref={box}>
      <div className="tlv-switcher__bar">
        <div className="tlv-switcher__menu">
          <button ref={button} type="button" className="tlv-switcher__button" aria-haspopup="menu" aria-expanded={open} aria-controls={menuId}
            onClick={() => setOpen(!open)} onKeyDown={(e) => { if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); } }}>
            View: {current}
          </button>
          <div id={menuId} className="tlv-switcher__list" role="menu" aria-label="View" hidden={!open} onKeyDown={onKey}>
            {labels.map((l, i) => (
              <button key={l} ref={(el) => { items.current[i] = el; }} type="button" role="menuitemradio" aria-checked={l === current}
                tabIndex={-1} className="tlv-switcher__item" onClick={() => choose(l)}>{l}</button>
            ))}
          </div>
        </div>
      </div>
      {views.map((v) => <div key={v.props.label} hidden={v.props.label !== current}>{v}</div>)}
    </div>
  );
}
