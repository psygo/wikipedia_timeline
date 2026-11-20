-- Just enough of Scribunto's `mw` library to run Module:TimelineRail outside MediaWiki.
mw = {
	text = {
		encode = function( s )
			return ( s:gsub( '[&<>"\']', { ['&'] = '&amp;', ['<'] = '&lt;', ['>'] = '&gt;', ['"'] = '&quot;', ["'"] = '&#039;' } ) )
		end,
	},
	uri = {
		anchorEncode = function( s )
			s = s:gsub( '%s+', '_' )
			return ( s:gsub( '[^%w_%-%.:]', function( c ) return string.format( '.%02X', c:byte() ) end ) )
		end,
	},
}

-- A frame as #invoke gives it: args of the invoke, and (when called from a template) the parent's args.
function mw.frame( args, parentArgs )
	local f = { args = args or {} }
	function f:extensionTag( name, _, a ) return '<' .. name .. ' src="' .. a.src .. '" />' end
	function f:getParent() return parentArgs and { args = parentArgs } or nil end
	-- a child frame, as frame:newChild gives it: its parent is the frame it was made on
	function f:newChild( t ) return mw.frame( t.args, self.args ) end
	return f
end

-- mw.html.create: just the builder calls Module:ViewSwitcher uses
local Html = {}
Html.__index = Html
local function node( tag ) return setmetatable( { name = tag, attrs = {}, classes = {}, kids = {} }, Html ) end
function Html:addClass( c ) self.classes[ #self.classes + 1 ] = c; return self end
function Html:attr( k, v ) self.attrs[ #self.attrs + 1 ] = { k, v }; return self end
function Html:tag( t ) local n = node( t ); n.parent = self; self.kids[ #self.kids + 1 ] = n; return n end
function Html:wikitext( s ) self.kids[ #self.kids + 1 ] = s; return self end
local function render( n )
	local a = ''
	if #n.classes > 0 then a = ' class="' .. table.concat( n.classes, ' ' ) .. '"' end
	for _, kv in ipairs( n.attrs ) do a = a .. ' ' .. kv[ 1 ] .. '="' .. kv[ 2 ] .. '"' end
	local out = {}
	for _, k in ipairs( n.kids ) do out[ #out + 1 ] = type( k ) == 'string' and k or render( k ) end
	return '<' .. n.name .. a .. '>' .. table.concat( out ) .. '</' .. n.name .. '>'
end
function Html:__tostring()
	local root = self
	while root.parent do root = root.parent end
	return render( root )
end
mw.html = { create = node }
