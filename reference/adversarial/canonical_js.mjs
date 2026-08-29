import fs from 'node:fs';

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
  if (typeof v === 'string') return JSON.stringify(v.replace(/\r\n/g,'\n').replace(/\r/g,'\n').normalize('NFC'));
  if (Array.isArray(v)) return '[' + v.map(canon).join(',') + ']';
  if (typeof v === 'object') {
    const mapped = new Map();
    for (const [k,val] of Object.entries(v)) {
      const nk=k.normalize('NFC');
      if (mapped.has(nk)) throw new Error('duplicate key after NFC');
      mapped.set(nk,val);
    }
    // ECMAScript Array.sort compares UTF-16 code units, matching the OBDS 1.0 contract.
    const keys=[...mapped.keys()].sort();
    return '{' + keys.map(k => JSON.stringify(k)+':'+canon(mapped.get(k))).join(',') + '}';
  }
  throw new Error('unsupported');
}
const raws = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const raw of raws) {
  const parsed=JSON.parse(raw);
  console.log(canon(parsed));
}
