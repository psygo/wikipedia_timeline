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
	var togglers = new Map(); // collapsible element -> its toggler

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
			togglers.set( target, toggler );
			toggler.tabIndex = 0;
			var act = function ( e ) {
				if ( e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ' ) { return; }
				if ( e.type === 'click' && e.target.closest( 'a[href]' ) ) { return; }
				e.preventDefault();
				toggle( toggler, target, !target.classList.contains( 'mw-collapsed' ) );
				// A real click on a section puts its anchor in the URL (bulk toggles do not).
				var li = toggler.parentElement;
				if ( li && li.classList.contains( 'wt-timeline__item--section' ) && li.id && ( e.detail > 0 || e.type === 'keydown' ) ) {
					setHash( li.id );
				}
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

	/*
	 * Anchors. Sections have ids, so a link such as page.html#Edo_period scrolls to the
	 * section and opens everything around it. MediaWiki's own module opens collapsed
	 * parents on hashchange; this also does it on load. When the page is framed (the
	 * viewer), the URL of the parent is kept in step through postMessage.
	 */
	function notify() {
		if ( window.parent !== window ) {
			window.parent.postMessage( { wtHash: location.hash }, '*' );
		}
	}
	function setHash( id ) {
		try {
			history.replaceState( null, '', location.pathname + location.search + '#' + id );
		} catch ( e ) { return; }
		notify();
	}
	function goTo( hash ) {
		var id = '';
		try { id = decodeURIComponent( hash.replace( /^#/, '' ) ); } catch ( e ) { return; }
		var el = id && document.getElementById( id );
		if ( !el ) { return; }
		for ( var n = el; n; n = n.parentElement ) {
			if ( n.classList.contains( 'mw-collapsed' ) && togglers.has( n ) ) {
				toggle( togglers.get( n ), n, false );
			}
		}
		if ( el.classList.contains( 'wt-timeline__item--section' ) ) {
			var body = el.querySelector( ':scope > .mw-collapsible' );
			if ( body && togglers.has( body ) ) { toggle( togglers.get( body ), body, false ); }
		}
		el.scrollIntoView();
	}
	window.addEventListener( 'hashchange', function () { goTo( location.hash ); notify(); } );
	window.addEventListener( 'message', function ( e ) {
		if ( e.data && typeof e.data.wtGoto === 'string' && e.data.wtGoto !== location.hash ) {
			location.hash = e.data.wtGoto;
		}
	} );
	if ( location.hash ) { goTo( location.hash ); }
}() );
