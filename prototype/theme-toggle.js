/*
 * Prototype only: light/dark switch. The real template has no JavaScript;
 * on Wikipedia, theme comes from the reader's Vector preference.
 * Cycles: system -> light -> dark -> system.
 */
( function () {
	var root = document.documentElement;
	var modes = [ 'system', 'light', 'dark' ];
	var mode = 'system';
	try {
		mode = localStorage.getItem( 'wt-theme' ) || 'system';
	} catch ( e ) {}
	if ( modes.indexOf( mode ) < 0 ) {
		mode = 'system';
	}

	var button = document.createElement( 'button' );
	button.type = 'button';
	button.className = 'theme-toggle';

	function apply() {
		if ( mode === 'system' ) {
			root.removeAttribute( 'data-theme' );
		} else {
			root.setAttribute( 'data-theme', mode );
		}
		button.textContent = 'Theme: ' + mode;
		button.setAttribute( 'aria-label', 'Colour theme: ' + mode + '. Activate to change.' );
	}

	button.addEventListener( 'click', function () {
		mode = modes[ ( modes.indexOf( mode ) + 1 ) % modes.length ];
		try {
			localStorage.setItem( 'wt-theme', mode );
		} catch ( e ) {}
		apply();
	} );

	apply();
	// In the viewer, the button lives in the toolbar; the framed article has none
	// (it follows through the storage event below).
	var slot = document.querySelector( '[data-theme-slot]' );
	if ( slot ) {
		button.className = '';
		slot.appendChild( button );
	} else if ( window.self === window.top ) {
		document.body.appendChild( button );
	}
	window.addEventListener( 'storage', function ( e ) {
		if ( e.key === 'wt-theme' && modes.indexOf( e.newValue ) >= 0 ) {
			mode = e.newValue;
			apply();
		}
	} );
}() );
