/*
 * <outline-table>: the data as a table. columns="date, text" picks and orders the columns
 * (date, title, text, image); by default the ones that have data.
 *   <outline-table for="go" columns="date, title, text"></outline-table>
 */
import { h } from './util.js';
import { flatten } from './data.js';
import { ViewElement, figure } from './view-element.js';

const LABELS = { date: 'Date', title: 'Title', text: 'Description', image: 'Image' };

export class OutlineTable extends ViewElement {
	draw( model ) {
		const root = h( 'div', 'view view-table' );
		const wanted = ( this.getAttribute( 'columns' ) || '' ).split( /[\s,]+/ ).filter( ( c ) => LABELS[ c ] );
		for ( const col of model.columns ) {
			const rows = flatten( col.nodes );
			const leaves = rows.filter( ( r ) => r.node.kind === 'item' ).map( ( r ) => r.node );
			const has = {
				date: leaves.some( ( n ) => n.date ),
				title: leaves.some( ( n ) => n.title || n.events.some( ( e ) => e.title ) ),
				text: leaves.some( ( n ) => n.text || n.events.some( ( e ) => e.text ) ),
				image: leaves.some( ( n ) => n.image || n.events.some( ( e ) => e.image ) ),
			};
			const cols = wanted.length ? wanted : Object.keys( LABELS ).filter( ( c ) => has[ c ] );
			if ( !cols.length ) { continue; }
			const cell = ( kind, src, sub ) => {
				if ( kind === 'date' ) { return h( 'td', 'view__date', null, src.date ); }
				if ( kind === 'title' ) { return h( 'td', 'view__title' + ( sub ? ' view__sub' : '' ), null, src.title ); }
				if ( kind === 'image' ) { return h( 'td', '', null, figure( src.image ) ); }
				return h( 'td', sub && !cols.includes( 'title' ) ? 'view__sub' : '', null, src.content() );
			};
			const table = h( 'table' );
			table.append( h( 'thead', '', null, h( 'tr', '', null, ...cols.map( ( c ) => h( 'th', '', { scope: 'col' }, LABELS[ c ] ) ) ) ) );
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
							if ( c === 'date' ) { if ( i === 0 ) { const td = cell( 'date', node ); td.rowSpan = node.events.length; tr.append( td ); } }
							else { tr.append( cell( c, ev, sub ) ); }
						}
						body.append( tr );
					} );
				} else {
					body.append( h( 'tr', '', null, ...cols.map( ( c ) => cell( c, node, sub ) ) ) );
				}
			}
			table.append( body );
			if ( col.title ) { root.append( h( 'div', 'view__col-title', null, col.title ) ); }
			root.append( h( 'div', '', { style: 'overflow-x:auto' }, table ) );
		}
		return root;
	}
}
if ( !customElements.get( 'outline-table' ) ) { customElements.define( 'outline-table', OutlineTable ); }
