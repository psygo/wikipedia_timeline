/*
 * Views of <timeline-rail>: the same data drawn as a timeline, a plain bulleted list or a table.
 *
 * A view is { label, render( model, ctx ) } and render returns a DOM node. The model is the
 * data the rail read from its children, the same for every view:
 *
 *   model.columns   [ { title, nodes } ]   one entry, with an empty title, unless the rail has
 *                                          <timeline-column>s
 *   node            { kind: 'item' | 'section', id, key, date, title, summary, text,
 *                     content(), image, events, children }
 *     text          the text as a plain string
 *     content()     a fresh DocumentFragment with the text and its links
 *     image         { src, alt, width, caption } or null
 *     events        for an item with several events on one dot: [ { title, text, content(), image } ]
 *     children      the sub items of an item, or the items and sections of a section
 *
 * ctx = { h( tag, class, attrs, ...children ), flatten( nodes ), rail }.
 * See the README for registering your own.
 */

export const viewsCss = `
.wt-viewbar { display: flex; justify-content: flex-end; margin: 0 0 0.6em; }
.wt-viewmenu { position: relative; }
.wt-viewmenu__button {
	font: inherit; font-size: 0.875em; color: var( --color-base, #202122 ); cursor: pointer;
	padding: 0.3em 0.75em; border: 1px solid var( --border-color-base, #a2a9b1 ); border-radius: 2px;
	background: var( --background-color-interactive-subtle, #f8f9fa );
}
.wt-viewmenu__button:hover, .wt-viewmenu__button[aria-expanded="true"] { border-color: var( --color-progressive, #36c ); }
.wt-viewmenu__button:focus-visible, .wt-viewmenu__item:focus-visible { outline: 2px solid var( --color-progressive, #36c ); outline-offset: 1px; }
.wt-viewmenu__button::after { content: ''; display: inline-block; margin-left: 0.55em; vertical-align: 0.1em;
	border: 0.3em solid transparent; border-top-color: currentColor; border-bottom-width: 0; }
.wt-viewmenu__list {
	position: absolute; right: 0; z-index: 5; min-width: 100%; margin: 2px 0 0; padding: 0.25em 0; list-style: none;
	border: 1px solid var( --border-color-base, #a2a9b1 ); border-radius: 2px;
	background: var( --background-color-base, #fff ); box-shadow: 0 2px 6px rgba( 0, 0, 0, 0.2 );
}
.wt-viewmenu__list[hidden] { display: none; }
.wt-viewmenu__item {
	display: block; width: 100%; padding: 0.35em 1.8em 0.35em 1em; border: 0; background: none;
	font: inherit; font-size: 0.875em; text-align: left; white-space: nowrap; cursor: pointer; color: var( --color-base, #202122 );
}
.wt-viewmenu__item:hover { background: var( --background-color-interactive-subtle, #f8f9fa ); }
.wt-viewmenu__item[aria-checked="true"] { font-weight: bold; color: var( --color-progressive, #36c ); }
.wt-viewmenu__item[aria-checked="true"]::after { content: '\\2713'; float: right; margin-right: -1.3em; }

.wt-view { color: var( --color-base, #202122 ); line-height: 1.6; }
.wt-view a { color: var( --color-progressive, #36c ); }
.wt-view__heading { margin: 1em 0 0.3em; font-weight: bold; }
.wt-view__heading[data-level="1"] { font-size: 1.3em; border-bottom: 1px solid var( --border-color-subtle, #c8ccd1 ); }
.wt-view__heading[data-level="2"] { font-size: 1.15em; }
.wt-view__lead { margin: 0 0 0.4em; }
.wt-view__col-title { margin: 1em 0 0.3em; font-weight: bold; font-size: 1.1em; }
.wt-view-list ul { margin: 0.3em 0 0 1.6em; padding: 0; list-style: disc; }
.wt-view-list li { margin-bottom: 0.25em; }
.wt-view-list .wt-view__figure { display: block; margin: 0.3em 0; max-width: 14em; font-size: 0.875em; color: var( --color-subtle, #54595d ); }
.wt-view__figure img { display: block; max-width: 100%; height: auto; }
.wt-view-table { overflow-x: auto; }
.wt-view-table table { border-collapse: collapse; width: 100%; margin: 0.4em 0 1em; background: var( --background-color-base, #fff ); }
.wt-view-table th, .wt-view-table td { padding: 0.4em 0.6em; border: 1px solid var( --border-color-base, #a2a9b1 ); vertical-align: top; text-align: left; }
.wt-view-table thead th { background: var( --background-color-interactive-subtle, #eaecf0 ); text-align: center; }
.wt-view-table td.wt-view__date { white-space: nowrap; }
.wt-view-table td.wt-view__title { font-weight: bold; }
.wt-view-table th[colspan] { background: var( --background-color-interactive-subtle, #f8f9fa ); }
.wt-view-table .wt-view__sub { padding-left: 1.6em; }
.wt-view-table .wt-view__sub::before { content: '\\21B3\\00A0'; color: var( --color-subtle, #54595d ); }
.wt-view-table .wt-view__figure { max-width: 10em; font-size: 0.875em; color: var( --color-subtle, #54595d ); }
`;

const figure = ( h, img ) => !img ? document.createDocumentFragment() : h( 'span', 'wt-view__figure', null,
	h( 'img', '', { src: img.src, alt: img.alt, width: img.width || null, loading: 'lazy' } ),
	img.caption ? h( 'span', '', null, img.caption ) : null );

