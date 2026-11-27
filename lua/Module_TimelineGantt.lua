-- Module:TimelineGantt
-- The outline syntax of Module:TimelineRail drawn as a Gantt chart: one row per event, a bar from its
-- start to its end on a shared time scale. A companion of the timeline: the same text, another view
-- (works on its own too, and as a view of Module:ViewSwitcher):
--
--   {{#invoke:TimelineGantt|gantt
--   |text=
--   !!== Ancient ==
--   !!* 3000 BC – 500 BC ;; Egyptian ;; Hieroglyphic numerals.
--   !!* '''800 BC – 146 BC''' Greek
--   !!== Medieval ==
--   !!* 500 – 1500 ;; Indian
--   !!* 1202 ;; Liber Abaci
--   !!* 1950 – present ;; Computing
--   }}
--
--   Rows:      each event of the outline; the label is its title (or its text if it has no title).
--   Dates:     "3000 BC – 500 BC", "3000–2500 BC" (BC/BCE/AD/CE; an era is shared by both ends when
--              only the last one has it), "1846", "c. 1800 – 1600 BC", "500 – present" (now; the bar
--              fades out). A date that is a single year is a dot (a milestone). A date that cannot be
--              read gives a row without a bar.
--   Sections:  a section line is a heading row; each top-level section has its own colour.
--   Nested:    the events of a nested timeline (!!**) are rows too, indented.
--   Options:   |from= and |to= (the ends of the scale; default: the data), |ticks= (the step, in years;
--              default: a round number giving about six), |parser=TimelineRail/sandbox (test parser).
--
-- Plain HTML and CSS (positions in %), no script: it also shows in the Wikipedia app.
local p = {}

local STYLES = 'Module:TimelineGantt/styles.css'
local PALETTE = 6      -- colours: wt-gantt__c1 ... wt-gantt__c6 (see the styles)

local function esc( s ) return mw.text.encode( s ) end

local function trim( s )
	if s == nil then return nil end
	s = tostring( s ):match( '^%s*(.-)%s*$' )
	if s == '' then return nil end
	return s
end

local function getArgs( frame )
	local args = {}
	for k, v in pairs( frame.args ) do args[ k ] = trim( v ) end
	local parent = frame:getParent()
	if parent then
		for k, v in pairs( parent.args ) do
			local t = trim( v )
			if t ~= nil then args[ k ] = t end
		end
	end
	return args
end

local function parse( text, parser ) return require( 'Module:' .. ( parser or 'TimelineRail' ) ).parseOutline( text ) end

local function thisYear()
	local ok, y = pcall( function() return tonumber( os.date( '%Y' ) ) end )
	return ok and y or 2026
end

-- ------------------------------------------------------------------ dates
-- Plain text of a date: no bold, links, notes, tags.
local function plain( s )
	s = s:gsub( '<ref[^>]*/>', '' ):gsub( '<ref.-</ref>', '' ):gsub( '<[^>]*>', '' )
	s = s:gsub( '%[%[[^%]|]*|([^%]]*)%]%]', '%1' ):gsub( '%[%[([^%]]*)%]%]', '%1' ):gsub( "'+", '' )
	s = s:gsub( '&nbsp;', ' ' ):gsub( '&ndash;', '-' ):gsub( '&mdash;', '-' )
	s = s:gsub( '\226\128[\147\148]', '-' ):gsub( '\226\136\146', '-' )   -- en dash, em dash, minus sign
	return trim( s ) or ''
end

-- one end of a range: number and era ('BC', 'AD' or nil), or 'now'
local function readEnd( s )
	local l = s:lower()
	if l:match( 'present' ) or l:match( '^%s*now' ) or l:match( 'ongoing' ) or l:match( 'today' ) then return { now = true } end
	local n = s:match( '%d[%d,]*' )
	if not n then return nil end
	n = tonumber( ( n:gsub( ',', '' ) ) )
	local era
	if l:match( 'bce' ) or l:match( '%f[%a]bc%f[%A]' ) or l:match( 'b%.c%.' ) then era = 'BC'
	elseif l:match( '%f[%a]ce%f[%A]' ) or l:match( '%f[%a]ad%f[%A]' ) or l:match( 'a%.d%.' ) then era = 'AD' end
	return { n = n, era = era }
end

local function value( e )
	if e.now then return thisYear() end
	return e.era == 'BC' and -e.n or e.n
end

-- "3000 BC - 500 BC" -> start, finish (numbers; BC is negative), open (ends now); nil if unreadable
function p.parseDate( raw )
	local s = plain( raw or '' )
	if s == '' then return nil end
	local a, b = s:match( '^(.-)%s*%-%s*(.+)$' )
	if not a then a, b = s:match( '^(.-)%s+to%s+(.+)$' ) end
	local ea, eb
	if a and a ~= '' then ea, eb = readEnd( a ), readEnd( b ) else ea = readEnd( s ) end
	if not ea then return nil end
	if not eb then
		if a and a ~= '' and b then return nil end
		return value( ea ), value( ea ), false
	end
	-- an era written on one end only: the first takes the second's; the second is AD unless that would
	-- end before the start
	if not ea.now and not ea.era then ea.era = eb.era or 'AD' end
	if not eb.now and not eb.era then
		eb.era = ( ea.era == 'BC' and eb.n <= ea.n ) and 'BC' or 'AD'
	end
	local x, y = value( ea ), value( eb )
	if y < x then x, y = y, x end
	return x, y, eb.now == true
end

local function yearLabel( y, anyBC )
	if y < 0 then return ( -y ) .. ' BC' end
	if anyBC then return y == 0 and '1 AD' or ( y .. ' AD' ) end
	return tostring( y )
end

