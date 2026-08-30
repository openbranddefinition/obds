import fs from 'node:fs';

function normaliseString(s) {
  // OBDS 14.3 step 2 then step 1: line endings to LF, then Unicode NFC.
  // Applies to string values and object keys alike.
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
const raws = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
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
