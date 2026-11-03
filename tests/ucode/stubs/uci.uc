// Test double for ucode's uci module (tests/plugin.test.js): config
// vantage held in global STUB = { sections: [ ... ], seq, committed,
// fail_commit, reverted }, and read-only configs wireless and network in
// STUB.wireless and STUB.network (absent when null; network 'no load',
// the harness's default when a case gives none: the run stops if it is
// loaded at all). Fails closed: a cursor made with
// arguments, a read of any other config, or a change to any config but
// vantage stops the run, so a plugin that tries one fails its tests.
'use strict';

function only(conf, allowed, what) {
	if (!(conf in allowed))
		die(sprintf('uci stub: %s of config %J', what, conf));
}

function find(sid) {
	for (let s in global.STUB.sections)
		if (s['.name'] == sid)
			return s;

	return null;
}

function sections(conf, state) {
	if (conf == 'wireless' && state)
		return global.STUB.wireless_state ?? global.STUB.wireless ?? [];
	return (conf == 'vantage') ? global.STUB.sections : (global.STUB[conf] ?? []);
}

function cursor(...args) {
	let state = length(args) == 2 && args[0] == null && args[1] == '/var/state';
	if (length(args) && !state)
		die(sprintf('uci stub: cursor%J', args));

	return {
		load: function(conf) {
			only(conf, state ? [ 'wireless' ] : [ 'vantage', 'wireless', 'network' ], 'load');

			if (conf == 'network' && global.STUB.network == 'no load')
				die('uci stub: config network loaded where it may not be');

			return conf == 'vantage' || global.STUB[conf] != null;
		},

		foreach: function(conf, stype, fn) {
			only(conf, state ? [ 'wireless' ] : [ 'vantage', 'wireless', 'network' ], 'foreach');

			for (let s in [ ...sections(conf, state) ])
				if (!stype || s['.type'] == stype)
					if (fn({ ...s }) === false)
						break;

			return true;
		},

		add: function(conf, stype) {
			only(conf, state ? [] : [ 'vantage' ], 'add');

			let sid = sprintf('cfg%06x', ++global.STUB.seq);
			push(global.STUB.sections, { '.name': sid, '.type': stype, '.anonymous': true });
			return sid;
		},

		set: function(conf, sid, opt, val) {
			only(conf, state ? [] : [ 'vantage' ], 'set');

			let s = find(sid);

			if (!s)
				return null;

			s[opt] = val;
			return true;
		},

		delete: function(conf, sid, opt) {
			only(conf, state ? [] : [ 'vantage' ], 'delete');

			if (opt != null) {
				let s = find(sid);

				if (s)
					delete s[opt];

				return !!s;
			}

			let before = length(global.STUB.sections);
			global.STUB.sections = filter(global.STUB.sections, (s) => s['.name'] != sid);
			return length(global.STUB.sections) < before;
		},

		commit: function(conf) {
			only(conf, state ? [] : [ 'vantage' ], 'commit');

			if (global.STUB.fail_commit)
				return null;

			global.STUB.committed = true;
			return true;
		},

		revert: function(conf) {
			only(conf, state ? [] : [ 'vantage' ], 'revert');

			global.STUB.reverted = true;
			return true;
		}
	};
}

export { cursor };
