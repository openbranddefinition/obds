import test from 'node:test';
import assert from 'node:assert/strict';
import {parseStrict,canonical,hash,evaluate,evaluate_family,Invalid,evaluate_path} from './evaluate.mjs';
const parse=s=>parseStrict(Buffer.from(s));
const rejects=(s,r)=>assert.throws(()=>parse(s),e=>e instanceof Invalid&&e.reason===r);
const digest='sha256:'+'0'.repeat(64);
function setup(type='string',value='yes',state='known'){
 const fact={state,evidenceRefs:['e']};if(state==='known')fact.value=value;
 const s={contractVersion:'0.1',task:{id:'task',action:'inspect',artifactHash:digest,inputPackageHash:digest},declarations:{f:{type}},facts:{f:fact},evidence:{}};
 const assertion={...fact};delete assertion.evidenceRefs;
 s.evidence.e={supplier:'test',sourceRef:'test',method:'test',verifier:'test',status:'verified',fact:'f',assertionHash:hash(assertion),taskId:'task',artifactHash:digest,inputPackageHash:digest};
 const v={taskId:'task',artifactHash:digest,inputPackageHash:digest,snapshotHash:hash(s),acceptedEvidence:{e:hash(s.evidence.e)}};
 const c={id:'condition',all:[{fact:'f',op:'present'}],requiresDefined:[]};return {s,v,c};
}
const family=({s,v,c})=>({family:'family',cases:[{id:'case',snapshot:s,verificationContext:v,conditions:[c]}]});
test('strict syntax wins over TFJ and rejects duplicate decoded keys',()=>{for(const x of ['[1.0,NaN]','{"a":1,"\\u0061":2}','\ufeff{}','{} true','{"x":Infinity}','[1,]'])rejects(x,'JSON_PARSE_ERROR');});
test('TFJ rejects number categories and scalars',()=>{for(const x of ['1.0','1e0','-0.0','9007199254740992','"\\ud800"'])rejects(x,'NON_CANONICAL_INPUT');assert.equal(canonical(parse('-0')),'0');});
test('canonical scalar sorting and controls',()=>{assert.equal(canonical({'\u{10000}':1,'\ue000':2,a:'\u0001\b\t\n\f\r/é'}),'{"a":"\\u0001\\b\\t\\n\\f\\r/é","":2,"𐀀":1}');assert.notEqual(hash(['a','b']),hash(['b','a']));});
test('verified known false and zero are present',()=>{for(const [t,val] of [['boolean',false],['integer',0]]){const {s,v,c}=setup(t,val);assert.equal(evaluate(s,c,v).outcome,'APPLIES');}});
test('bound malformed snapshots have their actual hashes',()=>{const f=family(setup());f.cases[0].snapshot=null;const [r]=evaluate_family(f);assert.equal(r.reason,'SCHEMA_INVALID');assert.equal(r.snapshotHash,hash(null));assert.equal(r.caseId,'case');});
test('routing failures and duplicates suppress every sibling',()=>{let f=family(setup());f.cases.push(structuredClone(f.cases[0]));assert.throws(()=>evaluate_family(f),e=>e.reason==='DUPLICATE_ID');delete f.cases[1].snapshot;assert.throws(()=>evaluate_family(f),e=>e.reason==='SCHEMA_INVALID');});
test('condition errors remain isolated and wrapper errors bind',()=>{const f=family(setup());f.cases[0].conditions.push({id:'bad',all:[],requiresDefined:[]});const r=evaluate_family(f);assert.equal(r[0].outcome,'APPLIES');assert.equal(r[1].reason,'SCHEMA_INVALID');delete f.cases[0].verificationContext;assert.ok(evaluate_family(f).every(x=>x.reason==='SCHEMA_INVALID'&&x.snapshotHash));});
test('attestation changes cannot retain verification',()=>{const {s,v,c}=setup();s.task.action='changed';assert.equal(evaluate(s,c,v).reason,'EVIDENCE_UNVERIFIED');});
test('missing, unknown, empty differ',()=>{for(const [state,expected] of [['unknown','FACT_UNKNOWN'],['empty','PREDICATE_FALSE']]){const {s,v,c}=setup('string',null,state);assert.equal(evaluate(s,c,v).reason,expected);}const {s,v,c}=setup();delete s.facts.f;delete s.evidence.e;v.snapshotHash=hash(s);assert.equal(evaluate(s,c,v).reason,'FACT_MISSING');});
test('relation conflict versus duplicate pairs',()=>{let {s,v,c}=setup('association-set',[['a','b'],['a','c']]);assert.equal(evaluate(s,c,v).reason,'ASSOCIATION_CONFLICT');({s,v,c}=setup('association-set',[['a','b'],['a','b']]));assert.equal(evaluate(s,c,v).reason,'TYPE_MISMATCH');});
test('temporal equality preserves dates and resolves offsets',()=>{const {s,v,c}=setup('date-time','2026-10-01T00:00:00+02:00');c.all=[{fact:'f',op:'equals',value:'2026-09-30T22:00:00Z'}];assert.equal(evaluate(s,c,v).outcome,'APPLIES');c.all[0].value='2026-09-30';assert.equal(evaluate(s,c,v).reason,'TIME_BASIS_UNRESOLVED');});
test('bad Gregorian and unresolved offset types fail',()=>{for(const [type,value] of [['date','1900-02-29'],['date-time','2026-01-01T00:00:00-00:00'],['date-time','2026-01-01T00:00:00+14:01']]){const {s,v,c}=setup(type,value);assert.equal(evaluate(s,c,v).reason,'TYPE_MISMATCH');}});
test('conservative unknown dominates false regardless of order',()=>{const {s,v,c}=setup();s.declarations.m={type:'string'};v.snapshotHash=hash(s);c.all=[{fact:'f',op:'absent'},{fact:'m',op:'present'}];assert.equal(evaluate(s,c,v).reason,'FACT_MISSING');c.all.reverse();assert.equal(evaluate(s,c,v).reason,'FACT_MISSING');});
test('unused malformed fact invalidates snapshot before bad condition',()=>{const {s,v,c}=setup('integer',true);c.all=[];assert.equal(evaluate(s,c,v).reason,'TYPE_MISMATCH');});
test('I/O returns a single fully unbound result',()=>{const [r]=evaluate_path('/nonexistent-task-facts-node-input');assert.deepEqual(r,{family:null,caseId:null,conditionId:null,snapshotHash:null,outcome:'INVALID',reason:'INPUT_IO_ERROR'});});
test('CLI preserves file order, unbound errors, and exit status',async()=>{
 const fs=await import('node:fs');const path=await import('node:path');const {spawnSync}=await import('node:child_process');const {fileURLToPath}=await import('node:url');
 const dir=fs.mkdtempSync(new URL('./cli-test-',import.meta.url));try{const good=path.join(dir,'good.json'),bad=path.join(dir,'bad.json');fs.writeFileSync(good,JSON.stringify(family(setup())));fs.writeFileSync(bad,'[1.0,NaN]');const cli=fileURLToPath(new URL('./evaluate.mjs',import.meta.url));let run=spawnSync(process.execPath,[cli,good],{encoding:'utf8'});assert.equal(run.status,0);assert.equal(JSON.parse(run.stdout).results[0].outcome,'APPLIES');run=spawnSync(process.execPath,[cli,bad,good],{encoding:'utf8'});assert.equal(run.status,2);const r=JSON.parse(run.stdout).results;assert.equal(r.length,2);assert.equal(r[0].reason,'JSON_PARSE_ERROR');assert.equal(r[0].snapshotHash,null);assert.equal(r[1].outcome,'APPLIES');}finally{fs.rmSync(dir,{recursive:true});}
});
