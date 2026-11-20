/*
 * <outline-list>: the data as a plain bulleted list, the way an article has it today.
 *   <outline-list for="go"></outline-list>   or   <outline-list> <timeline-item ...>...</outline-list>
 */
import { h } from './util.js';
import { ViewElement, figure } from './view-element.js';

export class OutlineList extends ViewElement {
	draw( model ) {
		const eventLi = ( ev ) => h( 'li', '', null,
			ev.title ? h( 'b', '', null, ev.title ) : null, ev.title && ev.text ? '. ' : null, ev.content(), figure( ev.image ) );
		const items = ( nodes ) => {
			const ul = h( 'ul' );
			for ( const n of nodes ) {
				const li = h( 'li' );
				if ( n.date ) { li.append( h( 'b', '', null, n.date ), n.title || n.text || n.events.length ? ' – ' : '' ); }
				if ( n.events.length ) {
					li.append( h( 'ul', '', null, ...n.events.map( eventLi ) ) );
				} else {
					if ( n.title ) { li.append( h( 'b', '', null, n.title ), n.text ? '. ' : '' ); }
					li.append( n.content(), figure( n.image ) );
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
					into.append( h( 'div', 'view__heading', { role: 'heading', 'aria-level': String( Math.min( level + 2, 6 ) ), 'data-level': String( Math.min( level, 3 ) ) }, n.title ) );
					if ( n.text || n.image ) { into.append( h( 'div', 'view__lead', null, n.content(), figure( n.image ) ) ); }
					walk( n.children, level + 1, into );
				} else { run.push( n ); }
			}
			flush();
		};
		const root = h( 'div', 'view view-list' );
		for ( const col of model.columns ) {
			if ( col.title ) { root.append( h( 'div', 'view__col-title', null, col.title ) ); }
			walk( col.nodes, 1, root );
		}
		return root;
	}
}
if ( !customElements.get( 'outline-list' ) ) { customElements.define( 'outline-list', OutlineList ); }
