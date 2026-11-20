-- Module:ViewSwitcher, Module:OutlineList and Module:OutlineTable.
-- Run: luajit lua/test/test_switcher.lua   (from the project root)
package.path = 'lua/test/?.lua;' .. package.path
require( 'mw_mock' )
local rail = assert( loadfile( 'lua/Module_TimelineRail.lua' ) )()
local switcher = assert( loadfile( 'lua/Module_ViewSwitcher.lua' ) )()
local olist = assert( loadfile( 'lua/Module_OutlineList.lua' ) )()
local otable = assert( loadfile( 'lua/Module_OutlineTable.lua' ) )()
package.preload[ 'Module:TimelineRail' ] = function() return rail end
package.preload[ 'Module:OutlineList' ] = function() return olist end
package.preload[ 'Module:OutlineTable/sandbox' ] = function() return otable end

local failures, count = 0, 0
local function check( name, ok, detail )
	count = count + 1
	if not ok then failures = failures + 1; print( 'FAIL ' .. name .. ( detail and ( '\n  ' .. detail ) or '' ) ) end
end
local function has( name, s, needle ) check( name, s:find( needle, 1, true ) ~= nil, 'missing ' .. needle .. ' in ' .. s ) end
local function lacks( name, s, needle ) check( name, s:find( needle, 1, true ) == nil, 'unexpected ' .. needle .. ' in ' .. s ) end
local function count_of( s, needle ) local n = 0; for _ in s:gmatch( needle:gsub( '%p', '%%%0' ) ) do n = n + 1 end return n end

-- views you write yourself
local out = switcher.switch( mw.frame( { label1 = 'A', view1 = 'alpha', label2 = 'B', view2 = '* beta', default = '2' } ) )
has( 'styles', out, 'Module:ViewSwitcher/styles.css' )
has( 'container', out, '<div class="viewswitcher">' )
has( 'label a', out, 'data-vs-label="A"' )
has( 'label b', out, 'data-vs-label="B"' )
has( 'default is second', out, 'class="viewswitcher__view viewswitcher__view--default" data-vs-label="B"' )
lacks( 'first not default', out, 'viewswitcher__view--default" data-vs-label="A"' )
has( 'newline before wikitext so a list starts a line', out, '>\n* beta\n</div>' )

-- from a template: the parent's arguments win
out = switcher.switch( mw.frame( {}, { label1 = 'X', view1 = 'x', label2 = 'Y', view2 = 'y' } ) )
has( 'template args', out, 'data-vs-label="Y"' )

-- nothing to show
has( 'error without views', switcher.switch( mw.frame( {} ) ), 'class="error"' )

-- views drawn from one set of data
local text = "== Early ==\n* '''1612''' The Go academy opens\n* 1846 ;; The Ear-Reddening Game ;; Move 127 [[Shusaku]]\n** a sub point\n== Modern ==\n* '''2016''' AlphaGo wins"
out = switcher.switch( mw.frame( {
	views = 'Timeline=TimelineRail.outline; List=OutlineList.list; Table=OutlineTable/sandbox.table',
	id = 'demo', text = text } ) )
has( 'three views', out, 'data-vs-label="Timeline"' )
has( 'list label', out, 'data-vs-label="List"' )
has( 'table label', out, 'data-vs-label="Table"' )
check( 'three view divs', count_of( out, 'class="viewswitcher__view' ) == 3 )
has( 'timeline view', out, 'wt-timeline__item' )
has( 'timeline id from args', out, 'mw-customcollapsible-demo_i1' )
has( 'list view', out, '<ul><li>' )
has( 'list date', out, "'''1612'''" )
has( 'list title', out, "'''The Ear-Reddening Game'''" )
has( 'list sub', out, '<ul><li>a sub point</li></ul>' )
has( 'list section', out, '<p><b>Early</b></p>' )
has( 'table', out, '<table class="wikitable">' )
has( 'table headers', out, '<th scope="col">Date</th><th scope="col">Title</th><th scope="col">Description</th>' )
lacks( 'no image column without images', out, '>Image<' )
has( 'table section row', out, 'colspan="3"' )
has( 'table link kept', out, '[[Shusaku]]' )
lacks( 'no timeline ids in list view', out:match( 'data%-vs%-label="List".-</div>' ) or '', 'id="' )
lacks( 'views argument not passed on', out, 'views=' )


-- the default view: * on a label, |default= as a label or a number
out = switcher.switch( mw.frame( { label1 = 'A', view1 = 'a', label2 = '*B', view2 = 'b', label3 = 'C', view3 = 'c' } ) )
has( 'star default', out, 'viewswitcher__view--default" data-vs-label="B"' )
has( 'star removed from label', out, 'data-vs-label="B"' )
out = switcher.switch( mw.frame( { label1 = 'A', view1 = 'a', label2 = 'Table', view2 = 'b', default = 'table' } ) )
has( 'default by label, any case', out, 'viewswitcher__view--default" data-vs-label="Table"' )
out = switcher.switch( mw.frame( { label1 = 'A', view1 = 'a', label2 = 'B', view2 = 'b', default = '9' } ) )
has( 'bad default falls back to the first', out, 'viewswitcher__view--default" data-vs-label="A"' )
out = switcher.switch( mw.frame( { views = 'T=TimelineRail.outline; *List=OutlineList.list', text = '* x' } ) )
has( 'star in views=', out, 'viewswitcher__view--default" data-vs-label="List"' )

-- "@name": a view that is the text of an argument, as it is
out = switcher.switch( mw.frame( { views = '*Timeline=TimelineRail.outline; Original=@orig', text = '* one', orig = '* the original' } ) )
has( 'at-arg view', out, '\n* the original\n' )
check( 'at-arg not passed on to the functions', not out:find( 'the original</div></div></li>', 1, true ) )

-- references only in the default view
local REF = "\127'\"`UNIQ--ref-0000000A-QINU`\"'\127"
out = switcher.switch( mw.frame( { views = '*Timeline=TimelineRail.outline; List=OutlineList.list', text = '* one ' .. REF } ) )
check( 'ref kept in the default view', count_of( out, 'UNIQ--ref-0000000A' ) == 1, 'count ' .. count_of( out, 'UNIQ--ref-0000000A' ) )
out = switcher.switch( mw.frame( { views = '*Timeline=TimelineRail.outline; List=OutlineList.list', text = '* one ' .. REF, refs = 'all' } ) )
check( 'refs=all keeps every one', count_of( out, 'UNIQ--ref-0000000A' ) == 2 )

-- bad function name
local ok, err = pcall( switcher.switch, mw.frame( { views = 'X=OutlineList.nope', text = 'a' } ) )
check( 'missing function is an error', not ok and tostring( err ):find( 'no function', 1, true ) ~= nil, tostring( err ) )

-- images and untitled items
out = otable.table( mw.frame( { text = "[[File:Moon.jpg|thumb|300px|The Moon]]\n* '''1968''' Earthrise" } ) )
has( 'image column', out, '>Image<' )
has( 'image', out, '[[File:Moon.jpg|thumb|none|300px|The Moon]]' )
lacks( 'no title column', out, '>Title<' )
out = olist.list( mw.frame( { text = "[[File:Moon.jpg|thumb|300px|The Moon]]\n* '''1968''' Earthrise" } ) )
has( 'list image', out, '[[File:Moon.jpg|thumb|none|300px|The Moon]]' )
has( 'list untitled', out, "<li>'''1968''' – Earthrise" )

print( count .. ' checks, ' .. failures .. ' failed' )
os.exit( failures == 0 and 0 or 1 )
