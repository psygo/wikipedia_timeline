/**
 * Timeline toolbar (user script).
 *
 * Adds a "Timeline" drop-down to the WikiEditor toolbar (the classic 2010
 * editor) that inserts ready-made wikitext for the timeline templates:
 * a simple timeline, a dot with several events, parallel timelines, and
 * parallel timelines with aligned dots.
 *
 * Install: copy this file to User:<YourName>/Timeline-toolbar.js on the wiki,
 * then add this line to User:<YourName>/common.js:
 *
 *     importScript( 'User:<YourName>/Timeline-toolbar.js' );
 *
 * The template names below are the real ones (Template:TimelineRail and its
 * subpages); the skeletons it inserts use them.
 */
( function () {
	'use strict';

	var NAMES = {
		timeline: 'TimelineRail',
		item: 'TimelineRail/item',
		event: 'TimelineRail/event',
		parallel: 'TimelineRail/parallel',
		gap: 'TimelineRail/gap',
		section: 'TimelineRail/section'
	};

	function t( key, args ) {
		return '{{' + NAMES[ key ] + ( args ? ' ' + args : '' ) + '}}';
	}

	// Wikitext skeletons. No blank lines between items: they would become
	// stray paragraphs inside the list.
	var SNIPPETS = {
		simple:
			'{{' + NAMES.timeline + '\n' +
			'|{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			'{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			'}}\n',

		multi:
			'{{' + NAMES.timeline + '\n' +
			'|{{' + NAMES.item + ' |date=Year |events=\n' +
			'{{' + NAMES.event + ' |title=First event |text=Text.}}\n' +
			'{{' + NAMES.event + ' |title=Second event |text=Text.}}\n' +
			'}}\n' +
			'}}\n',

		section:
			'{{' + NAMES.timeline + '\n' +
			'|{{' + NAMES.section + ' |title=Section\n' +
			'|{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			'{{' + NAMES.section + ' |title=Nested section\n' +
			'|{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			'}}\n' +
			'}}\n' +
			'}}\n',

		parallel:
			'{{' + NAMES.parallel + '\n' +
			'|{{' + NAMES.timeline + ' |title=First\n' +
			'|{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			'}}\n' +
			'{{' + NAMES.timeline + ' |title=Second\n' +
			'|{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			'}}\n' +
			'}}\n',

		grouped:
			'{{' + NAMES.parallel + ' |grouped=yes\n' +
			'|{{' + NAMES.timeline + ' |title=First\n' +
			'|{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			t( 'gap' ) + '\n' +
			'{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			'}}\n' +
			'{{' + NAMES.timeline + ' |title=Second\n' +
			t( 'gap' ) + '\n' +
			'{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			'{{' + NAMES.item + ' |date=Year |title=Title |text=Text.}}\n' +
			'}}\n' +
			'}}\n'
	};

	function entry( label, snippet ) {
		return {
			label: label,
			action: { type: 'encapsulate', options: { pre: snippet, peri: '', post: '' } }
		};
	}

	function addToolbar( $textarea ) {
		$textarea.wikiEditor( 'addToToolbar', {
			section: 'main',
			group: 'insert',
			tools: {
				timeline: {
					label: 'Timeline',
					type: 'select',
					list: {
						'timeline-simple': entry( 'Simple timeline', SNIPPETS.simple ),
						'timeline-multi': entry( 'Several events on one dot', SNIPPETS.multi ),
						'timeline-section': entry( 'Sections (nestable)', SNIPPETS.section ),
						'timeline-parallel': entry( 'Parallel timelines', SNIPPETS.parallel ),
						'timeline-grouped': entry( 'Parallel and grouped (aligned dots)', SNIPPETS.grouped )
					}
				}
			}
		} );
	}

	// Only run in the editor.
	if ( mw.config.get( 'wgAction' ) === 'edit' || mw.config.get( 'wgAction' ) === 'submit' ) {
		mw.loader.using( 'ext.wikiEditor' ).then( function () {
			mw.hook( 'wikiEditor.toolbarReady' ).add( addToolbar );
		} );
	}
}() );
