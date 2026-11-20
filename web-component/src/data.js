/*
 * The data elements: inert, they only hold what a view draws. Put them inside a view element, or once
 * inside <timeline-data id="x"> and let every view point at it with for="x".
 *
 *   <timeline-data id="go">
 *     <timeline-section title="Early"> <timeline-item date="1612" title="The academy">text</timeline-item> </timeline-section>
 *   </timeline-data>
 *   <timeline-rail for="go"></timeline-rail>   <outline-list for="go"></outline-list>
 *
 * <timeline-item>     date, title, summary, image, image-alt, image-width, caption, id, collapsed,
 *                     collapsible="false", last. Content: the text (any HTML). Nested items are sub items;
 *                     <timeline-event>s put several events on one dot.
 * <timeline-section>  title, id, collapsed, text, image, caption, ... Other content is its introduction.
 * <timeline-gap>      an empty slot, to line up dots in grouped columns.
 * <timeline-column>   title. Several of them place timelines side by side.
 */
import { isTag, blank } from './util.js';

export const DATA_TAGS = [ 'timeline-data', 'timeline-item', 'timeline-section', 'timeline-gap', 'timeline-column', 'timeline-event' ];
for ( const tag of DATA_TAGS ) {
	if ( !customElements.get( tag ) ) {
		customElements.define( tag, class extends HTMLElement {
			connectedCallback() { if ( tag === 'timeline-data' ) { this.hidden = true; } }
		} );
	}
}

const part = ( el ) => {
	const nodes = [ ...el.childNodes ].filter( ( n ) => !blank( n ) && !DATA_TAGS.includes( n.localName ) );
	const text = el.getAttribute( 'text' ) || nodes.map( ( n ) => n.textContent ).join( '' ).replace( /\s+/g, ' ' ).trim();
	const src = el.getAttribute( 'image' );
	return {
		title: el.getAttribute( 'title' ) || '', text,
		image: src ? { src, alt: el.getAttribute( 'image-alt' ) || '', width: el.getAttribute( 'image-width' ) || '', caption: el.getAttribute( 'caption' ) || '' } : null,
		/** a fresh fragment with the text and its links */
		content() {
			const f = document.createDocumentFragment();
			if ( el.getAttribute( 'text' ) ) { f.append( el.getAttribute( 'text' ) ); }
			f.append( ...nodes.map( ( n ) => n.cloneNode( true ) ) );
			return f;
		},
	};
};

function readList( parent ) {
	const out = [];
	for ( const el of parent.children ) {
		const tag = el.localName;
		if ( tag !== 'timeline-item' && tag !== 'timeline-section' ) { continue; }
		out.push( {
			kind: tag === 'timeline-item' ? 'item' : 'section', id: el.id || '', date: el.getAttribute( 'date' ) || '',
			summary: el.getAttribute( 'summary' ) || '', ...part( el ),
			events: [ ...el.children ].filter( ( c ) => isTag( c, 'timeline-event' ) ).map( part ),
			children: readList( el ),
		} );
	}
	return out;
}

/**
 * The data of a source element (the element itself or the one named by for=), the same for every view:
 *   { columns: [ { title, nodes } ] }   one column with no title unless there are <timeline-column>s
 *   node: { kind: 'item' | 'section', id, date, title, summary, text, content(), image, events, children }
 *     events: [ { title, text, content(), image } ] (several events on one dot)
 */
export function readModel( source ) {
	const columns = [ ...source.children ].filter( ( c ) => isTag( c, 'timeline-column' ) );
	return { columns: columns.length
		? columns.map( ( c ) => ( { title: c.getAttribute( 'title' ) || '', nodes: readList( c ) } ) )
		: [ { title: '', nodes: readList( source ) } ] };
}

/** [ { node, depth, parent } ] in reading order. */
export function flatten( nodes, depth = 0, parent = null, out = [] ) {
	for ( const n of nodes ) { out.push( { node: n, depth, parent } ); flatten( n.children, depth + 1, n, out ); }
	return out;
}
