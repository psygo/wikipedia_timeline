/*
 * <timeline-rail>: a vertical timeline as a custom element, no dependencies.
 *
 *   <timeline-rail>
 *     <timeline-item date="1612" title="The Go academy">The Tokugawa shogunate ...</timeline-item>
 *     <timeline-section title="Modern era" id="modern">
 *       <timeline-item date="2016" title="AlphaGo" image="alphago.jpg" caption="Game 4">...</timeline-item>
 *     </timeline-section>
 *   </timeline-rail>
 *
 * The child elements are only data: the rail reads them and draws the timeline in its shadow
 * root with the stylesheet of this project (prototype/timeline.css, same class names as the
 * Wikipedia template). Colours come from CSS custom properties with light fallbacks, so the
 * host page themes it (see theme.css).
 *
 * <timeline-item>     date, title, summary, image, image-alt, image-width, caption, id,
 *                     collapsed, collapsible="false", last. Content: the text (any HTML).
 *                     Nested <timeline-item>s become a sub timeline; <timeline-event>s
 *                     (title, image, ...) put several events side by side on one dot.
 * <timeline-section>  title, id, collapsed, image/caption..., text (attribute). Any other content
 *                     that is not a timeline element is the section's introduction. Children:
 *                     items and sections, nested to any depth.
 * <timeline-gap>      an empty slot, to line up dots in grouped columns.
 * <timeline-column>   title. Several of them as children of the rail place timelines side by side;
 *                     add the grouped attribute on the rail to align their dots.
 *
 * Views: a button at the top right switches the same data between a timeline, a bulleted list and
 * a table. view="list" starts in another view, views="timeline,table" limits the menu, switcher="false"
 * hides the button. TimelineRail.registerView(id, { label, render(model, ctx) }) adds views for every
 * rail, rail.addView(id, def) for one; see views.js for the model a view receives.
 *
 * Interaction: click or Enter on a row toggles it; double-click an item's dot to collapse or expand
 * every item of that timeline; double-click a section's dot to keep it open and close its sibling
 * sections. The "timeline-toggle" event bubbles with { id, open }. The rail also opens the
 * item or section named by location.hash.
 */
import baseCss from './timeline.css.js';
import { builtinViews, viewsCss } from './views.js';

// Links inside the shadow root do not see the page's link colour; use the same token.
const css = baseCss + '\n.wt-timeline a { color: var( --color-progressive, #36c ); }\n' + viewsCss;

const registry = new Map( Object.entries( builtinViews ) );
const DATA_TAGS = ['timeline-item', 'timeline-section', 'timeline-gap', 'timeline-column', 'timeline-event'];
let sheet = null;
if ( typeof CSSStyleSheet !== 'undefined' && 'replaceSync' in CSSStyleSheet.prototype ) {
	sheet = new CSSStyleSheet();
	sheet.replaceSync( css );
}

function h( tag, cls, attrs, ...kids ) {
	const el = document.createElement( tag );
	if ( cls ) { el.className = cls; }
	for ( const k in attrs || {} ) { if ( attrs[ k ] != null ) { el.setAttribute( k, attrs[ k ] ); } }
	for ( const k of kids ) { if ( k ) { el.append( k ); } }
	return el;
}
const isTag = ( n, t ) => n.nodeType === 1 && n.localName === t;
const blank = ( n ) => n.nodeType === 8 || ( n.nodeType === 3 && !n.textContent.trim() );
const bool = ( el, name ) => el.hasAttribute( name ) && el.getAttribute( name ) !== 'false';

export class TimelineRail extends HTMLElement {
	#root; #open = new Map(); #pending = false; #mo; #own = new Map(); #menuOpen = false; #refocus = false;
	static get observedAttributes() { return [ 'grouped', 'view', 'views', 'switcher' ]; }

	/** Add a view to every rail: def = { label, render( model, ctx ) returning a Node }. */
	static registerView( id, def ) { registry.set( id, def ); }

