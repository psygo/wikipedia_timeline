-- Run: luajit lua/test/test.lua   (from the project root)
package.path = 'lua/test/?.lua;' .. package.path
require( 'mw_mock' )
local chunk = assert( loadfile( 'lua/Module_TimelineRail.lua' ) )
local p = chunk()

local failures, count = 0, 0
local function check( name, ok, detail )
	count = count + 1
	if not ok then failures = failures + 1; print( 'FAIL ' .. name .. ( detail and ( '\n  ' .. detail ) or '' ) ) end
end
local function eq( name, got, want )
	check( name, got == want, 'got:  ' .. tostring( got ) .. '\n  want: ' .. tostring( want ) )
end
local function has( name, s, needle )
	check( name, s:find( needle, 1, true ) ~= nil, 'missing ' .. needle .. ' in ' .. s )
end

-- Tags must balance (the output is HTML; an unclosed one would swallow the rest of the article).
local VOID = { br = true, img = true }
local function balanced( html )
	local stack = {}
	for slash, tag in html:gmatch( '<(/?)([%w]+)[^>]*>' ) do
		tag = tag:lower()
		if not VOID[ tag ] and tag ~= 'templatestyles' then
			local selfClose = false
			if slash == '' then stack[ #stack + 1 ] = tag
			else
				if stack[ #stack ] ~= tag then return false, 'closing ' .. tag .. ' while ' .. tostring( stack[ #stack ] ) .. ' is open' end
				stack[ #stack ] = nil
			end
		end
	end
	return #stack == 0, 'unclosed: ' .. table.concat( stack, ',' )
end
local function wellFormed( name, html )
	local ok, why = balanced( html )
	check( name .. ' balanced', ok, why )
end

-- ---------------------------------------------------------------- item
local item = p.item( mw.frame( {}, { date = '1612', title = 'The Go academy', text = 'Text.' } ) )
eq( 'item', item,
	'<li class="wt-timeline__item wt-timeline__item--collapsible mw-collapsible" id="mw-customcollapsible-1612_The_Go_academy">'
	.. '<div class="wt-timeline__row mw-customtoggle-1612_The_Go_academy"><span class="wt-timeline__date">1612</span>'
	.. '<span class="wt-timeline__peek wt-timeline__peek--title">The Go academy</span></div>'
	.. '<div class="wt-timeline__body mw-collapsible-content"><div class="wt-timeline__events">'
	.. '<div class="wt-timeline__event"><span class="wt-timeline__title"></span><div class="wt-timeline__text">Text.</div></div>'
	.. '</div></div></li>' )
wellFormed( 'item', item )

local plain = p.item( mw.frame( {}, { date = '2017', collapsible = 'no', title = 'T', text = 'x', last = 'yes' } ) )
has( 'non-collapsible has no row', plain, '<li class="wt-timeline__item wt-timeline__item--last"><span class="wt-timeline__date">2017</span>' )
has( 'non-collapsible shows title in event', plain, '<span class="wt-timeline__title">T</span>' )
check( 'non-collapsible has no toggler', not plain:find( 'mw-customtoggle', 1, true ) )

local dateOnly = p.item( mw.frame( {}, { date = '1999' } ) )
check( 'date-only item is not collapsible', not dateOnly:find( 'mw-collapsible', 1, true ) )

local coll = p.item( mw.frame( {}, { date = '2006', collapsed = 'yes', summary = 'Two', id = 'e2006', events = '<div class="wt-timeline__event">E</div>' } ) )
has( 'collapsed class', coll, 'mw-collapsible mw-collapsed" id="mw-customcollapsible-e2006"' )
has( 'events peek uses summary', coll, '<span class="wt-timeline__peek">Two</span>' )

local img = p.item( mw.frame( {}, { date = '1', title = 'T', image = 'A b.jpg', caption = 'Cap', imagealt = 'alt' } ) )
has( 'image', img, '<span class="wt-timeline__image">[[File:A b.jpg|100x100px|alt=alt]]<span class="wt-timeline__caption">Cap</span></span>' )

local sub = p.item( mw.frame( {}, { date = '1', title = 'T', sub = '<li>s</li>' } ) )
has( 'sub timeline', sub, '<ol class="wt-timeline wt-timeline--sub"><li>s</li></ol>' )
wellFormed( 'sub', sub )

-- arguments given on the invoke itself work too, and the parent's win
local viaInvoke = p.item( mw.frame( { date = '1', title = 'A' }, { title = 'B' } ) )
has( 'parent args override', viaInvoke, '>B</span></div>' )

-- ---------------------------------------------------------------- section, rail, parallel, gap
local sec = p.section( mw.frame( {}, { title = 'Edo period', text = 'Intro', collapsed = 'yes', [ 1 ] = '<li>x</li>' } ) )
has( 'section collapsible id', sec, 'class="wt-timeline__item wt-timeline__item--section mw-collapsible mw-collapsed" id="mw-customcollapsible-section_Edo_period"' )
has( 'section row id', sec, 'class="wt-timeline__row" id="Edo_period"' )
has( 'section dot toggles', sec, '<span class="wt-timeline__dot mw-customtoggle-section_Edo_period"></span>' )
has( 'section extra', sec, '<div class="wt-timeline__section-extra"><div class="wt-timeline__event"><span class="wt-timeline__title"></span><div class="wt-timeline__text">Intro</div></div></div>' )
has( 'section body', sec, '<ol class="wt-timeline wt-timeline--section"><li>x</li></ol>' )
wellFormed( 'section', sec )

eq( 'rail', p.rail( mw.frame( {}, { [ 1 ] = '<li>a</li>' } ) ),
	'<templatestyles src="Template:TimelineRail/styles.css" /><ol class="wt-timeline"><li>a</li></ol>' )
has( 'rail column', p.rail( mw.frame( {}, { [ 1 ] = '', title = 'Players' } ) ),
	'<div class="wt-timelines__col"><div class="wt-timeline__heading">Players</div><ol class="wt-timeline"></ol></div>' )
has( 'parallel grouped', p.parallel( mw.frame( {}, { [ 1 ] = 'X', grouped = 'yes' } ) ), '<div class="wt-timelines wt-timelines--grouped">X</div>' )
eq( 'gap', p.gap(), '<li class="wt-timeline__item wt-timeline__item--gap" aria-hidden="true"></li>' )

-- ---------------------------------------------------------------- outline: parsing
local tree = p.parseOutline( [==[
!!== Lower Paleolithic ==
Intro line one
intro line two
!!* '''3.3 mya''': Oldest stone tools. <ref>r</ref>
continued text
* a sub-point
* another
!![[File:Hand axe.jpg|thumb|upright|A hand axe]]
!!* 1.8 mya ;; Hand axe ;; Acheulean.
!!=== Inner ===
!!* 400 kya ;; Fire
!!== Middle ==
!!* '''Date''' x
]==] )
eq( 'two top sections', #tree.children, 2 )
local lower = tree.children[ 1 ]
eq( 'section title', lower.title, 'Lower Paleolithic' )
eq( 'intro joined', table.concat( lower.intro, ' ' ), 'Intro line one intro line two' )
eq( 'lower has 2 items + 1 section', #lower.children, 3 )
local i1 = lower.children[ 1 ]
eq( 'bold date', i1.date, '3.3 mya' )
eq( 'text + continuation', table.concat( i1.text, ' ' ), 'Oldest stone tools. <ref>r</ref> continued text' )
eq( 'sub-bullets', #i1.subs, 2 )
local i2 = lower.children[ 2 ]
eq( 'image attaches to next item', i2.image, 'Hand axe.jpg' )
eq( 'image caption', i2.caption, 'A hand axe' )
eq( 'titled item', i2.title, 'Hand axe' )
eq( 'titled item text', i2.text[ 1 ], 'Acheulean.' )
local inner = lower.children[ 3 ]
eq( 'nested section', inner.title, 'Inner' )
eq( 'nested item title only', inner.children[ 1 ].title, 'Fire' )
eq( 'sibling section pops the stack', tree.children[ 2 ].title, 'Middle' )

-- ---------------------------------------------------------------- outline: rendering
local html = p.outline( mw.frame( {}, { text = [[
!!== A ==
!!* '''1''' one
!!* '''2''' two
!!== B ==
!!* '''3''' three
!!=== B inside ===
!!* '''4''' four
]] } ) )
wellFormed( 'outline', html )
local n = 0
for _ in html:gmatch( 'wt%-timeline__item%-%-section mw%-collapsible' ) do n = n + 1 end
eq( 'three sections', n, 3 )
local items = 0
for _ in html:gmatch( 'wt%-timeline__item%-%-collapsible' ) do items = items + 1 end
eq( 'four items', items, 4 )
has( 'styles first', html, '<templatestyles src="Template:TimelineRail/styles.css" />' )

-- an |id= prefix makes the generated ids independent of module state
local withId = p.outline( mw.frame( {}, { id = 'inv7', text = "!!== Zed ==\n!!* '''1''' one\n" } ) )
has( 'id prefix on items', withId, 'id="mw-customcollapsible-inv7_i1"' )
has( 'id prefix on sections', withId, 'id="mw-customcollapsible-inv7_s1"' )
has( 'sections are headings by default (table of contents)', withId, '<h3 class="wt-timeline__section-title">Zed</h3>' )
check( 'a heading has no row id of its own', not withId:find( 'id="Zed"', 1, true ) )
local plain = p.outline( mw.frame( {}, { id = 'inv8', toc = 'no', text = "!!== Zed ==\n!!* '''1''' one\n" } ) )
has( 'toc=no: row id stays the anchor', plain, 'id="Zed"' )
has( 'toc=no: the title is a span', plain, '<span class="wt-timeline__section-title">Zed</span>' )
check( 'toc=no: no heading', not plain:find( '<h%d' ) )
local multi = p.outline( mw.frame( {}, { id = 'inv12', text = "!![[File:A.jpg|150px|First]]\n!![[File:B.jpg|150px|Second]]\n!!* '''1''' x\n" } ) )
has( 'several pictures: a wrapping row', multi, '<div class="wt-timeline__images"><span class="wt-timeline__image" style="width:158px">[[File:A.jpg|150px|alt=]]<span class="wt-timeline__caption">First</span></span><span class="wt-timeline__image" style="width:158px">[[File:B.jpg|150px|alt=]]<span class="wt-timeline__caption">Second</span></span></div>' )
wellFormed( 'several pictures', multi )
local one = p.outline( mw.frame( {}, { id = 'inv13', text = "!![[File:A.jpg|150px|First]]\n!!* '''1''' x\n" } ) )
check( 'one picture: no row', not one:find( 'wt-timeline__images', 1, true ) )
local linkedCap = p.outline( mw.frame( {}, { id = 'inv14', text = "!![[File:A.jpg|150px|A [[Han dynasty|Han]] board, [[British Library]]]]\n!!* '''1''' x\n" } ) )
has( 'a link in a caption', linkedCap, '<span class="wt-timeline__caption">A [[Han dynasty|Han]] board, [[British Library]]</span>' )
local openHtml = p.outline( mw.frame( {}, { id = 'inv10', open = 'yes', text = "!!* '''1''' x\n" } ) )
has( 'open=yes: open rail', openHtml, '<ol class="wt-timeline wt-timeline--open">' )
has( 'closed by default', p.outline( mw.frame( {}, { id = 'inv11', text = "!!* '''1''' x\n" } ) ), '<ol class="wt-timeline">' )
local lvl = p.outline( mw.frame( {}, { id = 'inv9', toclevel = '2', text = "!!== A ==\n!!=== B ===\n!!==== C ====\n!!===== D =====\n!!====== E ======\n!!* '''1''' x\n" } ) )
has( 'toclevel=2: top section h2', lvl, '<h2 class="wt-timeline__section-title">A</h2>' )
has( 'nested section one level deeper', lvl, '<h3 class="wt-timeline__section-title">B</h3>' )
has( 'level is capped at 6', lvl, '<h6 class="wt-timeline__section-title">E</h6>' )
wellFormed( 'headings', lvl )

-- without |id=, different texts get different prefixes and equal texts the same one
local function firstId( text ) return p.outline( mw.frame( {}, { text = text } ) ):match( 'mw%-collapsible" id="mw%-customcollapsible%-([^"]+)"' ) end
check( 'default prefix differs per text', firstId( "!!* '''1''' a\n" ) ~= firstId( "!!* '''1''' b\n" ) )
eq( 'default prefix is stable', firstId( "!!* '''1''' a\n" ), firstId( "!!* '''1''' a\n" ) )

-- section anchors come from the visible words of a title with links
local linked = p.outline( mw.frame( {}, { id = 'k', toc = 'no', text = "!!== [[V-2 rocket|V-2]] and [[Moon]] ==\n!!* '''1''' one\n" } ) )
has( 'anchor from a linked title', linked, 'id="V-2_and_Moon"' )

-- ids are unique, also between two outlines on the page
local html2 = p.outline( mw.frame( {}, { text = "!!== A ==\n!!* '''1''' one\n" } ) )
local ids, dup = {}, false
for id in ( html .. html2 ):gmatch( ' id="([^"]+)"' ) do
	if ids[ id ] then dup = true; print( '  duplicate id ' .. id ) end
	ids[ id ] = true
end
check( 'ids unique across outlines', not dup )
local toggles = {}
for id in ( html .. html2 ):gmatch( 'mw%-customcollapsible%-([^"]+)"' ) do
	local t = html .. html2
	check( 'toggler exists for ' .. id, t:find( 'mw-customtoggle-' .. id .. '"', 1, true ) ~= nil )
end

local collapsedHtml = p.outline( mw.frame( {}, { text = "!!== A ==\n!!* '''1''' one\n", collapsed = 'all' } ) )
local c = 0
for _ in collapsedHtml:gmatch( 'mw%-collapsed' ) do c = c + 1 end
eq( 'collapsed=all', c, 2 )

local withSubs = p.outline( mw.frame( {}, { text = "!!* '''1''' one\n* a\n* b\n" } ) )
has( 'sub-bullets are a wikitext list', withSubs, 'one \n* a\n* b\n' )
wellFormed( 'subs', withSubs )

local nested = p.outline( mw.frame( {}, { text = "!!* '''1''' one\n* a\n** a1\n** a2\n*** a2x\n* b\n** b1\n" } ) )
has( 'nested sub-bullets (one * less)', nested, '\n* a\n** a1\n** a2\n*** a2x\n* b\n** b1\n' )
wellFormed( 'nested subs', nested )

-- the !* style: events are !*, a nested timeline is !**, every * line is plain wikitext
local bangText = "!!== A ==\n!!* '''1900''' one\n* a\n** a1\n!!** '''1901''' inner\n!!** 1902 ;; Title ;; inner two\n!!* '''2000''' two\n"
local bangHtml = p.outline( mw.frame( {}, { text = bangText } ) )
has( 'bang: list kept as written', bangHtml, 'one \n* a\n** a1\n' )
has( 'bang: nested timeline', bangHtml, 'wt-timeline wt-timeline--sub' )
has( 'bang: inner event', bangHtml, 'inner' )
has( 'bang: next event after the nested one', bangHtml, '2000' )
wellFormed( 'bang', bangHtml )
local bangTree = p.parseOutline( bangText )
eq( 'bang: two top events', #bangTree.children[ 1 ].children, 2 )
eq( 'bang: two inner events', #bangTree.children[ 1 ].children[ 1 ].children, 2 )
local legacy = p.parseOutline( "!!* '''1''' a\n!!* '''2''' b\n* c\n" )
eq( 'legacy: * stays an event', #legacy.children, 2 )

-- the text is passed through untouched: links, refs, templates
local rich = p.outline( mw.frame( {}, { text = "!!* '''c. 1651''': [[Huang Longshi|Huang]] is born.<ref name=\"a\">x</ref>\n" } ) )
has( 'wikilink preserved', rich, '[[Huang Longshi|Huang]] is born.<ref name="a">x</ref>' )

print( string.format( '%d checks, %d failed', count, failures ) )
os.exit( failures == 0 and 0 or 1 )
