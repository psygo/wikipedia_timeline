/*
 * What goes on User:Fanaro009/common.js (https://en.wikipedia.org/wiki/User:Fanaro009/common.js).
 * Add these lines to the page (keep whatever is already there). Each script lives on its own page,
 * copied from the file of the same name in this folder:
 *
 *   User:Fanaro009/ViewSwitcher.js         <- userscript/ViewSwitcher.js
 *   User:Fanaro009/Timeline-toolbar.js     <- userscript/Timeline-toolbar.js
 *   User:Fanaro009/Timeline-collapse-all.js <- userscript/Timeline-collapse-all.js
 *
 * Save those pages first, then this one, then hard-refresh (Ctrl+Shift+R / Cmd+Shift+R).
 */

// The View button (Timeline / List / Table) on pages that use Module:ViewSwitcher.
importScript( 'User:Fanaro009/ViewSwitcher.js' );

// A Timeline drop-down in the edit toolbar that inserts timeline skeletons.
importScript( 'User:Fanaro009/Timeline-toolbar.js' );

// Double-click a dot to collapse or expand a whole timeline.
importScript( 'User:Fanaro009/Timeline-collapse-all.js' );
