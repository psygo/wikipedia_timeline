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
	return f
end
