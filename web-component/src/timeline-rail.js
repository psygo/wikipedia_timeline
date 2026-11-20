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
 * Several views of the same data: put the items once in <timeline-data id="x"> and write
 * <timeline-rail for="x">, <outline-list for="x">, <outline-table for="x"> inside a <view-switcher>.
 *
 * Interaction: click or Enter on a row toggles it; double-click an item's dot to collapse or expand
 * every item of that timeline; double-click a section's dot to keep it open and close its sibling
 * sections. The "timeline-toggle" event bubbles with { id, open }. The rail also opens the
 * item or section named by location.hash.
 */
import baseCss from './timeline.css.js';
import { h, isTag, blank, bool, whenParsed } from './util.js';
import { DATA_TAGS } from './data.js';

// Links inside the shadow root do not see the page's link colour; use the same token.
const railCss = baseCss + '\n.wt-timeline a { color: var( --color-progressive, #36c ); }\n';

let sheet = null;
if ( typeof CSSStyleSheet !== 'undefined' && 'replaceSync' in CSSStyleSheet.prototype ) {
	sheet = new CSSStyleSheet();
	sheet.replaceSync( railCss );
}

export class TimelineRail extends HTMLElement {
	#root; #open = new Map(); #pending = false; #mo;
	static get observedAttributes() { return [ 'grouped', 'for' ]; }

	constructor() {
		super();
		this.#root = this.attachShadow( { mode: 'open' } );
		if ( sheet ) { this.#root.adoptedStyleSheets = [ sheet ]; }
		else { this.#root.append( h( 'style' ) ); this.#root.firstChild.textContent = railCss; }
		this.#mo = new MutationObserver( () => this.#schedule() );
	}

	connectedCallback() {
		window.addEventListener( 'hashchange', this.#hash );
		whenParsed( () => { this.#watch(); this.#render(); this.#hash(); } );
	}
	disconnectedCallback() {
		this.#mo.disconnect();
		window.removeEventListener( 'hashchange', this.#hash );
	}
	attributeChangedCallback() { if ( this.isConnected ) { this.#watch(); } this.#schedule(); }
	/** The element the items are read from: this one, or the one named by for="id" (see data.js). */
	get source() {
		const id = this.getAttribute( 'for' );
		return id ? document.getElementById( id ) : this;
	}
	#watch() {
		this.#mo.disconnect();
		const opts = { childList: true, subtree: true, characterData: true, attributes: true };
		const src = this.source;
		this.#mo.observe( this, opts );
		if ( src && src !== this ) { this.#mo.observe( src, opts ); }
	}
	#schedule() {
		if ( this.#pending ) { return; }
		this.#pending = true;
		queueMicrotask( () => { this.#pending = false; this.#render(); } );
	}

	// ------------------------------------------------------------------ public API
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
		const src = this.source;
		if ( !src ) { return; }
		const columns = [ ...src.children ].filter( ( c ) => isTag( c, 'timeline-column' ) );
		let tree;
		if ( columns.length ) {
			tree = h( 'div', 'wt-timelines' + ( bool( this, 'grouped' ) ? ' wt-timelines--grouped' : '' ) );
			columns.forEach( ( c, i ) => {
				const col = h( 'div', 'wt-timelines__col' );
				if ( c.getAttribute( 'title' ) ) { col.append( h( 'div', 'wt-timeline__heading', null, c.getAttribute( 'title' ) ) ); }
				col.append( this.#list( this.#readList( c, 'c' + i ), 'wt-timeline' ) );
				tree.append( col );
			} );
		} else {
			tree = this.#list( this.#readList( src, 'r' ), 'wt-timeline' );
		}
		[ ...this.#root.children ].forEach( ( n ) => { if ( n.localName !== 'style' ) { n.remove(); } } );
		this.#root.append( tree );
		tree.addEventListener( 'click', ( e ) => this.#onRow( e ) );
		tree.addEventListener( 'keydown', ( e ) => this.#onRow( e ) );
		tree.addEventListener( 'dblclick', ( e ) => this.#onDouble( e ) );
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

if ( !customElements.get( 'timeline-rail' ) ) { customElements.define( 'timeline-rail', TimelineRail ); }
