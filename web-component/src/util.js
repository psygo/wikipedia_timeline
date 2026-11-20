// Small helpers shared by the elements.
export function h( tag, cls, attrs, ...kids ) {
	const el = document.createElement( tag );
	if ( cls ) { el.className = cls; }
	for ( const k in attrs || {} ) { if ( attrs[ k ] != null ) { el.setAttribute( k, attrs[ k ] ); } }
	for ( const k of kids ) { if ( k ) { el.append( k ); } }
	return el;
}
export const isTag = ( n, t ) => n.nodeType === 1 && n.localName === t;
export const blank = ( n ) => n.nodeType === 8 || ( n.nodeType === 3 && !n.textContent.trim() );
export const bool = ( el, name ) => el.hasAttribute( name ) && el.getAttribute( name ) !== 'false';

/** Run fn once the document is parsed (an element may refer to data that comes later in the page). */
export function whenParsed( fn ) {
	if ( document.readyState === 'loading' ) { document.addEventListener( 'DOMContentLoaded', fn, { once: true } ); }
	else { fn(); }
}
