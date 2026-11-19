/*
 * Timeline: double-click any dot to collapse or expand every item of that timeline;
 * clicking a section puts its anchor in the address bar.
 *
 * Optional user script (or gadget). The collapsible items themselves need no script:
 * they use MediaWiki's built-in collapsible module. This only adds the shortcut.
 *
 * Install: copy to User:<YourName>/Timeline-collapse-all.js and add to
 * User:<YourName>/common.js:
 *     importScript( 'User:<YourName>/Timeline-collapse-all.js' );
 *
 * Behaviour: a double-click on an item's date row (the dot or the date) collapses every
 * collapsible item of that timeline (nested timelines included), or expands them all if
 * none is open. The two clicks of the double-click first toggle that one item twice,
 * which changes nothing.
 */
( function () {
	'use strict';
	var ROW = '.wt-timeline__row';

	// A real click on a section's red dot or title adds #Section_title to the URL, so the
	// address can be shared; it opens collapsed parents and scrolls there when visited.
	mw.hook( 'wikipage.content' ).add( function ( $content ) {
		$content.find( '.wt-timeline__item--section > ' + ROW ).each( function () {
			var $row = $( this );
			var id = $row.parent().attr( 'id' );
			if ( !id || $row.data( 'wtAnchor' ) ) {
				return;
			}
			$row.data( 'wtAnchor', true ).on( 'click', function ( e ) {
				if ( e.originalEvent && e.originalEvent.detail > 0 ) {
					history.replaceState( null, '', location.pathname + location.search + '#' + id );
				}
			} );
		} );
	} );

	mw.hook( 'wikipage.content' ).add( function ( $content ) {
		$content.find( ROW ).each( function () {
			var $row = $( this );
			var $list = $row.closest( '.wt-timeline' );
			if ( !$list.length || $row.data( 'wtCollapseAll' ) ) {
				return;
			}
			$row.data( 'wtCollapseAll', true ).on( 'dblclick', function ( e ) {
				e.preventDefault();
				var $rows = $list.find( ROW );
				var anyOpen = $rows.filter( '.mw-collapsible-toggle-expanded' ).length > 0;
				$rows.each( function () {
					var open = $( this ).hasClass( 'mw-collapsible-toggle-expanded' );
					if ( open === anyOpen ) {
						// What the real module does when the toggler is clicked.
						$( this ).trigger( 'click' );
					}
				} );
			} );
		} );
	} );
}() );
