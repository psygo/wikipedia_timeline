-- Module:TimelineGantt (reads the outline syntax through Module:TimelineRail).
-- Run: luajit lua/test/test_gantt.lua   (from the project root)
package.path = 'lua/test/?.lua;' .. package.path
require( 'mw_mock' )
local rail = assert( loadfile( 'lua/Module_TimelineRail.lua' ) )()
local gantt = assert( loadfile( 'lua/Module_TimelineGantt.lua' ) )()
package.preload[ 'Module:TimelineRail' ] = function() return rail end

local failures, count = 0, 0
local function check( name, ok, detail )
	count = count + 1
	if not ok then failures = failures + 1; print( 'FAIL ' .. name .. ( detail and ( '\n  ' .. detail ) or '' ) ) end
end
local function has( name, s, needle ) check( name, s:find( needle, 1, true ) ~= nil, 'missing ' .. needle .. ' in ' .. s ) end
local function lacks( name, s, needle ) check( name, s:find( needle, 1, true ) == nil, 'unexpected ' .. needle .. ' in ' .. s ) end
local function same( name, got, want ) check( name, got == want, 'got ' .. tostring( got ) .. ', want ' .. tostring( want ) ) end

-- dates
local function range( s ) local a, b, o = gantt.parseDate( s ); return a, b, o end
local a, b = range( '3000 BC – 500 BC' ); same( 'bc range start', a, -3000 ); same( 'bc range end', b, -500 )
a, b = range( '3000–2500 BC' ); same( 'shared era start', a, -3000 ); same( 'shared era end', b, -2500 )
a, b = range( "'''800 BC''' - 146 AD" ); same( 'mixed eras start', a, -800 ); same( 'mixed eras end', b, 146 )
a, b = range( 'c. 1800 – 1600 BC' ); same( 'circa start', a, -1800 ); same( 'circa end', b, -1600 )
a, b = range( '1846' ); same( 'single year start', a, 1846 ); same( 'single year end', b, 1846 )
a, b = range( '500 BC' ); same( 'single bc', a, -500 )
a, b = range( '1,200 – 1,500' ); same( 'commas', a, 1200 ); same( 'commas end', b, 1500 )
local o
a, b, o = range( '1950 – present' ); same( 'present start', a, 1950 ); check( 'present is open', o == true ); check( 'present ends now', b >= 2024 )
a, b = range( '800 BCE – 146 BCE' ); same( 'bce', a, -800 )
a = range( 'Unknown' ); check( 'unreadable gives nil', a == nil )
a = range( nil ); check( 'nil gives nil', a == nil )

-- the chart
local text = "!!== Ancient ==\n!!* 3000 BC – 1000 BC ;; Egyptian ;; Hieroglyphs\n!!* '''800 BC – 146 BC''' Greek\n!!== Modern ==\n!!* 1202 ;; Liber Abaci\n!!* 1950 – present ;; Computing\n!!* Unknown ;; No date"
local out = gantt.gantt( mw.frame( { text = text } ) )
has( 'styles', out, 'Module:TimelineGantt/styles.css' )
has( 'container', out, '<div class="wt-gantt">' )
has( 'section title', out, '<span class="wt-gantt__section-title">Ancient</span>' )
has( 'second section has the second colour', out, 'wt-gantt__section wt-gantt__c2' )
has( 'row label from the title', out, '>Egyptian<span class="wt-gantt__when">3000 BC - 1000 BC</span>' )
has( 'row label from the text', out, '>Greek<' )
has( 'bar', out, 'class="wt-gantt__bar"' )
has( 'bar position starts at the left', out, 'left:0%;width:' )
has( 'milestone is a dot', out, 'class="wt-gantt__dot"' )
has( 'open bar', out, 'wt-gantt__bar--open' )
has( 'scale', out, 'class="wt-gantt__scale"' )
has( 'bc tick', out, '3000 BC' )
has( 'ad tick', out, ' AD' )
local bars = select( 2, out:gsub( 'class="wt%-gantt__bar', '' ) )
same( 'three bars (two ranges and the open one)', bars, 3 )
local rows = select( 2, out:gsub( 'class="wt%-gantt__row wt', '' ) )
same( 'five rows', rows, 5 )

-- an undated row keeps its label and has no bar
local lone = gantt.gantt( mw.frame( { text = "!!* 100 – 200 ;; A\n!!* nothing ;; B" } ) )
has( 'undated row label', lone, '>B<' )
same( 'one bar only', ( select( 2, lone:gsub( 'class="wt%-gantt__bar', '' ) ) ), 1 )

-- scale limits and ticks
local fixed = gantt.gantt( mw.frame( { text = '!!* 100 – 200 ;; A', from = '0', to = '400', ticks = '100' } ) )
has( 'bar within a given scale', fixed, 'left:25%;width:25%' )
has( 'tick at 300', fixed, 'left:75%' )
has( 'plain years without BC', fixed, '>300<' )

-- nested events become indented rows
local nested = gantt.gantt( mw.frame( { text = "!!* 100 – 400 ;; Parent\n!!** 150 – 200 ;; Child" } ) )
has( 'nested row indented', nested, 'padding-left:1em' )

-- escaping: the tooltip is escaped
local evil = gantt.gantt( mw.frame( { text = '!!* 100 "x" – 200 ;; A' } ) )
lacks( 'no raw quote in the title attribute', evil, 'title="100 "x"' )

-- from a template: the parent's arguments win
local viaTpl = gantt.gantt( mw.frame( {}, { text = '!!* 1 – 2 ;; T' } ) )
has( 'template args', viaTpl, '>T<' )

-- nothing to draw
same( 'empty', gantt.gantt( mw.frame( { text = '' } ) ), '' )
same( 'no readable date at all', gantt.gantt( mw.frame( { text = '!!* nothing ;; B' } ) ), '' )

print( count .. ' checks, ' .. failures .. ' failed' )
os.exit( failures == 0 and 0 or 1 )