// ---------------------------------------------------------------------- list
function listView( model, { h } ) {
	const eventLi = ( ev ) => h( 'li', '', null,
		ev.title ? h( 'b', '', null, ev.title ) : null, ev.title && ev.text ? '. ' : null, ev.content(), figure( h, ev.image ) );

	const items = ( nodes ) => {
		const ul = h( 'ul' );
		for ( const n of nodes ) {
			const li = h( 'li' );
			if ( n.date ) { li.append( h( 'b', '', null, n.date ), n.title || n.text || n.events.length ? ' – ' : '' ); }
			if ( n.events.length ) {
				li.append( h( 'ul', '', null, ...n.events.map( eventLi ) ) );
			} else {
				if ( n.title ) { li.append( h( 'b', '', null, n.title ), n.text ? '. ' : '' ); }
				li.append( n.content(), figure( h, n.image ) );
			}
			const sub = n.children.filter( ( c ) => c.kind === 'item' );
			if ( sub.length ) { li.append( items( sub ) ); }
			ul.append( li );
		}
		return ul;
	};
	const walk = ( nodes, level, into ) => {
		let run = [];
		const flush = () => { if ( run.length ) { into.append( items( run ) ); run = []; } };
		for ( const n of nodes ) {
			if ( n.kind === 'section' ) {
				flush();
				into.append( h( 'div', 'wt-view__heading', { role: 'heading', 'aria-level': String( Math.min( level + 2, 6 ) ), 'data-level': String( Math.min( level, 3 ) ) }, n.title ) );
				if ( n.text || n.image ) { into.append( h( 'div', 'wt-view__lead', null, n.content(), figure( h, n.image ) ) ); }
				walk( n.children, level + 1, into );
			} else if ( n.kind === 'item' ) {
				run.push( n );
			}
		}
		flush();
	};
	const root = h( 'div', 'wt-view wt-view-list' );
	for ( const col of model.columns ) {
		if ( col.title ) { root.append( h( 'div', 'wt-view__col-title', null, col.title ) ); }
		walk( col.nodes, 1, root );
	}
	return root;
}

// ---------------------------------------------------------------------- table
const COLUMN_LABELS = { date: 'Date', title: 'Title', text: 'Description', image: 'Image' };

function tableView( model, { h, flatten, rail } ) {
	const root = h( 'div', 'wt-view wt-view-table' );
	// table-columns="date, text" picks and orders the columns (date, title, text, image).
	const wanted = ( rail.getAttribute( 'table-columns' ) || '' ).split( /[\s,]+/ ).filter( ( c ) => COLUMN_LABELS[ c ] );
	for ( const col of model.columns ) {
		const rows = flatten( col.nodes );
		const leaves = rows.filter( ( r ) => r.node.kind === 'item' );
		const has = {
			date: leaves.some( ( r ) => r.node.date ),
			title: leaves.some( ( r ) => r.node.title || r.node.events.some( ( e ) => e.title ) ),
			text: leaves.some( ( r ) => r.node.text || r.node.events.some( ( e ) => e.text ) ),
			image: leaves.some( ( r ) => r.node.image || r.node.events.some( ( e ) => e.image ) ),
		};
		const cols = wanted.length ? wanted : Object.keys( COLUMN_LABELS ).filter( ( c ) => has[ c ] );
		if ( !cols.length ) { continue; }
		const cell = ( kind, src, sub ) => {
			if ( kind === 'date' ) { return h( 'td', 'wt-view__date', null, src.date ); }
			if ( kind === 'title' ) { return h( 'td', 'wt-view__title' + ( sub ? ' wt-view__sub' : '' ), null, src.title ); }
			if ( kind === 'image' ) { return h( 'td', '', null, figure( h, src.image ) ); }
			return h( 'td', ( sub && !cols.includes( 'title' ) ) ? 'wt-view__sub' : '', null, src.content() );
		};

		const table = h( 'table' );
		table.append( h( 'thead', '', null, h( 'tr', '', null, ...cols.map( ( c ) => h( 'th', '', { scope: 'col' }, COLUMN_LABELS[ c ] ) ) ) ) );
		const body = h( 'tbody' );
		for ( const { node, depth, parent } of rows ) {
			if ( node.kind === 'section' ) {
				const th = h( 'th', '', { colspan: String( cols.length ), scope: 'colgroup' }, node.title );
				if ( depth ) { th.style.paddingLeft = ( 0.6 + depth * 1.2 ) + 'em'; }
				if ( node.text ) { th.append( h( 'div', '', { style: 'font-weight:normal' }, node.content() ) ); }
				body.append( h( 'tr', '', null, th ) );
				continue;
			}
			const sub = !!parent && parent.kind === 'item';
			if ( node.events.length ) {
				node.events.forEach( ( ev, i ) => {
					const tr = h( 'tr' );
					for ( const c of cols ) {
						if ( c === 'date' ) {
							if ( i === 0 ) { const td = cell( 'date', node ); td.rowSpan = node.events.length; tr.append( td ); }
						} else { tr.append( cell( c, ev, sub ) ); }
					}
					body.append( tr );
				} );
			} else {
				body.append( h( 'tr', '', null, ...cols.map( ( c ) => cell( c, node, sub ) ) ) );
			}
		}
		table.append( body );
		if ( col.title ) { root.append( h( 'div', 'wt-view__col-title', null, col.title ) ); }
		root.append( h( 'div', '', { style: 'overflow-x:auto' }, table ) );
	}
	return root;
}

/** The views every rail offers, in menu order. 'timeline' is drawn by the rail itself. */
export const builtinViews = {
	timeline: { label: 'Timeline' },
	list: { label: 'List', render: listView },
	table: { label: 'Table', render: tableView },
};