	constructor() {
		super();
		this.#root = this.attachShadow( { mode: 'open' } );
		if ( sheet ) { this.#root.adoptedStyleSheets = [ sheet ]; }
		else { this.#root.append( h( 'style' ) ); this.#root.firstChild.textContent = css; }
		this.#mo = new MutationObserver( () => this.#schedule() );
	}

	connectedCallback() {
		this.#mo.observe( this, { childList: true, subtree: true, characterData: true, attributes: true } );
		window.addEventListener( 'hashchange', this.#hash );
		document.addEventListener( 'click', this.#outside );
		this.#render();
		this.#hash();
	}
	disconnectedCallback() {
		this.#mo.disconnect();
		window.removeEventListener( 'hashchange', this.#hash );
		document.removeEventListener( 'click', this.#outside );
	}
	attributeChangedCallback() { this.#schedule(); }
	#schedule() {
		if ( this.#pending ) { return; }
		this.#pending = true;
		queueMicrotask( () => { this.#pending = false; this.#render(); } );
	}

	// ------------------------------------------------------------------ public API
	/** The id of the view being shown. Setting it switches the view. */
	get view() { return this.#current(); }
	set view( id ) { this.setAttribute( 'view', id ); }
	/** The views on offer, in menu order: [ { id, label } ]. */
	get views() { return this.#available().map( ( [ id, d ] ) => ( { id, label: d.label || id } ) ); }
	/** Add a view to this rail only. */
	addView( id, def ) { this.#own.set( id, def ); this.#schedule(); }
	/** Open (or close) the item or section with this id; with open=true its parents open too. */
	toggle( id, open ) {
		const li = this.#root.querySelector( `[data-key="${ CSS.escape( id ) }"]` );
		if ( !li ) { return false; }
		this.#setOpen( li, open === undefined ? li.classList.contains( 'mw-collapsed' ) : open );
		return true;
	}
	/** Open every parent of the element with this id, and scroll to it. */
	reveal( id ) {
		const el = this.#root.querySelector( `[data-key="${ CSS.escape( id ) }"]` );
		if ( !el ) { return false; }
		for ( let n = el; n && n !== this.#root; n = n.parentElement ) {
			if ( n.classList && n.classList.contains( 'mw-collapsed' ) ) { this.#setOpen( n, true ); }
		}
		el.scrollIntoView();
		return true;
	}

	// ------------------------------------------------------------------ views
	#available() {
		const all = new Map( [ ...registry, ...this.#own ] );
		const ids = ( this.getAttribute( 'views' ) || '' ).split( /[\s,]+/ ).filter( Boolean );
		return ( ids.length ? ids : [ ...all.keys() ] ).filter( ( id ) => all.has( id ) ).map( ( id ) => [ id, all.get( id ) ] );
	}
	#current() {
		const list = this.#available();
		const want = this.getAttribute( 'view' );
		return list.some( ( [ id ] ) => id === want ) ? want : ( list.length ? list[ 0 ][ 0 ] : 'timeline' );
	}
	#choose( id ) {
		this.#menuOpen = false;
		if ( id !== this.#current() ) {
			this.setAttribute( 'view', id );
			this.dispatchEvent( new CustomEvent( 'timeline-view', { bubbles: true, detail: { view: id } } ) );
		} else { this.#render(); }
	}
	#outside = ( e ) => {
		if ( this.#menuOpen && !e.composedPath().includes( this ) ) { this.#menuOpen = false; this.#render(); }
	};
	#bar( views, current ) {
		const label = ( views.find( ( [ id ] ) => id === current ) || [ , {} ] )[ 1 ].label || current;
		const button = h( 'button', 'wt-viewmenu__button', { type: 'button', 'aria-haspopup': 'menu', 'aria-expanded': String( this.#menuOpen ) }, 'View: ' + label );
		const list = h( 'div', 'wt-viewmenu__list', { role: 'menu', 'aria-label': 'View' } );
		list.hidden = !this.#menuOpen;
		for ( const [ id, def ] of views ) {
			list.append( h( 'button', 'wt-viewmenu__item', { type: 'button', role: 'menuitemradio', 'aria-checked': String( id === current ), 'data-view': id, tabindex: '-1' }, def.label || id ) );
		}
		const items = () => [ ...list.querySelectorAll( '.wt-viewmenu__item' ) ];
		const toggle = ( open, focusItem ) => {
			this.#menuOpen = open; list.hidden = !open; button.setAttribute( 'aria-expanded', String( open ) );
			if ( open ) { ( items().find( ( b ) => b.getAttribute( 'aria-checked' ) === 'true' ) || items()[ 0 ] ).focus(); }
			else if ( focusItem ) { button.focus(); }
		};
		button.addEventListener( 'click', () => toggle( !this.#menuOpen ) );
		button.addEventListener( 'keydown', ( e ) => { if ( e.key === 'ArrowDown' ) { e.preventDefault(); toggle( true ); } } );
		list.addEventListener( 'click', ( e ) => {
			const b = e.target.closest( '.wt-viewmenu__item' );
			if ( b ) { this.#refocus = true; this.#choose( b.dataset.view ); }
		} );
		list.addEventListener( 'keydown', ( e ) => {
			const all = items(), at = all.indexOf( this.#root.activeElement );
			const go = { ArrowDown: ( at + 1 ) % all.length, ArrowUp: ( at - 1 + all.length ) % all.length, Home: 0, End: all.length - 1 }[ e.key ];
			if ( go !== undefined ) { e.preventDefault(); all[ go ].focus(); }
			else if ( e.key === 'Escape' || e.key === 'Tab' ) { toggle( false, e.key === 'Escape' ); }
		} );
		return h( 'div', 'wt-viewbar', null, h( 'div', 'wt-viewmenu', null, button, list ) );
	}
	/** The data of a list of read nodes, in the shape the views get (see views.js). */
	#model( nodes ) {
		const part = ( ev ) => ( {
			title: ev.title, text: ev.text || ev.nodes.map( ( n ) => n.textContent ).join( '' ).replace( /\s+/g, ' ' ).trim(),
			image: ev.image ? { src: ev.image, alt: ev.alt, width: ev.width, caption: ev.caption } : null,
			content: () => { const f = document.createDocumentFragment(); if ( ev.text ) { f.append( ev.text ); } f.append( ...ev.nodes.map( ( n ) => n.cloneNode( true ) ) ); return f; },
		} );
		return nodes.filter( ( n ) => n.kind !== 'gap' ).map( ( n ) => ( {
			kind: n.kind, id: n.id, key: n.key, date: n.date, summary: n.summary,
			...part( n.ev ), title: n.title,
			events: n.events.map( part ), children: this.#model( n.children ),
		} ) );
	}

	// ------------------------------------------------------------------ reading the children
	#readEvent( el ) {
		return {
			title: el.getAttribute( 'title' ) || '', image: el.getAttribute( 'image' ) || '',
			alt: el.getAttribute( 'image-alt' ) || '', width: el.getAttribute( 'image-width' ) || '',
			caption: el.getAttribute( 'caption' ) || '', text: el.getAttribute( 'text' ) || '',
			nodes: [ ...el.childNodes ].filter( ( n ) => !blank( n ) && !DATA_TAGS.includes( n.localName ) ),
		};
	}
	#readList( parent, path ) {
		const out = [];
		let i = 0;
		for ( const el of parent.children ) {
			const tag = el.localName;
			if ( tag === 'timeline-gap' ) { out.push( { kind: 'gap' } ); continue; }
			if ( tag !== 'timeline-item' && tag !== 'timeline-section' ) { continue; }
			const key = el.id || el.getAttribute( 'data-id' ) || path + '/' + i;
			i++;
			const ev = this.#readEvent( el );
			const node = { kind: tag === 'timeline-item' ? 'item' : 'section', el, key, id: el.id || '', ev,
				collapsed: bool( el, 'collapsed' ), last: bool( el, 'last' ),
				date: el.getAttribute( 'date' ) || '', title: el.getAttribute( 'title' ) || '',
				summary: el.getAttribute( 'summary' ) || '', collapsible: el.getAttribute( 'collapsible' ) !== 'false' };
			node.events = [ ...el.children ].filter( ( c ) => isTag( c, 'timeline-event' ) ).map( ( c ) => this.#readEvent( c ) );
			node.children = this.#readList( el, key );
			out.push( node );
		}
		return out;
	}

	// ------------------------------------------------------------------ drawing
	#event( ev, hideTitle ) {
		const kids = [ h( 'span', 'wt-timeline__title', null, hideTitle ? '' : ev.title ) ];
		const nodes = ev.nodes.map( ( n ) => n.cloneNode( true ) );
		if ( ev.text || nodes.length ) {
			const t = h( 'div', 'wt-timeline__text' );
			if ( ev.text ) { t.append( ev.text ); }
			t.append( ...nodes );
			kids.push( t );
		}
		if ( ev.image ) {
			const img = h( 'img', '', { src: ev.image, alt: ev.alt, width: ev.width || null, loading: 'lazy' } );
			kids.push( h( 'span', 'wt-timeline__image', null, img, ev.caption ? h( 'br' ) : null, ev.caption ) );
		}
		return h( 'div', 'wt-timeline__event', null, ...kids );
	}
	#rowAttrs( node ) {
		return { role: 'button', tabindex: '0', 'aria-expanded': node.collapsed ? 'false' : 'true' };
	}
	#item( node ) {
		const ev = node.ev;
		const hasContent = node.title || ev.text || ev.nodes.length || ev.image || node.events.length || node.children.length;
		const collapsible = node.collapsible && hasContent;
		const cls = 'wt-timeline__item' + ( collapsible ? ' wt-timeline__item--collapsible mw-collapsible' : '' )
			+ ( node.last ? ' wt-timeline__item--last' : '' );
		const li = h( 'li', cls, { 'data-key': node.key } );
		const date = h( 'span', 'wt-timeline__date', null, node.date );
		const events = h( 'div', 'wt-timeline__events', null,
			...( node.events.length ? node.events.map( ( e ) => this.#event( e, false ) ) : [ this.#event( ev, collapsible ) ] ) );
		const sub = node.children.length ? this.#list( node.children, 'wt-timeline wt-timeline--sub' ) : null;
		if ( !collapsible ) { li.append( date, events ); if ( sub ) { li.append( sub ); } return li; }
		const peek = node.events.length
			? h( 'span', 'wt-timeline__peek', null, node.summary || node.title )
			: h( 'span', 'wt-timeline__peek wt-timeline__peek--title', null, node.title );
		li.append( h( 'div', 'wt-timeline__row', this.#rowAttrs( node ), date, peek ),
			h( 'div', 'wt-timeline__body', null, events, sub ) );
		const open = this.#open.has( node.key ) ? this.#open.get( node.key ) : !node.collapsed;
		this.#apply( li, open );
		return li;
	}
	#section( node ) {
		const ev = node.ev;
		const li = h( 'li', 'wt-timeline__item wt-timeline__item--section mw-collapsible', { 'data-key': node.key } );
		const extra = ev.text || ev.nodes.length || ev.image
			? h( 'div', 'wt-timeline__section-extra', null, this.#event( { ...ev, title: '' } ) ) : null;
		const row = h( 'div', 'wt-timeline__row', { ...this.#rowAttrs( node ), id: node.id || null },
			h( 'span', 'wt-timeline__section-title', null, node.title ), extra );
		li.append( row, h( 'div', 'wt-timeline__body', null,
			this.#list( node.children, 'wt-timeline wt-timeline--section' ) ) );
		this.#apply( li, this.#open.has( node.key ) ? this.#open.get( node.key ) : !node.collapsed );
		return li;
	}
	#list( nodes, cls ) {
		const ol = h( 'ol', cls );
		for ( const n of nodes ) {
			ol.append( n.kind === 'gap' ? h( 'li', 'wt-timeline__item wt-timeline__item--gap', { 'aria-hidden': 'true' } )
				: n.kind === 'section' ? this.#section( n ) : this.#item( n ) );
		}
		return ol;
	}
	#render() {
		const columns = [ ...this.children ].filter( ( c ) => isTag( c, 'timeline-column' ) );
		const views = this.#available(), current = this.#current();
		const bar = views.length > 1 && this.getAttribute( 'switcher' ) !== 'false' ? this.#bar( views, current ) : null;
		const def = views.find( ( [ id ] ) => id === current );
		const custom = def && def[ 1 ].render;
		let tree;
		if ( custom ) {
			const model = { columns: columns.length
				? columns.map( ( c, i ) => ( { title: c.getAttribute( 'title' ) || '', nodes: this.#model( this.#readList( c, 'c' + i ) ) } ) )
				: [ { title: '', nodes: this.#model( this.#readList( this, 'r' ) ) } ] };
			const flatten = ( nodes, depth = 0, parent = null, out = [] ) => {
				for ( const n of nodes ) { out.push( { node: n, depth, parent } ); flatten( n.children, depth + 1, n, out ); }
				return out;
			};
			try { tree = custom( model, { h, flatten, rail: this } ); }
			catch ( err ) { console.error( '<timeline-rail> view "' + current + '" failed', err ); tree = h( 'p', '', null, 'This view could not be drawn.' ); }
			tree.dataset.view = current;
		} else if ( columns.length ) {
			tree = h( 'div', 'wt-timelines' + ( bool( this, 'grouped' ) ? ' wt-timelines--grouped' : '' ) );
			columns.forEach( ( c, i ) => {
				const col = h( 'div', 'wt-timelines__col' );
				if ( c.getAttribute( 'title' ) ) { col.append( h( 'div', 'wt-timeline__heading', null, c.getAttribute( 'title' ) ) ); }
				col.append( this.#list( this.#readList( c, 'c' + i ), 'wt-timeline' ) );
				tree.append( col );
			} );
		} else {
			tree = this.#list( this.#readList( this, 'r' ), 'wt-timeline' );
		}
		const hadFocus = this.#root.activeElement && this.#root.activeElement.closest && this.#root.activeElement.closest( '.wt-viewmenu' );
		[ ...this.#root.children ].forEach( ( n ) => { if ( n.localName !== 'style' ) { n.remove(); } } );
		if ( bar ) { this.#root.append( bar ); }
		this.#root.append( tree );
		if ( this.#refocus ) { this.#refocus = false; const b = this.#root.querySelector( '.wt-viewmenu__button' ); if ( b ) { b.focus(); } }
		else if ( hadFocus && this.#menuOpen ) { this.#root.querySelector( '.wt-viewmenu__item[aria-checked="true"]' ).focus(); }
		if ( !custom ) {
			tree.addEventListener( 'click', ( e ) => this.#onRow( e ) );
			tree.addEventListener( 'keydown', ( e ) => this.#onRow( e ) );
			tree.addEventListener( 'dblclick', ( e ) => this.#onDouble( e ) );
		}
	}

	// ------------------------------------------------------------------ state and interaction
	#apply( li, open ) {
		li.classList.toggle( 'mw-collapsed', !open );
		const body = li.querySelector( ':scope > .wt-timeline__body' );
		if ( body ) { body.hidden = !open; }
		const row = li.querySelector( ':scope > .wt-timeline__row' );
		if ( row ) { row.setAttribute( 'aria-expanded', String( open ) ); }
	}
	#setOpen( li, open, silent ) {
		this.#apply( li, open );
		const key = li.dataset.key;
		this.#open.set( key, open );
		if ( !silent ) {
			this.dispatchEvent( new CustomEvent( 'timeline-toggle', { bubbles: true, detail: { id: key, open } } ) );
		}
	}
	#onRow( e ) {
		if ( e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ' ) { return; }
		const row = e.target.closest( '.wt-timeline__row' );
		if ( !row || ( e.type === 'click' && e.target.closest( 'a[href]' ) ) ) { return; }
		if ( e.target.closest( '.wt-timeline__section-extra' ) && e.type === 'click' ) { return; }   // select the text
		e.preventDefault();
		const li = row.parentElement;
		this.#setOpen( li, li.classList.contains( 'mw-collapsed' ) );
	}
	#onDouble( e ) {
		const row = e.target.closest( '.wt-timeline__row' );
		if ( !row ) { return; }
		e.preventDefault();
		const self = row.parentElement, list = self.parentElement;
		if ( self.classList.contains( 'wt-timeline__item--section' ) ) {
			const others = [ ...list.children ].filter( ( c ) => c !== self && c.classList.contains( 'wt-timeline__item--section' ) );
			const someOpen = others.some( ( c ) => !c.classList.contains( 'mw-collapsed' ) );
			others.forEach( ( c ) => this.#setOpen( c, !someOpen ) );
			this.#setOpen( self, true );
			return;
		}
		const root = list.closest( '.wt-timeline:not(.wt-timeline--sub):not(.wt-timeline--section)' ) || list;
		const items = [ ...root.querySelectorAll( '.wt-timeline__item--collapsible' ) ];
		const anyOpen = items.some( ( i ) => !i.classList.contains( 'mw-collapsed' ) );
		items.forEach( ( i ) => this.#setOpen( i, !anyOpen ) );
	}
	#hash = () => {
		let id = '';
		try { id = decodeURIComponent( location.hash.slice( 1 ) ); } catch ( e ) { return; }
		if ( id ) { this.reveal( id ); }
	};
}

// The data elements are inert: only the rail draws them.
for ( const tag of DATA_TAGS ) {
	if ( !customElements.get( tag ) ) { customElements.define( tag, class extends HTMLElement {} ); }
}
if ( !customElements.get( 'timeline-rail' ) ) { customElements.define( 'timeline-rail', TimelineRail ); }
