-- Module:OutlineTable
-- The outline syntax of Module:TimelineRail drawn as a table (class="wikitable"): Date, Title,
-- Description and Image columns, those that have data; sections are full-width rows. A view for
-- Module:ViewSwitcher, but it works on its own:
--   {{#invoke:OutlineTable|table |text= == Section == ... * '''1612''' text }}
-- No styles, no ids.
local p = {}

local function trim( s )
	if s == nil then return nil end
	s = tostring( s ):match( '^%s*(.-)%s*$' )
	if s == '' then return nil end
	return s
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

-- The outline syntax is read by the parser of Module:TimelineRail; this module only draws it differently.
-- (|parser=TimelineRail/sandbox reads it with the sandbox copy, for testing.)
local function parse( text, parser ) return require( 'Module:' .. ( parser or 'TimelineRail' ) ).parseOutline( text ) end

local function itemText( ch )
	local text = trim( table.concat( ch.text, ' ' ) )
	if #ch.subs > 0 then
		-- the sub-points are wikitext lists (made by the parser); an older parser gave HTML ones
		local list = ch.subtext
		if not list then
			local lis = {}
			for _, x in ipairs( ch.subs ) do lis[ #lis + 1 ] = '<li>' .. x .. '</li>' end
			list = '<ul>' .. table.concat( lis ) .. '</ul>'
		end
		text = ( text and ( text .. ' ' ) or '' ) .. list
	end
	return text
end

local function plainImage( ch )
	if not ch.image then return '' end
	local out = {}
	for _, f in ipairs( ch.images or { { ch.image, ch.caption, ch.imagesize } } ) do
		out[ #out + 1 ] = '[[File:' .. f[ 1 ] .. '|thumb|none|' .. ( f[ 3 ] or '220px' ) .. '|' .. ( f[ 2 ] or '' ) .. ']]'
	end
	return table.concat( out, ' ' )
end

function p.table( frame )
	local a = getArgs( frame )
	local rows, has = {}, {}
	local function walk( node, depth )
		for _, ch in ipairs( node.children ) do
			if ch.section then
				rows[ #rows + 1 ] = { section = ch, depth = depth }
				walk( ch, depth + 1 )
			else
				rows[ #rows + 1 ] = { item = ch, text = itemText( ch ) }
				has.date = has.date or ch.date ~= nil
				has.title = has.title or ch.title ~= nil
				has.text = has.text or rows[ #rows ].text ~= nil
				has.image = has.image or ch.image ~= nil
			end
		end
	end
	walk( parse( a.text or a[ 1 ] or '', a.parser ), 0 )
	local cols = {}
	for _, c in ipairs( { { 'date', 'Date' }, { 'title', 'Title' }, { 'text', 'Description' }, { 'image', 'Image' } } ) do
		if has[ c[ 1 ] ] then cols[ #cols + 1 ] = c end
	end
	if #cols == 0 then return '' end
	local out = { '<table class="wikitable"><tr>' }
	for _, c in ipairs( cols ) do out[ #out + 1 ] = '<th scope="col">' .. c[ 2 ] .. '</th>' end
	out[ #out + 1 ] = '</tr>'
	for _, r in ipairs( rows ) do
		if r.section then
			local intro = trim( table.concat( r.section.intro, ' ' ) )
			out[ #out + 1 ] = '<tr><th colspan="' .. #cols .. '" scope="colgroup"'
				.. ( r.depth > 0 and ( ' style="padding-left:' .. ( 0.6 + r.depth * 1.2 ) .. 'em"' ) or '' ) .. '>'
				.. r.section.title .. ( intro and ( '<div style="font-weight:normal">' .. intro .. '</div>' ) or '' ) .. '</th></tr>'
		else
			local ch, cells = r.item, {}
			for _, c in ipairs( cols ) do
				local v = c[ 1 ] == 'date' and ch.date or c[ 1 ] == 'title' and ( ch.title and ( "'''" .. ch.title .. "'''" ) )
					or c[ 1 ] == 'text' and r.text or c[ 1 ] == 'image' and ( ch.image and plainImage( ch ) ) or nil
				cells[ #cells + 1 ] = '<td' .. ( c[ 1 ] == 'date' and ' style="white-space:nowrap"' or '' ) .. '>' .. ( v or '' ) .. '</td>'
			end
			out[ #out + 1 ] = '<tr>' .. table.concat( cells ) .. '</tr>'
		end
	end
	out[ #out + 1 ] = '</table>'
	return table.concat( out )
end

return p
