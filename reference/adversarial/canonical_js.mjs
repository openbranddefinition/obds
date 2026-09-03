import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';

// OBDS 14.3c. NFC is only deterministic once the Unicode version performing it
// is fixed, so a governed string may contain only code points assigned in the
// pinned version, plus the permanent noncharacters. Node ships a newer Unicode
// database than the pin, which is exactly why this file reads the pinned
// assignment set from the release rather than trusting its own runtime.
// Section 28.1: the one governed interchange contract, in this runtime too.
//
// This file is an independent implementation of section 14.3 canonicalisation,
// and it reads two governed documents to do its job: the Unicode pin table and
// the canonical vector document. `JSON.parse` is last-wins on a duplicate
// object key, so a pin table declaring `assignedRanges` twice, or a vector
// document declaring `vectors` twice, silently became a different document here
// than in the Python reader — which is the Class A defect, in the one place
// where "two implementations agree" is the whole point of the file.
//
// `JSON.parse` cannot detect a duplicate: a reviver only sees keys after the
// collapse. So this is a small recursive-descent reader that refuses one, and
// applies the same section 28.1 bounds as the Python reader.
const MAX_NESTING_DEPTH = 100;

function readGovernedJson(text) {
  let at = 0;

  const error = message => { throw new Error(`governed JSON: ${message} at ${at}`); };
  const white = () => { while (at < text.length && ' \t\n\r'.includes(text[at])) at += 1; };
  const literal = word => {
    if (text.slice(at, at + word.length) !== word) error(`expected ${word}`);
    at += word.length;
  };

  const string = () => {
    if (text[at] !== '"') error('expected a string');
    const start = at;
    at += 1;
    while (at < text.length) {
      if (text[at] === '\\') { at += 2; continue; }
      if (text[at] === '"') { at += 1; return JSON.parse(text.slice(start, at)); }
      at += 1;
    }
    error('unterminated string');
    return undefined;
  };

  const number = () => {
    const start = at;
    if (text[at] === '-') at += 1;
    while (at < text.length && '0123456789+-.eE'.includes(text[at])) at += 1;
    const token = text.slice(start, at);
    if (!/^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?$/.test(token)) {
      error(`not a JSON number: ${token}`);
    }
    const value = Number(token);
    if (!Number.isFinite(value)) error(`non-finite number: ${token}`);
    // Section 28.1 refuses an integer literal that binary64 cannot carry
    // exactly. "Exactly representable" is not "safe integer": 2^53 is
    // representable and is not safe, and the shipped canonical vectors admit it.
    // The Python reader asks `int(float(value)) == value`; this asks the same
    // question, in the only arithmetic that can answer it here.
    if (!/[.eE]/.test(token) && BigInt(value) !== BigInt(token)) {
      error(`integer is not exactly representable as IEEE-754 binary64: ${token}`);
    }
    return value;
  };

  const value = depth => {
    if (depth > MAX_NESTING_DEPTH) error(`nesting exceeds ${MAX_NESTING_DEPTH} levels`);
    white();
    const character = text[at];
    if (character === '{') {
      at += 1;
      // `Object.create(null)`, not `{}`. Assigning `__proto__` on an ordinary
      // object invokes JavaScript's inherited prototype setter instead of
      // creating an own property, so the key vanished from `Object.entries()`
      // and this runtime canonicalised a document with one fewer member than
      // the Python reader saw. A governed reader may not lose a key because of
      // what that key is called.
      const result = Object.create(null);
      const seen = new Set();
      white();
      if (text[at] === '}') { at += 1; return result; }
      for (;;) {
        white();
        const key = string();
        // Section 28.1: a duplicate key is refused, not resolved, and the
        // comparison is the *canonical* one — section 14.3 steps 1 and 2, so the
        // CRLF/CR fold before NFC. Deduplicating on NFC alone accepted `a\rb`
        // beside `a\nb`, which are one key in canonical form, and the Python
        // reader refuses exactly that pair.
        const normalised = key.replace(/\r\n/g, '\n').replace(/\r/g, '\n').normalize('NFC');
        if (seen.has(normalised)) error(`duplicate object key: ${key}`);
        seen.add(normalised);
        white();
        if (text[at] !== ':') error('expected :');
        at += 1;
        Object.defineProperty(result, key, {
          value: value(depth + 1),
          enumerable: true,
          writable: true,
          configurable: true,
        });
        white();
        if (text[at] === ',') { at += 1; continue; }
        if (text[at] === '}') { at += 1; return result; }
        error('expected , or }');
      }
    }
    if (character === '[') {
      at += 1;
      const result = [];
      white();
      if (text[at] === ']') { at += 1; return result; }
      for (;;) {
        result.push(value(depth + 1));
        white();
        if (text[at] === ',') { at += 1; continue; }
        if (text[at] === ']') { at += 1; return result; }
        error('expected , or ]');
      }
    }
    if (character === '"') return string();
    if (character === 't') { literal('true'); return true; }
    if (character === 'f') { literal('false'); return false; }
    if (character === 'n') { literal('null'); return null; }
    if (character === '-' || (character >= '0' && character <= '9')) return number();
    error(`unexpected character ${JSON.stringify(character ?? '<end>')}`);
    return undefined;
  };

  const result = value(1);
  white();
  if (at !== text.length) error('trailing content');
  return result;
}

