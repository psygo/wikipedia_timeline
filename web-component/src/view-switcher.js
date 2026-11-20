/*
 * <view-switcher>: a "View" dropdown at the top right that shows one of its children at a time.
 * It knows nothing about timelines: a view is any child element with a label.
 *
 *   <view-switcher>
 *     <timeline-rail for="go" label="Timeline" default></timeline-rail>
 *     <outline-list  for="go" label="List"></outline-list>
 *     <outline-table for="go" label="Table"></outline-table>
 *   </view-switcher>
 *
 * label       on each child: the name in the menu (else its id, else its tag name).
 * default     on one child: the view shown first. Or default="Table" on the switcher (a label), or
 *             view="Table" to set the current one. Without any of them, the first.
 * No JavaScript: the children simply all show, one after the other.
 * Script: switcher.view (label, get and set), switcher.views (labels), and a bubbling "view-change"
 * event with { label, index }.
 */
import { h } from './util.js';

const css = `
:host { display: block; }
::slotted( [hidden] ) { display: none !important; }
.bar { display: flex; justify-content: flex-end; margin: 0 0 0.6em; }
.menu { position: relative; }
.button {
	font: inherit; font-size: 0.875em; color: var( --color-base, #202122 ); cursor: pointer;
	padding: 0.3em 0.75em; border: 1px solid var( --border-color-base, #a2a9b1 ); border-radius: 2px;
	background: var( --background-color-interactive-subtle, #f8f9fa );
}
.button:hover, .button[aria-expanded="true"] { border-color: var( --color-progressive, #36c ); }
.button:focus-visible, .item:focus-visible { outline: 2px solid var( --color-progressive, #36c ); outline-offset: 1px; }
.button::after { content: ''; display: inline-block; margin-left: 0.55em; vertical-align: 0.1em;
	border: 0.3em solid transparent; border-top-color: currentColor; border-bottom-width: 0; }
.list {
	position: absolute; right: 0; z-index: 5; min-width: 100%; margin: 2px 0 0; padding: 0.25em 0;
	border: 1px solid var( --border-color-base, #a2a9b1 ); border-radius: 2px;
	background: var( --background-color-base, #fff ); box-shadow: 0 2px 6px rgba( 0, 0, 0, 0.2 );
}
.list[hidden] { display: none; }
.item {
	display: block; width: 100%; padding: 0.35em 1.8em 0.35em 1em; border: 0; background: none;
	font: inherit; font-size: 0.875em; text-align: left; white-space: nowrap; cursor: pointer; color: var( --color-base, #202122 );
}
.item:hover { background: var( --background-color-interactive-subtle, #f8f9fa ); }
.item[aria-checked="true"] { font-weight: bold; color: var( --color-progressive, #36c ); }
.item[aria-checked="true"]::after { content: '\\2713'; float: right; margin-right: -1.3em; }
`;

export class ViewSwitcher extends HTMLElement {
	static get observedAttributes() { return [ 'view', 'default' ]; }
	#root; #bar; #slot; #open = false; #current = null; #mo;

