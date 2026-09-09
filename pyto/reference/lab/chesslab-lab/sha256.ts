// Pure-JS, SYNCHRONOUS SHA-256 (FIPS 180-4) over bytes.
//
// Why not Web Crypto: crypto.subtle.digest is Promise-based in every
// environment (browser and Node alike), but runEngine's public contract —
// and threeFactorParity.test.ts, which calls runThreeFactor synchronously
// and is a HARD INVARIANT this wave must not touch — is synchronous.
// R1 also rules out node:crypto's synchronous createHash (Node-only) for
// anything in the browser-safe core. This file is the one piece of exec/**
// that computes its own digest instead of delegating, so compile.ts's
// planFingerprint and sink.ts's artifact hashing can run inside a
// synchronous executeCompiledPlan without breaking either constraint.
//
// Verified byte-for-byte against node:crypto's sha256 across several
// inputs (including one crossing the 64-byte block boundary) before this
// file was wired into compile.ts/sink.ts — see the Wave 1A report.

const K = new Uint32Array([
	0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
	0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
	0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
	0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
	0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
	0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
	0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
	0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]);

function rightRotate(x: number, n: number): number {
	return (x >>> n) | (x << (32 - n));
}

export function sha256Bytes(message: Uint8Array): Uint8Array {
	let h0 = 0x6a09e667;
	let h1 = 0xbb67ae85;
	let h2 = 0x3c6ef372;
	let h3 = 0xa54ff53a;
	let h4 = 0x510e527f;
	let h5 = 0x9b05688c;
	let h6 = 0x1f83d9ab;
	let h7 = 0x5be0cd19;

	const bitLen = message.length * 8;
	const withOne = message.length + 1;
	const mod = withOne % 64;
	const padLen = mod <= 56 ? 56 - mod : 120 - mod;
	const total = withOne + padLen + 8;
	const buf = new Uint8Array(total);
	buf.set(message);
	buf[message.length] = 0x80;
	const view = new DataView(buf.buffer);
	view.setUint32(total - 4, bitLen >>> 0, false);
	view.setUint32(total - 8, Math.floor(bitLen / 4294967296), false);

	const w = new Uint32Array(64);
	for (let offset = 0; offset < total; offset += 64) {
		for (let i = 0; i < 16; i++) w[i] = view.getUint32(offset + i * 4, false);
		for (let i = 16; i < 64; i++) {
			const s0 = rightRotate(w[i - 15], 7) ^ rightRotate(w[i - 15], 18) ^ (w[i - 15] >>> 3);
			const s1 = rightRotate(w[i - 2], 17) ^ rightRotate(w[i - 2], 19) ^ (w[i - 2] >>> 10);
			w[i] = (w[i - 16] + s0 + w[i - 7] + s1) | 0;
		}
		let a = h0, b = h1, c = h2, d = h3, e = h4, f = h5, g = h6, h = h7;
		for (let i = 0; i < 64; i++) {
			const S1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
			const ch = (e & f) ^ (~e & g);
			const temp1 = (h + S1 + ch + K[i] + w[i]) | 0;
			const S0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
			const maj = (a & b) ^ (a & c) ^ (b & c);
			const temp2 = (S0 + maj) | 0;
			h = g; g = f; f = e; e = (d + temp1) | 0;
			d = c; c = b; b = a; a = (temp1 + temp2) | 0;
		}
		h0 = (h0 + a) | 0; h1 = (h1 + b) | 0; h2 = (h2 + c) | 0; h3 = (h3 + d) | 0;
		h4 = (h4 + e) | 0; h5 = (h5 + f) | 0; h6 = (h6 + g) | 0; h7 = (h7 + h) | 0;
	}
	const out = new Uint8Array(32);
	const outView = new DataView(out.buffer);
	outView.setUint32(0, h0 >>> 0, false);
	outView.setUint32(4, h1 >>> 0, false);
	outView.setUint32(8, h2 >>> 0, false);
	outView.setUint32(12, h3 >>> 0, false);
	outView.setUint32(16, h4 >>> 0, false);
	outView.setUint32(20, h5 >>> 0, false);
	outView.setUint32(24, h6 >>> 0, false);
	outView.setUint32(28, h7 >>> 0, false);
	return out;
}

function toHex(bytes: Uint8Array): string {
	return Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('');
}

export function sha256HexSync(bytes: Uint8Array): string {
	return toHex(sha256Bytes(bytes));
}

export function sha256HexSyncText(text: string): string {
	return sha256HexSync(new TextEncoder().encode(text));
}