// Mirrors the Python split exactly. `readGovernedDocument` parses under section
// 28.1 and bounds the data model; `loadGovernedData` additionally requires an
// object root, which is what a *governed document* is. The vector file uses the
// first, because a bare array of inputs is an accepted ad-hoc shape here and has
// been since before 1.1.3.
// Section 28.1: governed input is UTF-8, and bytes that are not UTF-8 are not a
// governed document. Node's `readFileSync(file, 'utf8')` substitutes U+FFFD for
// malformed sequences, so this runtime silently read a *different* document
// where the Python reader refused the bytes outright. `TextDecoder` in fatal
// mode asks the same question Python's `read_text(encoding="utf-8")` asks.
const UTF8 = new TextDecoder('utf-8', { fatal: true });

const readGovernedFile = file => {
  try {
    return UTF8.decode(fs.readFileSync(file));
  } catch (cause) {
    throw new Error(`governed JSON: input is not valid UTF-8: ${cause.message}`);
  }
};

const readGovernedDocument = file => readGovernedJson(readGovernedFile(file));

const loadGovernedData = file => {
  const document = readGovernedDocument(file);
  if (document === null || typeof document !== 'object' || Array.isArray(document)) {
    throw new Error('governed JSON: root must be an object');
  }
  return document;
};

const PIN_PATH = path.join(
  path.dirname(url.fileURLToPath(import.meta.url)),
  '..', 'foundation', 'src', 'obds_ref', 'unicode-pin-15.1.0.json',
);
const PIN = loadGovernedData(PIN_PATH);
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
// Section 28.1 / A2: `--read <file>` makes this file usable as a governed
// reader under test rather than only as a canonicalisation implementation. It
// reads one governed document under the contract above and prints its canonical
// form as hex, so the Python side can compare value for value and refusal for
// refusal. Without it, "every governed reader agrees" was asserted over Python
// readers only, and an independent review found this one diverging on a numeric
// rule nothing compared.
// `--read-parse` stops at the reader. `--read` continues into canonicalisation,
// and canonicalisation has its own duplicate-key check, so a reader-stage
// difference between the two implementations can be masked by a later stage
// agreeing. Parity has to be measured at the stage the contract lives in, so
// both stages are exposed separately.
if (process.argv.includes('--read-parse')) {
  const target = process.argv[process.argv.indexOf('--read-parse') + 1];
  const document = loadGovernedData(target);
  // Numbers go through the same canonical token the canonicaliser uses, because
  // JSON has one number type and the two host languages do not. Comparing host
  // spellings would report a divergence the contract does not have.
  // ASCII-escaped, matching the Python side: the comparison is about the value
  // the readers produced, not about how each host language prints it.
  const asciiString = text => JSON.stringify(text).replace(
    /[\u0080-\uffff]/g,
    ch => '\\u' + ch.charCodeAt(0).toString(16).padStart(4, '0'),
  );
  const stable = value => {
    if (value === null) return 'null';
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    if (typeof value === 'number') return num(value);
    if (typeof value === 'string') return asciiString(value);
    if (Array.isArray(value)) return '[' + value.map(stable).join(',') + ']';
    const keys = Object.keys(value).sort();
    return '{' + keys.map(k => asciiString(k) + ':' + stable(value[k])).join(',') + '}';
  };
  process.stdout.write(Buffer.from(stable(document), 'utf8').toString('hex') + '\n');
  process.exit(0);
}

if (process.argv.includes('--read')) {
  const target = process.argv[process.argv.indexOf('--read') + 1];
  const document = loadGovernedData(target);
  process.stdout.write(Buffer.from(canon(document), 'utf8').toString('hex') + '\n');
  process.exit(0);
}

// The vector file gained expected output in 1.1.3, so it is an object with a
// `vectors` array rather than a bare array of inputs. A plain array is still
// accepted, which is what ad-hoc test files pass.
const loaded = readGovernedDocument(process.argv[2]);
const raws = Array.isArray(loaded)
  ? loaded
  : loaded.vectors.map(v => v.input);
// Canonical output may contain U+2028 and U+2029, which section 14.3b emits
// directly and which Python's splitlines() treats as line breaks. Printing the
// text would silently misalign a batch comparison, so each result is emitted as
// one line of lowercase hex. --text restores the old behaviour for one vector.
const asText = process.argv.includes('--text');
for (const raw of raws) {
  // The vector *input* stays a raw parse, deliberately and symmetrically with
  // the Python side: it is the string under test, not a governed document, and
  // canonicalisation is what this file exists to compare. Governing it here and
  // not there would compare two different things.
  const parsed=JSON.parse(raw);
  const canonical = canon(parsed);
  if (asText) { console.log(canonical); continue; }
  console.log(Buffer.from(canonical, 'utf8').toString('hex'));
}
