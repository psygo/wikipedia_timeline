-- Module:OutlineList
-- The outline syntax of Module:TimelineRail drawn as a plain bulleted list: the list the article has
-- today. A view for Module:ViewSwitcher, but it works on its own:
--   {{#invoke:OutlineList|list |text= == Section == ... * '''1612''' text }}
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

local function listHtml( node )
	local out, run = {}, {}
	local function flush()
		if #run > 0 then out[ #out + 1 ] = '<ul>' .. table.concat( run ) .. '</ul>'; run = {} end
	end
	for _, ch in ipairs( node.children ) do
		if ch.section then
			flush()
			out[ #out + 1 ] = '<p><b>' .. ch.title .. '</b></p>'
			local intro = trim( table.concat( ch.intro, ' ' ) )
			if intro then out[ #out + 1 ] = '<p>' .. intro .. '</p>' end
			out[ #out + 1 ] = listHtml( ch )
		else
			local head = {}
			if ch.date then head[ #head + 1 ] = "'''" .. ch.date .. "'''" end
			if ch.title then head[ #head + 1 ] = "'''" .. ch.title .. "'''" end
			local text = itemText( ch )
			local line = table.concat( head, ' – ' )
			if text then line = line .. ( ch.title and '. ' or ( ch.date and ' – ' or '' ) ) .. text end
			run[ #run + 1 ] = '<li>' .. line .. ( ch.image and ( '<br />' .. plainImage( ch ) ) or '' )
				.. ( ch.children and listHtml( ch ) or '' ) .. '</li>'
		end
	end
	flush()
	return table.concat( out )
end

function p.list( frame )
	local a = getArgs( frame )
	return listHtml( parse( a.text or a[ 1 ] or '', a.parser ) )
end

return p
