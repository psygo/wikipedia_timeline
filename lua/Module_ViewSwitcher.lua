-- Module:ViewSwitcher
-- Several views of the same content with a "View" dropdown at the top right (the dropdown itself is
-- made by a small script, see ViewSwitcher.js; without it the reader gets the first view).
--
-- It knows nothing about timelines: a view is any wikitext, or the output of any module function.
--
--   Views you write (or build with templates) yourself:
--     {{#invoke:ViewSwitcher|switch |label1=Timeline |view1=... |label2=List |view2=... |default=1}}
--
--   Views drawn from one set of data, by module functions that all get the same arguments:
--     {{#invoke:ViewSwitcher|switch
--       |views=*Timeline=TimelineRail.outline; List=@original; Table=OutlineTable.table
--       |id=inv1 |text= ... |original= ... }}
--     "Label=Module.function" (the module name is without "Module:", may contain /sandbox);
--     "Label=@name" shows the text of the argument |name= as it is (the article's original list or
--     table, say). Every other argument goes to every function.
--
--   The default view (the one shown first, and the only one without the script): a * before its label,
--     or |default=Table (a label) or |default=2 (a position). Without any of them, the first.
--
--   Footnotes: the <ref>s of the text would be listed once per view, so only the default view keeps
--     them. |refs=all keeps them in every view.
--
-- Output: <div class="viewswitcher"><div class="viewswitcher__view" data-vs-label="Timeline">...</div>...</div>

local p = {}

local STYLES = 'Module:ViewSwitcher/styles.css'

local function trim( s )
	if s == nil then return nil end
	s = tostring( s ):match( '^%s*(.-)%s*$' )
	if s == '' then return nil end
	return s
end

local function getArgs( frame )
	local args = {}
	for k, v in pairs( frame.args ) do args[ k ] = v end
	local parent = frame:getParent()
	if parent then
		for k, v in pairs( parent.args ) do
			if trim( v ) ~= nil then args[ k ] = v end
		end
	end
	return args
end

-- "Label=Module.function; *Label2=@arg; ..." -> { { label, default, module, func | arg }, ... }
-- A leading * on the label marks the default view; "@arg" takes the text of the argument |arg=.
local function parseViews( spec )
	local views = {}
	for part in ( spec .. ';' ):gmatch( '([^;]*);' ) do
		local label, target = part:match( '^%s*(.-)%s*=%s*(.-)%s*$' )
		if label and label ~= '' and target ~= '' then
			local star = label:match( '^%*%s*(.*)$' )
			local v = { label = star or label, default = star ~= nil }
			local arg = target:match( '^@%s*(.+)$' )
			if arg then
				v.arg = arg
			else
				local mod, func = target:match( '^(.*)%.([^%.]+)$' )
				if mod then v.module, v.func = mod, func end
			end
			if v.arg or v.module then views[ #views + 1 ] = v end
		end
	end
	return views
end

local function render( frame, args, v )
	local mod = require( 'Module:' .. v.module )
	local fn = mod[ v.func ]
	if type( fn ) ~= 'function' then
		error( 'ViewSwitcher: Module:' .. v.module .. ' has no function "' .. v.func .. '"', 0 )
	end
	-- Each function sees the arguments as if it had been invoked on its own.
	local child = frame:newChild( { title = 'Module:' .. v.module, args = args } )
	return fn( child )
end

-- A footnote written in the text of several views would be listed once per view. The reference
-- markers (what <ref> is turned into before a module sees it) are taken out of every view but the
-- default one; |refs=all keeps them everywhere.
local function withoutRefs( html )
	return ( html:gsub( '\127\'"`UNIQ%-%-ref%-%x+%-QINU`"\'\127', '' ) )
end

function p.switch( frame )
	local args = getArgs( frame )
	local views = {}
	if trim( args.views ) then
		local specs = parseViews( args.views )
		local reserved = { views = true, default = true, class = true, refs = true }
		for _, v in ipairs( specs ) do if v.arg then reserved[ v.arg ] = true end end
		local passed = {}
		for k, v in pairs( args ) do
			if not reserved[ k ] then passed[ k ] = v end
		end
		for _, v in ipairs( specs ) do
			views[ #views + 1 ] = { label = v.label, default = v.default,
				html = v.arg and ( args[ v.arg ] or '' ) or render( frame, passed, v ) }
		end
	else
		local i = 1
		while trim( args[ 'view' .. i ] ) or trim( args[ 'label' .. i ] ) do
			local label = trim( args[ 'label' .. i ] ) or ( 'View ' .. i )
			local star = label:match( '^%*%s*(.*)$' )
			views[ #views + 1 ] = { label = star or label, default = star ~= nil, html = args[ 'view' .. i ] or '' }
			i = i + 1
		end
	end
	if #views == 0 then
		return '<span class="error">ViewSwitcher: give |views= or |label1= and |view1=</span>'
	end

	-- the default view: a * on a label, else |default= (a number or a label), else the first
	local default
	for i, v in ipairs( views ) do
		if v.default and not default then default = i end
	end
	local want = trim( args.default )
	if not default and want then
		default = tonumber( want )
		if not default then
			for i, v in ipairs( views ) do
				if v.label:lower() == want:lower() then default = i; break end
			end
		end
	end
	if not default or default < 1 or default > #views then default = 1 end

	local root = mw.html.create( 'div' ):addClass( 'viewswitcher' )
	if trim( args.class ) then root:addClass( args.class ) end
	for i, v in ipairs( views ) do
		local d = root:tag( 'div' ):addClass( 'viewswitcher__view' ):attr( 'data-vs-label', v.label )
		if i == default then d:addClass( 'viewswitcher__view--default' ) end
		local html = v.html
		if i ~= default and trim( args.refs ) ~= 'all' then html = withoutRefs( html ) end
		-- newlines: a list or table written in a view must start a line
		d:wikitext( '\n' .. html .. '\n' )
	end
	return frame:extensionTag( 'templatestyles', '', { src = STYLES } ) .. tostring( root )
end

return p
