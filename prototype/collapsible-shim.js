/*
 * Prototype-only stand-in for MediaWiki's jquery.makeCollapsible, for the case this
 * timeline uses: a "custom toggler". On Wikipedia the real module does this (it is
 * loaded automatically for pages that use the class mw-collapsible), so nothing
 * from this file goes into the template.
 *
 * Contract, copied from the real module:
 *   element.mw-collapsible#mw-customcollapsible-XXX   what collapses
 *   any element .mw-customtoggle-XXX                  what toggles it
 * Collapsing sets .mw-collapsed on the collapsible and hidden on it; the toggler
 * gets .mw-collapsible-toggle-collapsed / -expanded, aria-expanded and tabindex 0.
 * Clicking a link inside a toggler follows the link and does not toggle.
 */
( function () {
	function toggle( toggler, target, collapse ) {
		target.classList.toggle( 'mw-collapsed', collapse );
		target.hidden = collapse;
		toggler.classList.toggle( 'mw-collapsible-toggle-collapsed', collapse );
		toggler.classList.toggle( 'mw-collapsible-toggle-expanded', !collapse );
		toggler.setAttribute( 'aria-expanded', collapse ? 'false' : 'true' );
	}
	document.querySelectorAll( '.mw-collapsible[id^="mw-customcollapsible-"]' ).forEach( function ( target ) {
		var cls = target.id.replace( 'mw-customcollapsible-', 'mw-customtoggle-' );
		document.querySelectorAll( '.' + CSS.escape( cls ) ).forEach( function ( toggler ) {
			toggler.classList.add( 'mw-customtoggle' );
			toggler.tabIndex = 0;
			var act = function ( e ) {
				if ( e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ' ) { return; }
				if ( e.type === 'click' && e.target.closest( 'a[href]' ) ) { return; }
				e.preventDefault();
				toggle( toggler, target, !target.classList.contains( 'mw-collapsed' ) );
			};
			toggler.addEventListener( 'click', act );
			toggler.addEventListener( 'keydown', act );
			toggle( toggler, target, target.classList.contains( 'mw-collapsed' ) );
		} );
	} );

	/*
	 * Double-click any dot: collapse every collapsible item of that timeline (its own
	 * list and any nested ones), or expand them all if none is open. Not part of
	 * MediaWiki; on a wiki this is userscript/Timeline-collapse-all.js.
	 */
	document.querySelectorAll( '.wt-timeline__row' ).forEach( function ( row ) {
		var list = row.closest( '.wt-timeline' );
		if ( !list || list.classList.contains( 'wt-timeline--compact' ) ) { return; }
		row.addEventListener( 'dblclick', function ( e ) {
			e.preventDefault();
			var rows = list.querySelectorAll( '.wt-timeline__row' );
			var anyOpen = Array.prototype.some.call( rows, function ( r ) {
				return r.classList.contains( 'mw-collapsible-toggle-expanded' );
			} );
			rows.forEach( function ( r ) {
				var open = r.classList.contains( 'mw-collapsible-toggle-expanded' );
				if ( open === anyOpen ) { r.click(); }
			} );
		} );
	} );
}() );
