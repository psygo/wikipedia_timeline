/*
 * Base of the plain views (<outline-list>, <outline-table>): draws the data of its source, which is the
 * element itself or the one named by for="id", into a shadow root. Subclasses implement draw( model ).
 * Write your own the same way:
 *
 *   class OutlineCards extends ViewElement { draw( model ) { return h( 'div', '', null, ... ); } }
 *   customElements.define( 'outline-cards', OutlineCards );
 */
import { h, whenParsed } from './util.js';
import { readModel } from './data.js';

export const viewCss = `
:host { display: block; }
.view { color: var( --color-base, #202122 ); line-height: 1.6; }
.view a { color: var( --color-progressive, #36c ); text-decoration: none; }
.view a:hover { text-decoration: underline; }
.view__heading { margin: 1em 0 0.3em; font-weight: bold; }
.view__heading[data-level="1"] { font-size: 1.3em; border-bottom: 1px solid var( --border-color-subtle, #c8ccd1 ); }
.view__heading[data-level="2"] { font-size: 1.15em; }
.view__lead { margin: 0 0 0.4em; }
.view__col-title { margin: 1em 0 0.3em; font-weight: bold; font-size: 1.1em; }
.view__figure { display: block; max-width: 14em; font-size: 0.875em; color: var( --color-subtle, #54595d ); }
.view__figure img { display: block; max-width: 100%; height: auto; }
.view-list ul { margin: 0.3em 0 0 1.6em; padding: 0; list-style: disc; }
.view-list li { margin-bottom: 0.25em; }
.view-list .view__figure { margin: 0.3em 0; }
.view-table table { border-collapse: collapse; width: 100%; margin: 0.4em 0 1em; background: var( --background-color-base, #fff ); }
.view-table th, .view-table td { padding: 0.4em 0.6em; border: 1px solid var( --border-color-base, #a2a9b1 ); vertical-align: top; text-align: left; }
.view-table thead th { background: var( --background-color-interactive-subtle, #eaecf0 ); text-align: center; }
.view-table td.view__date { white-space: nowrap; }
.view-table td.view__title { font-weight: bold; }
.view-table th[colspan] { background: var( --background-color-interactive-subtle, #f8f9fa ); }
.view-table .view__sub::before { content: '\\21B3\\00A0'; color: var( --color-subtle, #54595d ); }
.view-table .view__sub { padding-left: 1.6em; }
.view-table .view__figure { max-width: 10em; }
`;

export const figure = ( img ) => !img ? document.createDocumentFragment() : h( 'span', 'view__figure', null,
	h( 'img', '', { src: img.src, alt: img.alt, width: img.width || null, loading: 'lazy' } ),
	img.caption ? h( 'span', '', null, img.caption ) : null );

export class ViewElement extends HTMLElement {
	static get observedAttributes() { return [ 'for', 'columns' ]; }
	#root; #mo; #pending = false;

	constructor() {
		super();
		this.#root = this.attachShadow( { mode: 'open' } );
		const style = document.createElement( 'style' );
		style.textContent = viewCss;
		this.#root.append( style );
		this.#mo = new MutationObserver( () => this.#schedule() );
	}
	/** The element the data is read from. */
	get source() {
		const id = this.getAttribute( 'for' );
		return id ? document.getElementById( id ) : this;
	}
	connectedCallback() { whenParsed( () => { this.#watch(); this.#render(); } ); }
	disconnectedCallback() { this.#mo.disconnect(); }
	attributeChangedCallback() { if ( this.isConnected ) { this.#watch(); this.#schedule(); } }
	#watch() {
		this.#mo.disconnect();
		const opts = { childList: true, subtree: true, characterData: true, attributes: true };
		this.#mo.observe( this, { attributes: true } );
		const src = this.source;
		if ( src && src !== this ) { this.#mo.observe( src, opts ); } else { this.#mo.observe( this, opts ); }
	}
	#schedule() {
		if ( this.#pending ) { return; }
		this.#pending = true;
		queueMicrotask( () => { this.#pending = false; this.#render(); } );
	}
	#render() {
		const src = this.source;
		[ ...this.#root.children ].forEach( ( n ) => { if ( n.localName !== 'style' ) { n.remove(); } } );
		if ( src ) { this.#root.append( this.draw( readModel( src ) ) ); }
	}
	/** Subclasses: return the Node for this model. */
	draw() { return document.createDocumentFragment(); }
}
