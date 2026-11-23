/*
 * Prototype-only stand-in for MediaWiki's jquery.makeCollapsible, for the case this
 * timeline uses: a "custom toggler". On Wikipedia the real module does this (it is
 * loaded automatically for pages that use the class mw-collapsible), so nothing
 * from this file goes into the template.
 *
 * Contract, copied from the real module (read from its source on en.wikipedia):
 *   element.mw-collapsible#mw-customcollapsible-XXX   what collapses (the timeline item)
 *   its child .mw-collapsible-content                 what is hidden (the body)
 *   any element .mw-customtoggle-XXX                  what toggles it (the date row)
 * Collapsing sets .mw-collapsed on the collapsible and the hidden attribute on the content.
 * A custom toggler gets NO state class and no aria change: only tabindex 0.
 * Clicking a link inside a toggler follows the link and does not toggle.
 */
( function () {
	var togglers = new Map(); // collapsible element -> its toggler

	function toggle( target, collapse ) {
		target.classList.toggle( 'mw-collapsed', collapse );
		var content = target.querySelector( ':scope > .mw-collapsible-content' ) || target;
		content.hidden = collapse;
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
				toggle( target, !target.classList.contains( 'mw-collapsed' ) );
				// A real click on a section puts its anchor in the URL (bulk toggles do not).
				if ( target.classList.contains( 'wt-timeline__item--section' ) && toggler.id && ( e.detail > 0 || e.type === 'keydown' ) ) {
					setHash( toggler.id );
				}
			};
			toggler.addEventListener( 'click', act );
			toggler.addEventListener( 'keydown', act );
			toggle( target, target.classList.contains( 'mw-collapsed' ) );
		} );
	} );

	/*
	 * Double-click an item's dot: collapse every collapsible item of that timeline (its own
	 * list and any nested ones), or expand them all if none is open. Double-click a
	 * section's dot: close the other sections of its list and keep this one open (or open
	 * them all when they are all closed). Not part of
	 * MediaWiki; on a wiki this is userscript/Timeline-collapse-all.js.
	 */
	document.querySelectorAll( '.wt-timeline__row' ).forEach( function ( row ) {
		var list = row.closest( '.wt-timeline' );
		if ( !list ) { return; }
		row.addEventListener( 'dblclick', function ( e ) {
			e.preventDefault();
			var self = row.parentElement;
			if ( self.classList.contains( 'wt-timeline__item--section' ) ) {
				// A section dot: keep this section open and close the other sections of its
				// list; if they are all closed already, open them all.
				var others = Array.prototype.filter.call( list.children, function ( c ) {
					return c !== self && c.classList.contains( 'wt-timeline__item--section' );
				} );
				var someOpen = others.some( function ( c ) { return !c.classList.contains( 'mw-collapsed' ); } );
				others.forEach( function ( c ) { toggle( c, someOpen ); } );
				toggle( self, false );
				return;
			}
			var items = list.querySelectorAll( '.wt-timeline__item.mw-collapsible' );
			var anyOpen = Array.prototype.some.call( items, function ( i ) {
				return !i.classList.contains( 'mw-collapsed' );
			} );
			items.forEach( function ( i ) {
				var open = !i.classList.contains( 'mw-collapsed' );
				if ( open === anyOpen ) { toggle( i, anyOpen ); }
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
		// Like the real module: open every collapsed parent of the target (a section's own
		// row sits inside its collapsible, so the section opens too).
		for ( var n = el; n; n = n.parentElement ) {
			if ( n.classList.contains( 'mw-collapsed' ) && togglers.has( n ) ) {
				toggle( n, false );
			}
		}
		el.scrollIntoView();
	}
	window.addEventListener( 'hashchange', function () { goTo( location.hash ); notify(); } );
	window.addEventListener( 'message', function ( e ) {
		if ( e.source === window.parent && e.data && typeof e.data.wtGoto === 'string' && e.data.wtGoto !== location.hash ) {
			location.hash = e.data.wtGoto;
		}
	} );
	if ( location.hash ) { goTo( location.hash ); }
}() );
