/*
 * ViewSwitcher.js: the "View" dropdown for Module:ViewSwitcher.
 *
 * The module writes   <div class="viewswitcher"><div class="viewswitcher__view" data-vs-label="Table">...
 * and this script puts a button at the top right that shows one view at a time. Install it as a
 * gadget (MediaWiki:Gadget-ViewSwitcher.js) or, to try it, on its own page User:<name>/ViewSwitcher.js,
 * loaded by the line  importScript( 'User:<name>/ViewSwitcher.js' );  in your User:<name>/common.js.
 * Without it the reader sees the first (default) view.
 *
 * Fires a "viewswitcher-change" DOM event on the container, with detail.label and detail.index.
 */
( function () {
	'use strict';

	function build( box ) {
		if ( box.classList.contains( 'viewswitcher--js' ) ) { return; }
		var views = [].filter.call( box.children, function ( c ) { return c.classList.contains( 'viewswitcher__view' ); } );
		if ( views.length < 2 ) { return; }
		box.classList.add( 'viewswitcher--js' );

		var current = Math.max( 0, views.findIndex( function ( v ) { return v.classList.contains( 'viewswitcher__view--default' ); } ) );
		var el = function ( tag, cls, attrs, text ) {
			var n = document.createElement( tag );
			if ( cls ) { n.className = cls; }
			Object.keys( attrs || {} ).forEach( function ( k ) { n.setAttribute( k, attrs[ k ] ); } );
			if ( text ) { n.textContent = text; }
			return n;
		};
		var label = function ( i ) { return views[ i ].getAttribute( 'data-vs-label' ) || ( 'View ' + ( i + 1 ) ); };

		var button = el( 'button', 'viewswitcher__button', { type: 'button', 'aria-haspopup': 'menu', 'aria-expanded': 'false' } );
		var list = el( 'div', 'viewswitcher__list', { role: 'menu', 'aria-label': 'View' } );
		list.hidden = true;
		var items = views.map( function ( v, i ) {
			var b = el( 'button', 'viewswitcher__item', { type: 'button', role: 'menuitemradio', tabindex: '-1' }, label( i ) );
			list.appendChild( b );
			return b;
		} );
		var bar = el( 'div', 'viewswitcher__bar' );
		var menu = el( 'div', 'viewswitcher__menu' );
		menu.appendChild( button );
		menu.appendChild( list );
		bar.appendChild( menu );
		box.insertBefore( bar, box.firstChild );

		function show( i, announce ) {
			current = i;
			views.forEach( function ( v, k ) { v.hidden = k !== i; } );
			items.forEach( function ( b, k ) { b.setAttribute( 'aria-checked', String( k === i ) ); } );
			button.textContent = label( i );
			if ( announce ) {
				box.dispatchEvent( new CustomEvent( 'viewswitcher-change', { bubbles: true, detail: { label: label( i ), index: i } } ) );
			}
		}
		function toggle( open, refocus ) {
			list.hidden = !open;
			button.setAttribute( 'aria-expanded', String( open ) );
			if ( open ) { items[ current ].focus(); } else if ( refocus ) { button.focus(); }
		}
		button.addEventListener( 'click', function () { toggle( list.hidden ); } );
		button.addEventListener( 'keydown', function ( e ) {
			if ( e.key === 'ArrowDown' ) { e.preventDefault(); toggle( true ); }
		} );
		items.forEach( function ( b, i ) {
			b.addEventListener( 'click', function () { show( i, i !== current ); toggle( false, true ); } );
		} );
		list.addEventListener( 'keydown', function ( e ) {
			var at = items.indexOf( document.activeElement );
			var go = { ArrowDown: ( at + 1 ) % items.length, ArrowUp: ( at - 1 + items.length ) % items.length,
				Home: 0, End: items.length - 1 }[ e.key ];
			if ( go !== undefined ) { e.preventDefault(); items[ go ].focus(); }
			else if ( e.key === 'Escape' || e.key === 'Tab' ) { toggle( false, e.key === 'Escape' ); }
		} );
		document.addEventListener( 'click', function ( e ) {
			if ( !list.hidden && !menu.contains( e.target ) ) { toggle( false ); }
		} );
		show( current, false );
	}

	function init( $content ) {
		var root = $content && $content[ 0 ] ? $content[ 0 ] : document;
		[].forEach.call( root.querySelectorAll( '.viewswitcher' ), build );
	}

	if ( typeof mw !== 'undefined' && mw.hook ) {
		mw.hook( 'wikipage.content' ).add( init );
	} else {
		document.addEventListener( 'DOMContentLoaded', function () { init(); } );
	}
}() );
