-- Module:TimelineRail
-- Vertical timeline: a date column, a rail with dots, collapsible items and sections.
-- Same markup and class names as the template family Template:TimelineRail (the stylesheet
-- Template:TimelineRail/styles.css is shared), generated here instead of with parser functions.
--
-- Entry points (all read the arguments of the template that invoked them, or their own):
--   rail      {{#invoke:TimelineRail|rail}}      a timeline; |1= items and sections, |title= makes it a column
--   parallel  {{#invoke:TimelineRail|parallel}}  timelines side by side; |1= columns, |grouped=yes
--   item      {{#invoke:TimelineRail|item}}      one dot with a date and events
--   section   {{#invoke:TimelineRail|section}}   a titled, collapsible, nestable group
--   gap       {{#invoke:TimelineRail|gap}}       an empty slot to line up grouped columns
--   outline   {{#invoke:TimelineRail|outline}}   a whole timeline from one text (see the doc page);
--             its sections are headings of the page (table of contents) unless |toc=no, level |toclevel= (3)
--
-- "outline" is the one that scales: the content is passed once and built once, so a timeline of
-- hundreds of items stays far below the post-expand include size limit that item-by-item
-- templates run into.

local p = {}

local STYLES = 'Template:TimelineRail/styles.css'

-- ------------------------------------------------------------------ helpers
local function trim( s )
	if s == nil then return nil end
	s = tostring( s ):match( '^%s*(.-)%s*$' )
	if s == '' then return nil end
	return s
end

local function esc( s )
	return mw.text.encode( s )
end

local function styles( frame )
	return frame:extensionTag( 'templatestyles', '', { src = STYLES } )
end

-- Arguments of the calling template if there is one, else of the #invoke itself; trimmed, empty = nil.
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

-- Anchors are made from the visible words: [[a|b]] -> b, [[a]] -> a, no ''' or ''.
local function anchor( s )
	s = s:gsub( '%[%[[^%]|]*|([^%]]*)%]%]', '%1' ):gsub( '%[%[([^%]]*)%]%]', '%1' ):gsub( "'+", '' )
	return mw.uri.anchorEncode( s )
end

-- ------------------------------------------------------------------ rendering
-- Each renderer takes a plain table (the "model") and returns an HTML/wikitext string.

-- The framed picture is as wide as the picture (3 px padding and a 1 px border on each side), so a longer caption wraps
-- inside the box instead of widening it. Only known when the size is given in pixels.
local function boxStyle( size )
	local n = size and tostring( size ):match( '^(%d+)px$' )
	return n and ( ' style="width:' .. ( tonumber( n ) + 8 ) .. 'px"' ) or ''
end

-- ev: { title, text, image, imagesize, imagealt, caption }
local function renderEvent( ev, hideTitle )
	local out = { '<div class="wt-timeline__event"><span class="wt-timeline__title">',
		hideTitle and '' or ( ev.title or '' ), '</span>' }
	if ev.text then
		out[ #out + 1 ] = '<div class="wt-timeline__text">' .. ev.text .. '</div>'
	end
	if ev.images and #ev.images > 1 then
		-- several pictures: one row of framed pictures that wraps when there is no more room
		out[ #out + 1 ] = '<div class="wt-timeline__images">'
		for _, f in ipairs( ev.images ) do
			out[ #out + 1 ] = '<span class="wt-timeline__image"' .. boxStyle( f[ 3 ] ) .. '>[[File:' .. f[ 1 ] .. '|' .. ( f[ 3 ] or '100x100px' )
				.. '|alt=]]' .. ( f[ 2 ] and ( '<span class="wt-timeline__caption">' .. f[ 2 ] .. '</span>' ) or '' ) .. '</span>'
		end
		out[ #out + 1 ] = '</div>'
	elseif ev.image then
		out[ #out + 1 ] = '<span class="wt-timeline__image"' .. boxStyle( ev.imagesize ) .. '>[[File:' .. ev.image .. '|'
			.. ( ev.imagesize or '100x100px' ) .. '|alt=' .. ( ev.imagealt or '' ) .. ']]'
		if ev.caption then out[ #out + 1 ] = '<span class="wt-timeline__caption">' .. ev.caption .. '</span>' end
		out[ #out + 1 ] = '</span>'
	end
	out[ #out + 1 ] = '</div>'
	return table.concat( out )
end

-- item: { date, title, summary, text, image, imagesize, imagealt, caption, id, collapsed, collapsible,
--         last, events (string of rendered events), sub (string of rendered items) }
local function renderItem( it )
	local collapsible = it.collapsible ~= false
		and ( it.title or it.text or it.image or it.events or it.sub ) ~= nil
	local id = it.id or anchor( ( it.date or '' ) .. '_' .. ( it.title or it.summary or '' ) )
	local out = {}
	if collapsible then
		out[ #out + 1 ] = '<li class="wt-timeline__item wt-timeline__item--collapsible mw-collapsible'
			.. ( it.collapsed and ' mw-collapsed' or '' )
			.. ( it.last and ' wt-timeline__item--last' or '' )
			.. '" id="mw-customcollapsible-' .. esc( id ) .. '">'
		out[ #out + 1 ] = '<div class="wt-timeline__row mw-customtoggle-' .. esc( id ) .. '">'
			.. '<span class="wt-timeline__date">' .. ( it.date or '' ) .. '</span>'
		if it.events then
			out[ #out + 1 ] = '<span class="wt-timeline__peek">' .. ( it.summary or it.title or '' ) .. '</span>'
		else
			out[ #out + 1 ] = '<span class="wt-timeline__peek wt-timeline__peek--title">' .. ( it.title or '' ) .. '</span>'
		end
		out[ #out + 1 ] = '</div><div class="wt-timeline__body mw-collapsible-content">'
	else
		out[ #out + 1 ] = '<li class="wt-timeline__item' .. ( it.last and ' wt-timeline__item--last' or '' ) .. '">'
		out[ #out + 1 ] = '<span class="wt-timeline__date">' .. ( it.date or '' ) .. '</span>'
	end
	out[ #out + 1 ] = '<div class="wt-timeline__events">' .. ( it.events or renderEvent( it, collapsible ) ) .. '</div>'
	if it.sub then
		out[ #out + 1 ] = '<ol class="wt-timeline wt-timeline--sub">' .. it.sub .. '</ol>'
	end
	if collapsible then out[ #out + 1 ] = '</div>' end
	out[ #out + 1 ] = '</li>'
	return table.concat( out )
end

-- section: { title, id, collapsed, text, image, imagesize, imagealt, caption, body (rendered children),
--             level (2-6: the title is then a real <hN> heading, so the page's table of contents lists it) }
local function renderSection( sec )
	local id = sec.toggleId or sec.id or anchor( 'section_' .. ( sec.title or '' ) )
	local rowId = sec.id or anchor( sec.title or '' )
	local extra = ''
	if sec.text or sec.image then
		extra = '<div class="wt-timeline__section-extra">'
			.. renderEvent( { text = sec.text, image = sec.image, imagesize = sec.imagesize,
				imagealt = sec.imagealt, caption = sec.caption } ) .. '</div>'
	end
	return '<li class="wt-timeline__item wt-timeline__item--section mw-collapsible'
		.. ( sec.collapsed and ' mw-collapsed' or '' ) .. '" id="mw-customcollapsible-' .. esc( id ) .. '">'
		.. '<div class="wt-timeline__row mw-customtoggle-' .. esc( id ) .. '"'
		-- a heading gets its own anchor from MediaWiki (the same words, _2 for a repeat): no id twice
		.. ( sec.level and '' or ' id="' .. esc( rowId ) .. '"' ) .. '>'
		.. ( sec.level
			and ( '<h' .. sec.level .. ' class="wt-timeline__section-title">' .. ( sec.title or '' ) .. '</h' .. sec.level .. '>' )
			or ( '<span class="wt-timeline__section-title">' .. ( sec.title or '' ) .. '</span>' ) )
		.. extra .. '</div>'
		.. '<div class="wt-timeline__body mw-collapsible-content"><ol class="wt-timeline wt-timeline--section">'
		.. ( sec.body or '' ) .. '</ol></div></li>'
end

-- open: the rail fades out below the last dot instead of ending there (a list that is not finished)
local function renderRail( body, title, open )
	local ol = '<ol class="wt-timeline' .. ( open and ' wt-timeline--open' or '' ) .. '">' .. ( body or '' ) .. '</ol>'
	if title then
		return '<div class="wt-timelines__col"><div class="wt-timeline__heading">' .. title .. '</div>' .. ol .. '</div>'
	end
	return ol
end

-- ------------------------------------------------------------------ template-style entry points
function p.event( frame )
	local a = getArgs( frame )
	return renderEvent( { title = a.title, text = a.text, image = a.image, imagesize = a.imagesize,
		imagealt = a.imagealt, caption = a.caption } )
end

function p.item( frame )
	local a = getArgs( frame )
	return renderItem( {
		date = a.date, title = a.title, summary = a.summary, text = a.text, image = a.image,
		imagesize = a.imagesize, imagealt = a.imagealt, caption = a.caption, id = a.id,
		collapsed = a.collapsed ~= nil, collapsible = a.collapsible ~= 'no', last = a.last ~= nil,
		events = a.events, sub = a.sub,
	} )
end

function p.section( frame )
	local a = getArgs( frame )
	return renderSection( {
		title = a.title, id = a.id, collapsed = a.collapsed ~= nil, text = a.text, image = a.image,
		imagesize = a.imagesize, imagealt = a.imagealt, caption = a.caption, body = a[ 1 ],
	} )
end

function p.gap()
	return '<li class="wt-timeline__item wt-timeline__item--gap" aria-hidden="true"></li>'
end

function p.rail( frame )
	local a = getArgs( frame )
	return styles( frame ) .. renderRail( a[ 1 ], a.title )
end

function p.parallel( frame )
	local a = getArgs( frame )
	return styles( frame ) .. '<div class="wt-timelines' .. ( a.grouped and ' wt-timelines--grouped' or '' )
		.. '">' .. ( a[ 1 ] or '' ) .. '</div>'
end

-- ------------------------------------------------------------------ outline
-- One text in, one timeline out:
--
--   == Section ==                        a section (== is the top level; === inside it, and so on)
--   Text on the next lines                 the section's introduction, shown beside its dot
--   * '''3.3 mya''' Oldest stone tools.    an item: bold date, then the text
--   * 1612 ;; The Go academy ;; Text       an item with a title: date ;; title ;; text
--   ** a sub-point                         from ** down, lines are ordinary wikitext lists in the item (one * less)
--   [[File:X.jpg|thumb|Caption]]           the picture of the next item (several lines: several pictures, in a row that wraps)
--   a continuation line                    goes on the text of the item above

local OPT = {
	thumb = 1, thumbnail = 1, frame = 1, frameless = 1, border = 1, right = 1, left = 1, center = 1,
	centre = 1, none = 1, baseline = 1, middle = 1, sub = 1, super = 1, ['text-top'] = 1,
	['text-bottom'] = 1, top = 1, bottom = 1,
}

-- Split on | outside [[ ]] and {{ }}.
local function splitPipes( s )
	local parts, depth, cur, i = {}, 0, {}, 1
	while i <= #s do
		local two = s:sub( i, i + 1 )
		if two == '[[' or two == '{{' then
			depth = depth + 1; cur[ #cur + 1 ] = two; i = i + 2
		elseif two == ']]' or two == '}}' then
			depth = depth - 1; cur[ #cur + 1 ] = two; i = i + 2
		elseif s:sub( i, i ) == '|' and depth == 0 then
			parts[ #parts + 1 ] = table.concat( cur ); cur = {}; i = i + 1
		else
			cur[ #cur + 1 ] = s:sub( i, i ); i = i + 1
		end
	end
	parts[ #parts + 1 ] = table.concat( cur )
	return parts
end

local function parseFile( line )
	local parts = splitPipes( line:sub( 3, -3 ) )
	local name = trim( ( parts[ 1 ]:gsub( '^%s*[Ff][Ii][Ll][Ee]:', '' ):gsub( '^%s*[Ii][Mm][Aa][Gg][Ee]:', '' ) ) )
	local caption, size
	for i = 2, #parts do
		local o = trim( parts[ i ] )
		if o then
			if o:match( '^%d*x?%d+px$' ) or o:match( '^upright' ) then size = size or o:match( '^%d*x?%d+px$' )
			elseif OPT[ o:lower() ] or o:match( '^alt=' ) or o:match( '^link=' ) or o:match( '^class=' )
				or o:match( '^lang=' ) or o:match( '^page=' ) then -- an option, not a caption
			else caption = o end
		end
	end
	return name, caption, size
end

local function parseItem( body )
	-- bold date first: '''date''' text (the form the plain bullet lists of articles use)
	local d, rest = body:match( "^'''(.-)'''%s*(.*)$" )
	if d then
		d = d:gsub( ':%s*$', '' )
		rest = rest:gsub( '^:%s*', '' )
		return trim( d ), nil, trim( rest )
	end
	local date, title, text = body:match( '^(.-)%s*;;%s*(.-)%s*;;%s*(.*)$' )
	if date then return trim( date ), trim( title ), trim( text ) end
	date, title = body:match( '^(.-)%s*;;%s*(.*)$' )
	if date then return trim( date ), trim( title ), nil end
	return trim( body ), nil, nil
end

-- Returns a tree: { children = { node, ... } }; node is a section ({ section = true, title, level,
-- intro = {...}, children }) or an item ({ date, title, text, subs, image, caption }).
function p.parseOutline( text )
	local root = { children = {}, level = 0 }
	local stack = { root }
	local cur, lastItem, pendingFile = nil, nil, nil   -- cur: table receiving continuation lines
	-- Two styles. With any line that starts with !* the events are marked !* (and !** for an event of a
	-- nested timeline inside the one above, !*** one deeper), and every * line is ordinary wikitext
	-- inside its event. Without one (the original style) * marks an event and ** a list inside it.
	local bang = ( '\n' .. text ):find( '\n%s*!%*' ) ~= nil
	local evs = {}      -- bang style: the latest event of each depth
	for line in ( text .. '\n' ):gmatch( '(.-)\r?\n' ) do
		local l = trim( line )
		if not l then
			-- a blank line (or a template that expands over several lines) does not end the text above
		elseif l:match( '^=+.-=+$' ) and not l:match( '^=+$' ) then
			local eq, title = l:match( '^(=+)%s*(.-)%s*=+$' )
			local level = #eq
			while #stack > 1 and stack[ #stack ].level >= level do stack[ #stack ] = nil end
			local node = { section = true, title = title, level = level, intro = {}, children = {} }
			local parent = stack[ #stack ]
			parent.children[ #parent.children + 1 ] = node
			stack[ #stack + 1 ] = node
			cur, lastItem, evs = node.intro, nil, {}
		elseif bang and l:match( '^!%*' ) then
			local stars, rest = l:match( '^!(%*+)%s*(.*)$' )
			local depth = #stars
			local date, title, body = parseItem( rest ~= '' and rest or '' )
			lastItem = { date = date, title = title, text = { body }, subs = {} }
			if pendingFile then
				lastItem.image, lastItem.caption, lastItem.imagesize = pendingFile[ 1 ][ 1 ], pendingFile[ 1 ][ 2 ], pendingFile[ 1 ][ 3 ]
				lastItem.images = pendingFile
				pendingFile = nil
			end
			local parent = depth > 1 and evs[ depth - 1 ] or stack[ #stack ]
			if depth > 1 and not evs[ depth - 1 ] then parent = stack[ #stack ] end
			parent.children = parent.children or {}
			parent.children[ #parent.children + 1 ] = lastItem
			for d = depth, #evs do evs[ d ] = nil end
			evs[ depth ] = lastItem
			cur = lastItem.text
		elseif bang and l:match( '^[%*#:;]' ) then
			-- ordinary wikitext (lists) inside the event above, exactly as written
			if lastItem then
				lastItem.subs[ #lastItem.subs + 1 ] = l
				cur = lastItem.subs; cur.sub = true
			end
		elseif not bang and l:match( '^%*%*' ) then
			-- the lines below an event that start with ** or more are ordinary wikitext lists inside it:
			-- one * less (** is a * list, *** a ** list), so they are written as on any Wikipedia page
			if lastItem then
				lastItem.subs[ #lastItem.subs + 1 ] = trim( l:sub( 2 ) )
				cur = lastItem.subs; cur.sub = true
			end
		elseif not bang and l:match( '^%*' ) then
			local date, title, body = parseItem( trim( ( l:gsub( '^%*%s*', '' ) ) ) or '' )
			lastItem = { date = date, title = title, text = { body }, subs = {} }
			if pendingFile then
				lastItem.image, lastItem.caption, lastItem.imagesize = pendingFile[ 1 ][ 1 ], pendingFile[ 1 ][ 2 ], pendingFile[ 1 ][ 3 ]
				lastItem.images = pendingFile
				pendingFile = nil
			end
			local parent = stack[ #stack ]
			parent.children[ #parent.children + 1 ] = lastItem
			cur = lastItem.text
		elseif l:match( '^%[%[.*%]%]$' ) and ( l:lower():match( '^%[%[file:' ) or l:lower():match( '^%[%[image:' ) ) then
			local name, caption, size = parseFile( l )
			pendingFile = pendingFile or {}      -- a list: every picture line before an item belongs to it
			pendingFile[ #pendingFile + 1 ] = { name, caption, size }
		elseif cur then
			if cur.sub then
				cur[ #cur ] = cur[ #cur ] .. ' ' .. l
			else
				cur[ #cur + 1 ] = l
			end
		end
	end
	local function finish( node )
		for _, ch in ipairs( node.children ) do
			if ch.section then finish( ch )
			else
				if #ch.subs > 0 then ch.subtext = '\n' .. table.concat( ch.subs, '\n' ) .. '\n' end
				if ch.children then finish( ch ) end
			end
		end
	end
	finish( root )
	return root
end

local used = {}      -- anchors already given to a section (within this module instance)
local uid = 0        -- counts outlines; NOTE: Scribunto may load the module afresh for every #invoke,
                     -- so this alone does not keep ids unique on a page: give each outline an |id=

local function buildOutline( node, opts, prefix, counter, depth )
	depth = depth or 0
	local out = {}
	for _, ch in ipairs( node.children ) do
		if ch.section then
			counter.s = counter.s + 1
			local base = anchor( ch.title )
			local rowId, k = base, 1
			while used[ rowId ] do k = k + 1; rowId = base .. '_' .. k end
			if not opts.tocLevel then used[ rowId ] = true end   -- a heading's anchor is MediaWiki's
			out[ #out + 1 ] = renderSection( {
				title = ch.title, id = rowId, toggleId = prefix .. '_s' .. counter.s, collapsed = opts.collapseSections,
				level = opts.tocLevel and math.min( opts.tocLevel + depth, 6 ) or nil,
				text = trim( table.concat( ch.intro, ' ' ) ),
				body = buildOutline( ch, opts, prefix, counter, depth + 1 ),
			} )
		else
			counter.i = counter.i + 1
			local text = trim( table.concat( ch.text, ' ' ) )
			if #ch.subs > 0 then
				text = ( text and ( text .. ' ' ) or '' ) .. ch.subtext
			end
			local images
			if ch.images then
				images = {}
				for _, f in ipairs( ch.images ) do images[ #images + 1 ] = { f[ 1 ], f[ 2 ], f[ 3 ] or '220px' } end
			end
			out[ #out + 1 ] = renderItem( {
				date = ch.date, title = ch.title, text = text, image = ch.image, caption = ch.caption, images = images,
				imagesize = ch.image and ( ch.imagesize or '220px' ) or nil,
				id = prefix .. '_i' .. counter.i, collapsed = opts.collapseItems,
				sub = ch.children and buildOutline( ch, opts, prefix, counter, depth ) or nil,
			} )
		end
	end
	return table.concat( out )
end

function p.outline( frame )
	local a = getArgs( frame )
	local text = a.text or a[ 1 ] or ''
	local tree = p.parseOutline( text )
	uid = uid + 1
	local collapsed = a.collapsed
	local opts = {
		collapseSections = collapsed == 'sections' or collapsed == 'all',
		collapseItems = collapsed == 'items' or collapsed == 'all',
		-- |toc=no: the section titles are plain text; otherwise they are headings (level |toclevel=, 3 by
		-- default: a timeline usually sits under a == Timeline == heading) and show in the table of contents
		tocLevel = not ( { no = 1, off = 1, ['false'] = 1, ['0'] = 1 } )[ ( a.toc or '' ):lower() ]
			and math.max( 2, math.min( tonumber( a.toclevel ) or 3, 6 ) ) or nil,
	}
	-- Without |id=, the prefix comes from the text itself: two different outlines on a page never
	-- share it (Scribunto does not keep a counter between #invoke calls).
	local h = 5381
	for i = 1, #text do h = ( h * 33 + text:byte( i ) ) % 4294967296 end
	local body = buildOutline( tree, opts, a.id or string.format( 'tl%x', h ), { s = 0, i = 0 } )
	return styles( frame ) .. renderRail( body, a.title, a.open ~= nil and a.open:lower() ~= 'no' )
end

-- exposed for the tests
p._render = { event = renderEvent, item = renderItem, section = renderSection, rail = renderRail }

return p
