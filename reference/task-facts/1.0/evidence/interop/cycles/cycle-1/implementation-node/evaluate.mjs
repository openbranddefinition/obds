import fs from 'node:fs';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
export class Invalid extends Error { constructor(reason) {super(reason);this.reason=reason;} }
const fail = reason => {throw new Invalid(reason);};
const own=(o,k)=>Object.hasOwn(o,k);
const object=x=>x!==null && typeof x==='object' && !Array.isArray(x);
export function parseStrict(bytes) {
  let s; try {s=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);} catch {fail('JSON_PARSE_ERROR');}
  let i=0, noncanonical=false;
  const ws=()=>{while(/[\x20\t\r\n]/.test(s[i]??'!'))i++;};
  function string() {
    const start=i++; let closed=false;
    while(i<s.length) {const c=s[i++]; if(c==='"'){closed=true;break;} if(c==='\\'){if(i>=s.length)break;const e=s[i++];if(e==='u'){if(!/^[0-9a-fA-F]{4}$/.test(s.slice(i,i+4)))fail('JSON_PARSE_ERROR');i+=4;}else if(!'"\\/bfnrt'.includes(e))fail('JSON_PARSE_ERROR');}else if(c.charCodeAt(0)<32)fail('JSON_PARSE_ERROR');}
    if(!closed)fail('JSON_PARSE_ERROR');try{return JSON.parse(s.slice(start,i));}catch{fail('JSON_PARSE_ERROR');}
  }
  function value(){ws();const c=s[i];if(c==='"')return string();
    if(c==='{'){i++;ws();const o=Object.create(null);if(s[i]==='}'){i++;return o;}while(true){ws();if(s[i]!=='"')fail('JSON_PARSE_ERROR');const k=string();if(own(o,k))fail('JSON_PARSE_ERROR');ws();if(s[i++]!==':')fail('JSON_PARSE_ERROR');o[k]=value();ws();const d=s[i++];if(d==='}')return o;if(d!==',')fail('JSON_PARSE_ERROR');}}
    if(c==='['){i++;ws();const a=[];if(s[i]===']'){i++;return a;}while(true){a.push(value());ws();const d=s[i++];if(d===']')return a;if(d!==',')fail('JSON_PARSE_ERROR');}}
    for(const [token,v] of [['true',true],['false',false],['null',null]])if(s.startsWith(token,i)){i+=token.length;return v;}
    const m=s.slice(i).match(/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/);if(!m)fail('JSON_PARSE_ERROR');i+=m[0].length;
    if(/[.eE]/.test(m[0]))noncanonical=true;else if(BigInt(m[0])>9007199254740991n || BigInt(m[0])< -9007199254740991n)noncanonical=true;
    return Number(m[0]);
  }
  const result=value();ws();if(i!==s.length)fail('JSON_PARSE_ERROR');if(noncanonical)fail('NON_CANONICAL_INPUT');validateTFJ(result);return result;
}
export function validateTFJ(x,seen=new Set()) {
  if(x===null || typeof x==='boolean')return;
  if(typeof x==='number'){if(!Number.isSafeInteger(x))fail('NON_CANONICAL_INPUT');return;}
  if(typeof x==='string'){for(const c of x){const n=c.codePointAt(0);if(n>=0xd800 && n<=0xdfff)fail('NON_CANONICAL_INPUT');}return;}
  if(!Array.isArray(x)&&!object(x))fail('NON_CANONICAL_INPUT');if(seen.has(x))fail('NON_CANONICAL_INPUT');seen.add(x);
  if(Array.isArray(x)){for(let i=0;i<x.length;i++)validateTFJ(x[i],seen);}else{if(![Object.prototype,null].includes(Object.getPrototypeOf(x)))fail('NON_CANONICAL_INPUT');for(const k of Object.keys(x)){validateTFJ(k,seen);validateTFJ(x[k],seen);}}seen.delete(x);
}
export function scalarCompare(a,b){const aa=Array.from(a,c=>c.codePointAt(0)),bb=Array.from(b,c=>c.codePointAt(0));for(let i=0;i<Math.min(aa.length,bb.length);i++)if(aa[i]!==bb[i])return aa[i]-bb[i];return aa.length-bb.length;}
export function canonical(x){validateTFJ(x);function emit(v){if(v===null||typeof v!=='object')return JSON.stringify(v);if(Array.isArray(v))return '['+v.map(emit).join(',')+']';return '{'+Object.keys(v).sort(scalarCompare).map(k=>JSON.stringify(k)+':'+emit(v[k])).join(',')+'}';}return emit(x);}
export const hash=x=>'sha256:'+crypto.createHash('sha256').update(canonical(x),'utf8').digest('hex');
const schema=JSON.parse(fs.readFileSync(new URL('./schemas/task-facts.schema.json',import.meta.url),'utf8'));
// Implements the schema vocabulary used by the supplied frozen schema.
function matches(x,s){if(s.$ref)return matches(x,schema.$defs[s.$ref.split('/').at(-1)]);if(s.oneOf&&s.oneOf.filter(v=>matches(x,v)).length!==1)return false;
if(own(s,'const')&&canonical(x)!==canonical(s.const))return false;if(s.enum&&!s.enum.some(v=>canonical(x)===canonical(v)))return false;
if(s.type && !({object:object(x),array:Array.isArray(x),string:typeof x==='string',boolean:typeof x==='boolean',integer:Number.isSafeInteger(x)})[s.type])return false;
if(typeof x==='string'&&((s.minLength!==undefined&&Array.from(x).length<s.minLength)||(s.pattern&&!new RegExp(s.pattern).test(x))))return false;
if(Array.isArray(x)){if(s.minItems!==undefined&&x.length<s.minItems)return false;if(s.uniqueItems&&new Set(x.map(canonical)).size!==x.length)return false;if(s.items&&!x.every(v=>matches(v,s.items)))return false;}
if(object(x)){if(s.required&&!s.required.every(k=>own(x,k)))return false;for(const k of Object.keys(x)){if(s.propertyNames&&!matches(k,s.propertyNames))return false;if(s.properties&&own(s.properties,k)){if(!matches(x[k],s.properties[k]))return false;}else if(s.additionalProperties===false)return false;else if(object(s.additionalProperties)&&!matches(x[k],s.additionalProperties))return false;}}return true;}
const check=(x,name)=>{if(!matches(x,schema.$defs[name]))fail('SCHEMA_INVALID');};
function date(v){if(typeof v!=='string'||v.length!==10||!/^\d{4}-\d{2}-\d{2}$/.test(v))return false;const [y,m,d]=v.split('-').map(Number);return y>=1&&m>=1&&m<=12&&d>=1&&d<=([31,(y%4===0&&(y%100!==0||y%400===0))?29:28,31,30,31,30,31,31,30,31,30,31][m-1]);}
function instant(v){if(typeof v!=='string')return false;const m=v.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(Z|([+-])(\d{2}):(\d{2}))$/);return !!m&&m[0].length===v.length&&date(m[1])&&+m[2]<24&&+m[3]<60&&+m[4]<60&&m[5]!=='-00:00'&&(m[5]==='Z'||(+m[7]<=14&&+m[8]<60&&(+m[7]!==14||+m[8]===0)));}
const text=x=>typeof x==='string'&&x.length>0;
const pair=x=>Array.isArray(x)&&x.length===2&&x.every(text);
function typed(x,t){switch(t){case 'string':return text(x);case 'boolean':return typeof x==='boolean';case 'integer':return Number.isSafeInteger(x);case 'date':return date(x);case 'date-time':return instant(x);case 'string-set':case 'association-set':return Array.isArray(x)&&x.length>0&&x.every(t==='string-set'?text:pair)&&new Set(x.map(canonical)).size===x.length;default:return false;}}
function validateBound(s,c,v){check(s,'snapshot');for(const k of Object.keys(s.facts))if(!own(s.declarations,k))fail('UNDECLARED_FACT');for(const k of Object.keys(s.facts).sort(scalarCompare)){const f=s.facts[k];if(f.state==='known'&&!typed(f.value,s.declarations[k].type))fail('TYPE_MISMATCH');}
const used=new Set();for(const [k,f] of Object.entries(s.facts))for(const r of f.evidenceRefs){if(!own(s.evidence,r)||s.evidence[r].fact!==k)fail('EVIDENCE_REFERENCE');used.add(r);}for(const k of Object.keys(s.evidence))if(!used.has(k))fail('EVIDENCE_REFERENCE');check(v,'verificationContext');check(c,'condition');
for(const a of c.all){if(!own(s.declarations,a.fact))fail('UNDECLARED_FACT');const t=s.declarations[a.fact].type;if(a.op==='equals'){if(t.endsWith('-set'))fail('OPERATOR_TYPE');if(t==='date'||t==='date-time'){if(!date(a.value)&&!instant(a.value))fail('TYPE_MISMATCH');}else if(!typed(a.value,t))fail('TYPE_MISMATCH');}else if(a.op==='contains'){if(!t.endsWith('-set'))fail('OPERATOR_TYPE');if(!(t==='string-set'?text(a.value):pair(a.value)))fail('TYPE_MISMATCH');}}
}
function atom(s,a,v,h){const f=s.facts[a.fact];if(!f)return ['UNKNOWN','FACT_MISSING'];const t=s.task;let verified=v.snapshotHash===h&&v.taskId===t.id&&v.artifactHash===t.artifactHash&&v.inputPackageHash===t.inputPackageHash;const assertion={...f};delete assertion.evidenceRefs;
for(const r of f.evidenceRefs){const e=s.evidence[r];verified=verified&&e.status==='verified'&&v.acceptedEvidence[r]===hash(e)&&e.assertionHash===hash(assertion)&&e.taskId===t.id&&e.artifactHash===t.artifactHash&&e.inputPackageHash===t.inputPackageHash;}
if(!verified)return ['UNKNOWN','EVIDENCE_UNVERIFIED'];if(f.state==='unknown')return ['UNKNOWN','FACT_UNKNOWN'];if(f.state==='contradictory')return ['CONTRADICTORY','FACT_CONTRADICTORY'];const type=s.declarations[a.fact].type;
if(f.state==='known'&&type==='association-set'){const m=new Map();for(const [source,target] of f.value){if(m.has(source)&&m.get(source)!==target)return ['CONTRADICTORY','ASSOCIATION_CONFLICT'];m.set(source,target);}}
let yes=false;if(a.op==='present')yes=f.state==='known';else if(a.op==='absent')yes=f.state==='empty';else if(f.state==='known'){if(a.op==='contains')yes=f.value.some(x=>canonical(x)===canonical(a.value));else if(type==='date'||type==='date-time'){if(date(f.value)!==date(a.value))return ['UNKNOWN','TIME_BASIS_UNRESOLVED'];yes=type==='date'?f.value===a.value:Date.parse(f.value)===Date.parse(a.value);}else yes=f.value===a.value;}
return yes?['APPLIES','ALL_TRUE']:['DOES_NOT_APPLY','PREDICATE_FALSE'];}
export function evaluate(s,c,v){let h=null;let id=null;try{validateTFJ([s,c,v]);if(!object(c)||!matches(c.id??null,schema.$defs.identifier))fail('SCHEMA_INVALID');id=c.id;h=hash(s);validateBound(s,c,v);const rank={APPLIES:0,DOES_NOT_APPLY:1,UNKNOWN:2,CONTRADICTORY:3};const r=c.all.map(a=>atom(s,a,v,h)).sort((a,b)=>rank[b[0]]-rank[a[0]]||scalarCompare(a[1],b[1]))[0];return {conditionId:id,snapshotHash:h,outcome:r[0],reason:r[1]};}catch(e){if(!(e instanceof Invalid))throw e;return {conditionId:id,snapshotHash:h,outcome:'INVALID',reason:e.reason};}}
const unbound=reason=>({family:null,caseId:null,conditionId:null,snapshotHash:null,outcome:'INVALID',reason});
export function evaluate_family(f){validateTFJ(f);check(f,'routingFamily');if(new Set(f.cases.map(c=>c.id)).size!==f.cases.length)fail('DUPLICATE_ID');for(const c of f.cases)if(new Set(c.conditions.map(a=>a.id)).size!==c.conditions.length)fail('DUPLICATE_ID');const out=[];for(const c of f.cases)for(const a of c.conditions){let r;try{check(f,'family');check(c,'case');r=evaluate(c.snapshot,a,c.verificationContext);}catch(e){if(!(e instanceof Invalid))throw e;r={conditionId:a.id,snapshotHash:hash(c.snapshot),outcome:'INVALID',reason:e.reason};}out.push({family:f.family,caseId:c.id,...r});}return out;}
export function evaluate_path(path){let raw;try{raw=fs.readFileSync(path);}catch{return [unbound('INPUT_IO_ERROR')];}try{return evaluate_family(parseStrict(raw));}catch(e){if(!(e instanceof Invalid))throw e;return [unbound(e.reason)];}}
export function main(paths){const results=paths.flatMap(evaluate_path);process.stdout.write(JSON.stringify({results},null,2)+'\n');return results.some(r=>r.outcome==='INVALID')?2:0;}
if(process.argv[1]&&fileURLToPath(import.meta.url)===fs.realpathSync(process.argv[1]))process.exitCode=main(process.argv.slice(2));