local function niceStep( span )
	local raw = span / 6
	local mag = 10 ^ math.floor( math.log( raw ) / math.log( 10 ) )
	for _, m in ipairs( { 1, 2, 2.5, 5, 10 } ) do
		if m * mag >= raw then return m * mag end
	end
	return 10 * mag
end

-- a number with at most two decimals and no trailing zeros
local function num( x )
	local s = string.format( '%.2f', x )
	if s:find( '.', 1, true ) then s = s:gsub( '0+$', '' ):gsub( '%.$', '' ) end
	return s
end

-- position of a year on the scale, in % (kept inside the chart)
local function pct( v, from, span )
	local x = ( v - from ) / span * 100
	if x < 0 then x = 0 elseif x > 100 then x = 100 end
	return num( x )
end

-- ------------------------------------------------------------------ chart
local function label( ch )
	if ch.title then return ch.title end
	return trim( table.concat( ch.text or {}, ' ' ) ) or ''
end

function p.gantt( frame )
	local a = getArgs( frame )
	local tree = parse( a.text or a[ 1 ] or '', a.parser )

	-- flatten the outline into rows
	local rows, lo, hi, anyBC = {}, nil, nil, false
	local colour = 0
	local function walk( node, depth, col, sub )
		for _, ch in ipairs( node.children ) do
			if ch.section then
				if depth == 0 then colour = colour + 1 end
				local c = depth == 0 and colour or col
				rows[ #rows + 1 ] = { section = ch, depth = depth, colour = c }
				walk( ch, depth + 1, c, false )
			else
				local x, y, open = p.parseDate( ch.date )
				local r = { item = ch, depth = depth, colour = col, sub = sub, from = x, to = y, open = open }
				rows[ #rows + 1 ] = r
				if x then
					lo = math.min( lo or x, x ); hi = math.max( hi or y, y )
					if x < 0 then anyBC = true end
				end
				if ch.children then walk( ch, depth, col, true ) end
			end
		end
	end
	walk( tree, 0, 1, false )

	local from, to = p.parseDate( a.from ), nil
	if a.to then to = select( 2, p.parseDate( a.to ) ) end
	if a.from then from = ( p.parseDate( a.from ) ) end
	from = from or lo
	to = to or hi
	if not from or not to then return '' end
	if to <= from then to = from + 1 end
	local span = to - from
	if from < 0 then anyBC = true end

	local out = {}
	local function add( s ) out[ #out + 1 ] = s end
	add( frame:extensionTag( 'templatestyles', '', { src = STYLES } ) )
	add( '<div class="wt-gantt"><div class="wt-gantt__plot">' )

	-- the grid: a line at every tick
	local step = tonumber( a.ticks ) or niceStep( span )
	if step <= 0 then step = niceStep( span ) end
	local ticks = {}
	local t = math.ceil( from / step ) * step
	local guard = 0
	while t <= to and guard < 60 do
		ticks[ #ticks + 1 ] = t
		t = t + step; guard = guard + 1
	end
	add( '<div class="wt-gantt__grid" aria-hidden="true">' )
	for _, tk in ipairs( ticks ) do
		add( '<span style="left:' .. pct( tk, from, span ) .. '%"></span>' )
	end
	add( '</div><ol class="wt-gantt__rows">' )

	for _, r in ipairs( rows ) do
		if r.section then
			local intro = trim( table.concat( r.section.intro or {}, ' ' ) )
			add( '<li class="wt-gantt__section wt-gantt__c' .. ( ( r.colour - 1 ) % PALETTE + 1 ) .. '"'
				.. ( r.depth > 0 and ( ' style="padding-left:' .. ( r.depth * 1.2 ) .. 'em"' ) or '' ) .. '>'
				.. '<span class="wt-gantt__section-title">' .. r.section.title .. '</span>'
				.. ( intro and ( ' <span class="wt-gantt__section-intro">' .. intro .. '</span>' ) or '' ) .. '</li>' )
		else
			local ch = r.item
			local when = trim( ch.date )
			add( '<li class="wt-gantt__row wt-gantt__c' .. ( ( r.colour - 1 ) % PALETTE + 1 ) .. '">'
				.. '<span class="wt-gantt__label"' .. ( r.sub and ' style="padding-left:1em"' or '' ) .. '>' .. label( ch )
				.. ( when and ( '<span class="wt-gantt__when">' .. plain( when ) .. '</span>' ) or '' ) .. '</span>'
				.. '<span class="wt-gantt__track">' )
			if r.from then
				local left = pct( r.from, from, span )
				if r.from == r.to then
					add( '<span class="wt-gantt__dot" style="left:' .. left .. '%" title="' .. esc( plain( when or '' ) ) .. '"></span>' )
				else
					local width = num( tonumber( pct( r.to, from, span ) ) - tonumber( left ) )
					add( '<span class="wt-gantt__bar' .. ( r.open and ' wt-gantt__bar--open' or '' ) .. '" style="left:' .. left
						.. '%;width:' .. width .. '%" title="' .. esc( plain( when or '' ) ) .. '"></span>' )
				end
			end
			add( '</span></li>' )
		end
	end
	add( '</ol></div>' )

	-- the scale
	add( '<div class="wt-gantt__scale" aria-hidden="true">' )
	for _, tk in ipairs( ticks ) do
		local x = tonumber( pct( tk, from, span ) )
		add( '<span' .. ( x < 4 and ' class="wt-gantt__tick--first"' or x > 96 and ' class="wt-gantt__tick--last"' or '' )
			.. ' style="left:' .. pct( tk, from, span ) .. '%">' .. yearLabel( tk, anyBC ) .. '</span>' )
	end
	add( '</div></div>' )
	return table.concat( out )
end

return p
