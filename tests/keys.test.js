'use strict';
/* keys/ holds the project's public signing keys only, never a private key:
   the apk key (25.12) and the usign key (24.10). */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DIR = path.join(__dirname, '..', 'keys');

test('keys/: only the public signing keys, and the apk key is a P-256 public key', () => {
	assert.deepStrictEqual(fs.readdirSync(DIR).sort(), [ 'qwrt-24.10.usign.pub', 'qwrt-signing.pem', 'vantage-24.10.usign.pub', 'vantage-signing.pem' ]);
	for (const file of [ 'vantage-signing.pem', 'qwrt-signing.pem' ]) {
		const pem = fs.readFileSync(path.join(DIR, file), 'utf8');
		assert.doesNotMatch(pem, /PRIVATE KEY/);
		const key = crypto.createPublicKey(pem);
		assert.strictEqual(key.asymmetricKeyType, 'ec');
		assert.strictEqual(key.asymmetricKeyDetails.namedCurve, 'prime256v1');
	}
});

test('keys/: the fingerprint in the docs matches the key file', () => {
	const sum = crypto.createHash('sha256').update(fs.readFileSync(path.join(DIR, 'vantage-signing.pem'))).digest('hex');
	for (const doc of [ 'README.md', 'docs/INSTALL.md', 'dev/build/repo-index.html' ])
		assert.match(fs.readFileSync(path.join(__dirname, '..', doc), 'utf8'), new RegExp(sum), doc);
});

/* a usign public key: a comment line, then base64 of 'Ed', the 8-byte key
   number (its fingerprint) and the 32-byte Ed25519 key; a secret key is
   longer */
const usignFingerprint = (file = 'vantage-24.10.usign.pub') => {
	const lines = fs.readFileSync(path.join(DIR, file), 'utf8').trim().split('\n');
	assert.strictEqual(lines.length, 2);
	assert.match(lines[0], /^untrusted comment: /);
	const raw = Buffer.from(lines[1], 'base64');
	assert.strictEqual(raw.length, 42, 'a public key, not a secret key');
	assert.strictEqual(raw.subarray(0, 2).toString(), 'Ed');
	return raw.subarray(2, 10).toString('hex');
};

test('keys/: the 24.10 key is a usign public key, and the docs give its fingerprint', () => {
	const fp = usignFingerprint();
	for (const doc of [ 'docs/INSTALL.md', 'dev/build/repo-index.html' ])
		assert.match(fs.readFileSync(path.join(__dirname, '..', doc), 'utf8'), new RegExp(fp), doc);
});

test('keys/: QWRT feeds document their own public keys, distinct from upstream', () => {
	const sum = crypto.createHash('sha256').update(fs.readFileSync(path.join(DIR, 'qwrt-signing.pem'))).digest('hex');
	const fp = usignFingerprint('qwrt-24.10.usign.pub');
	assert.notStrictEqual(fp, usignFingerprint());
	assert.notDeepStrictEqual(fs.readFileSync(path.join(DIR, 'qwrt-signing.pem')), fs.readFileSync(path.join(DIR, 'vantage-signing.pem')));
	for (const doc of [ 'docs/QWRT.md', 'dev/build/qwrt-repo-index.html' ]) {
		const text = fs.readFileSync(path.join(__dirname, '..', doc), 'utf8');
		assert.match(text, new RegExp(sum), doc);
		assert.match(text, new RegExp(fp), doc);
	}
});