	constructor() {
		super();
		this.#root = this.attachShadow( { mode: 'open' } );
		const style = document.createElement( 'style' );
		style.textContent = css;
		this.#slot = document.createElement( 'slot' );
		this.#root.append( style, this.#slot );
		this.#slot.addEventListener( 'slotchange', () => this.#sync() );
		this.#mo = new MutationObserver( () => this.#sync() );
	}
	connectedCallback() {
		this.#mo.observe( this, { attributes: true, attributeFilter: [ 'label', 'default' ], subtree: true } );
		document.addEventListener( 'click', this.#outside );
		this.#sync();
	}
	disconnectedCallback() { this.#mo.disconnect(); document.removeEventListener( 'click', this.#outside ); }
	attributeChangedCallback( name ) { if ( name === 'view' ) { this.#current = null; } this.#sync(); }

	get #views() { return [ ...this.children ].filter( ( c ) => !c.hasAttribute( 'slot' ) ); }
	#label( el, i ) { return el.getAttribute( 'label' ) || el.id || el.localName + ( i ? ' ' + ( i + 1 ) : '' ); }
	/** The labels of the views, in menu order. */
	get views() { return this.#views.map( ( el, i ) => this.#label( el, i ) ); }
	/** The label of the view being shown. Setting it switches the view. */
	get view() { return this.views[ this.#index() ] || ''; }
	set view( label ) { this.#choose( this.views.indexOf( label ) ); }

	#index() {
		const views = this.#views, labels = this.views;
		if ( this.#current !== null && this.#current < views.length ) { return this.#current; }
		let i = labels.indexOf( this.getAttribute( 'view' ) );
		if ( i < 0 ) { i = views.findIndex( ( el ) => el.hasAttribute( 'default' ) ); }
		if ( i < 0 ) { i = labels.indexOf( this.getAttribute( 'default' ) ); }
		return Math.max( 0, i );
	}
	#choose( i ) {
		if ( i < 0 || i >= this.#views.length ) { return; }
		const changed = i !== this.#index();
		this.#current = i;
		this.#sync();
		if ( changed ) { this.dispatchEvent( new CustomEvent( 'view-change', { bubbles: true, detail: { label: this.views[ i ], index: i } } ) ); }
	}
	#outside = ( e ) => {
		if ( this.#open && !e.composedPath().includes( this ) ) { this.#open = false; this.#sync(); }
	};

	#sync() {
		const views = this.#views;
		if ( this.#bar ) { this.#bar.remove(); this.#bar = null; }
		if ( views.length < 2 ) { views.forEach( ( el ) => { el.hidden = false; } ); return; }
		const cur = this.#index(), labels = this.views;
		views.forEach( ( el, i ) => { el.hidden = i !== cur; } );

		const button = h( 'button', 'button', { type: 'button', 'aria-haspopup': 'menu', 'aria-expanded': String( this.#open ) }, 'View: ' + labels[ cur ] );
		const list = h( 'div', 'list', { role: 'menu', 'aria-label': 'View' } );
		list.hidden = !this.#open;
		const items = labels.map( ( l, i ) => {
			const b = h( 'button', 'item', { type: 'button', role: 'menuitemradio', 'aria-checked': String( i === cur ), tabindex: '-1' }, l );
			list.append( b );
			return b;
		} );
		const toggle = ( open, refocus ) => {
			this.#open = open; list.hidden = !open; button.setAttribute( 'aria-expanded', String( open ) );
			if ( open ) { items[ cur ].focus(); } else if ( refocus ) { button.focus(); }
		};
		button.addEventListener( 'click', () => toggle( !this.#open ) );
		button.addEventListener( 'keydown', ( e ) => { if ( e.key === 'ArrowDown' ) { e.preventDefault(); toggle( true ); } } );
		items.forEach( ( b, i ) => b.addEventListener( 'click', () => {
			this.#open = false; this.#choose( i );
			const again = this.#root.querySelector( '.button' ); if ( again ) { again.focus(); }
		} ) );
		list.addEventListener( 'keydown', ( e ) => {
			const at = items.indexOf( this.#root.activeElement );
			const go = { ArrowDown: ( at + 1 ) % items.length, ArrowUp: ( at - 1 + items.length ) % items.length, Home: 0, End: items.length - 1 }[ e.key ];
			if ( go !== undefined ) { e.preventDefault(); items[ go ].focus(); }
			else if ( e.key === 'Escape' || e.key === 'Tab' ) { toggle( false, e.key === 'Escape' ); }
		} );
		this.#bar = h( 'div', 'bar', null, h( 'div', 'menu', null, button, list ) );
		this.#root.insertBefore( this.#bar, this.#slot );
		if ( this.#open ) { items[ cur ].focus(); }
	}
}
if ( !customElements.get( 'view-switcher' ) ) { customElements.define( 'view-switcher', ViewSwitcher ); }
