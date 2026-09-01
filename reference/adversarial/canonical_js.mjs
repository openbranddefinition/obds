import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';

// OBDS 14.3c. NFC is only deterministic once the Unicode version performing it
// is fixed, so a governed string may contain only code points assigned in the
// pinned version, plus the permanent noncharacters. Node ships a newer Unicode
// database than the pin, which is exactly why this file reads the pinned
// assignment set from the release rather than trusting its own runtime.
const PIN_PATH = path.join(
  path.dirname(url.fileURLToPath(import.meta.url)),
  '..', 'foundation', 'src', 'obds_ref', 'unicode-pin-15.1.0.json',
);
const PIN = JSON.parse(fs.readFileSync(PIN_PATH, 'utf8'));
const PIN_STARTS = PIN.assignedRanges.map(r => r[0]);
const PIN_ENDS = PIN.assignedRanges.map(r => r[1]);

// Section 14.3c. Admitting only code points assigned in the pinned version makes
// NFC identical on every database at or after it, and says nothing about an
// older one, which does not know those code points and gives them combining
// class zero. A runtime that cannot satisfy the contract says so.
const hostUnicode = process.versions.unicode;
if (hostUnicode) {
  const parse = v => v.split('.').map(Number);
  const [hostMajor, hostMinor = 0] = parse(hostUnicode);
  const [pinMajor, pinMinor = 0] = parse(PIN.unicodeVersion);
  if (hostMajor < pinMajor || (hostMajor === pinMajor && hostMinor < pinMinor)) {
    throw new Error(
      `this runtime carries Unicode ${hostUnicode}; OBDS section 14.3c pins `
      + `Unicode ${PIN.unicodeVersion} and requires a database at or after it. `
      + 'Node.js 21 or later satisfies this.',
    );
  }
}

function assignedInPin(cp) {
  // Both ends of every range are inclusive.
  let low = 0, high = PIN_STARTS.length;
  while (low < high) {
    const mid = (low + high) >> 1;
    if (PIN_STARTS[mid] <= cp) low = mid + 1; else high = mid;
  }
  const index = low - 1;
  return index >= 0 && cp <= PIN_ENDS[index];
}

function assertPinnedCodePoints(s) {
  for (const character of s) {
    const cp = character.codePointAt(0);
    if (cp < 0x80) continue;
    if (!assignedInPin(cp)) {
      throw new Error(
        `code point U+${cp.toString(16).toUpperCase().padStart(4, '0')} is not `
        + `assigned in Unicode ${PIN.unicodeVersion}, the version pinned by section 14.3c`,
      );
    }
  }
}

function normaliseString(s) {
  // OBDS 14.3 step 0, then step 2, then step 1: reject code points outside the
  // pinned Unicode version, line endings to LF, then Unicode NFC.
  // Applies to string values and object keys alike.
  assertPinnedCodePoints(s);
  return s.replace(/\r\n/g,'\n').replace(/\r/g,'\n').normalize('NFC');
}
function num(v) {
  if (!Number.isFinite(v)) throw new Error('non-finite');
  if (Object.is(v, -0) || v === 0) return '0';
  return String(v);
}
function canon(v) {
  if (v === null) return 'null';
  if (v === true) return 'true';
  if (v === false) return 'false';
  if (typeof v === 'number') return num(v);
  if (typeof v === 'string') return JSON.stringify(normaliseString(v));
  if (Array.isArray(v)) return '[' + v.map(canon).join(',') + ']';
  if (typeof v === 'object') {
    const mapped = new Map();
    for (const [k,val] of Object.entries(v)) {
      // OBDS 14.3 steps 1 and 2 apply to every string AND object key:
      // CRLF -> LF, CR -> LF, then NFC. Keys and values use one function so
      // they cannot drift apart.
      const nk=normaliseString(k);
      if (mapped.has(nk)) throw new Error('duplicate key after canonical normalisation');
      mapped.set(nk,val);
    }
    // ECMAScript Array.sort compares UTF-16 code units, matching the OBDS 1.0 contract.
    const keys=[...mapped.keys()].sort();
    return '{' + keys.map(k => JSON.stringify(k)+':'+canon(mapped.get(k))).join(',') + '}';
  }
  throw new Error('unsupported');
}
// The vector file gained expected output in 1.1.3, so it is an object with a
// `vectors` array rather than a bare array of inputs. A plain array is still
// accepted, which is what ad-hoc test files pass.
const loaded = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const raws = Array.isArray(loaded)
  ? loaded
  : loaded.vectors.map(v => v.input);
// Canonical output may contain U+2028 and U+2029, which section 14.3b emits
// directly and which Python's splitlines() treats as line breaks. Printing the
// text would silently misalign a batch comparison, so each result is emitted as
// one line of lowercase hex. --text restores the old behaviour for one vector.
const asText = process.argv.includes('--text');
for (const raw of raws) {
  const parsed=JSON.parse(raw);
  const canonical = canon(parsed);
  if (asText) { console.log(canonical); continue; }
  console.log(Buffer.from(canonical, 'utf8').toString('hex'));
}
