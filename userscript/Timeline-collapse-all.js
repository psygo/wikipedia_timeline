/*
 * Timeline: double-click the top dot to collapse or expand all items.
 *
 * Optional user script (or gadget). The collapsible items themselves need no script:
 * they use MediaWiki's built-in collapsible module. This only adds the shortcut.
 *
 * Install: copy to User:<YourName>/Timeline-collapse-all.js and add to
 * User:<YourName>/common.js:
 *     importScript( 'User:<YourName>/Timeline-collapse-all.js' );
 *
 * Behaviour: on a timeline whose first item is collapsible, a double-click on its
 * date row collapses every collapsible item of that timeline, or expands them all if
 * none is open. (The two clicks of the double-click first toggle that one item twice,
 * which changes nothing.)
 */
( function () {
	'use strict';
	var ROW = '.wt-timeline__row';

	mw.hook( 'wikipage.content' ).add( function ( $content ) {
		$content.find( '.wt-timeline' ).each( function () {
			var $list = $( this );
			var $first = $list.children( '.wt-timeline__item' ).first().children( ROW );
			if ( !$first.length || $first.data( 'wtCollapseAll' ) ) {
				return;
			}
			$first.data( 'wtCollapseAll', true ).on( 'dblclick', function ( e ) {
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
