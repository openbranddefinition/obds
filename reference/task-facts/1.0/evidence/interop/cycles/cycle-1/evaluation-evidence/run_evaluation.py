import copy, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]; OUT=ROOT/'evaluation-evidence'
TMP=pathlib.Path(tempfile.mkdtemp(prefix='obds-independent-probes-',dir='/private/tmp'))
INPUTS=TMP/'inputs'; INPUTS.mkdir()
def canon(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(v): return 'sha256:'+hashlib.sha256(canon(v)).hexdigest()
def att(c):
 s=c['snapshot']; t=s['task']; s['evidence']={}
 for k,f in s['facts'].items():
  refs=[k+':0',k+':1'] if f['state']=='contradictory' else [k+':0']; f['evidenceRefs']=refs
  for ref in refs:
   s['evidence'][ref]={'supplier':'independent-probe','sourceRef':'probe:'+ref,'method':'synthetic-review','verifier':'probe-verifier','status':'verified','fact':k,'assertionHash':digest({k:v for k,v in f.items() if k!='evidenceRefs'}),'taskId':t['id'],'artifactHash':t['artifactHash'],'inputPackageHash':t['inputPackageHash']}
 c['verificationContext']={'taskId':t['id'],'artifactHash':t['artifactHash'],'inputPackageHash':t['inputPackageHash'],'snapshotHash':digest(s),'acceptedEvidence':{k:digest(v) for k,v in s['evidence'].items()}}
 return c
def case(spec=None):
 spec=spec or {'items':('string-set',['claim-A','claim-B'])}
 c={'id':'probe-case','snapshot':{'contractVersion':'0.1','task':{'id':'task:probe','action':'inspect','artifactHash':'sha256:'+'1'*64,'inputPackageHash':'sha256:'+'2'*64},'declarations':{k:{'type':t} for k,(t,v) in spec.items()},'facts':{k:{'state':'known','value':v} for k,(t,v) in spec.items()},'evidence':{}},'conditions':[{'id':'rule-'+str(i),'all':[{'fact':k,'op':'present'}],'requiresDefined':[]} for i,k in enumerate(spec)]}
 return att(c)
probes={}; relationships=[]
def add(name,c=None,raw=None):
 value={'family':'independent-probe','cases':[c or case()]}
 probes[name]=raw if raw is not None else json.dumps(value,ensure_ascii=False)
 return value
base=case(); add('base',base)
c=copy.deepcopy(base); c['snapshot']['facts']['items']['value'].reverse(); att(c);add('set-reordered',c);relationships.append(('base','set-reordered','different'))
def rev(v):
 if isinstance(v,dict):return {k:rev(x) for k,x in reversed(list(v.items()))}
 if isinstance(v,list):return [rev(x) for x in v]
 return v
add('object-reordered',raw=json.dumps(rev({'family':'independent-probe','cases':[base]}),ensure_ascii=False));relationships.append(('base','object-reordered','equal'))
for name,value in [('duplicate-set',['claim-A','claim-A']),('wrong-scalar-set','claim-A')]:
 c=case();c['snapshot']['facts']['items']['value']=value;att(c);add(name,c)
for state in ['missing','empty','unknown','contradictory']:
 c=case()
 if state=='missing':del c['snapshot']['facts']['items']
 else:c['snapshot']['facts']['items']={'state':state}
 att(c);add(state,c)
relationships += [('missing','empty','different'),('missing','unknown','different')]
for field in ['id','action','artifactHash','inputPackageHash']:
 c=case();c['snapshot']['task'][field]='task:changed' if field=='id' else 'changed' if field=='action' else 'sha256:'+'3'*64
 add('changed-'+field+'-stale',c);relationships.append(('base','changed-'+field+'-stale','different'))
 att(c);add('changed-'+field+'-verified',c)
for name,spec in [('multiple-claims',{'claims':('string-set',['C01','C06','C99'])}),('multiple-assets',{'assets':('string-set',['portrait','font','logo'])}),('partner-portrait',{'partners':('string-set',['OM']),'assets':('string-set',['portrait'])}),('campaign-claim',{'campaign':('string','AC26'),'claims':('string-set',['C06'])}),('association-conflict',{'pairs':('association-set',[['a','b'],['a','c']])}),('duplicate-association',{'pairs':('association-set',[['a','b'],['a','b']])})]:add(name,case(spec))
c=case(); c['conditions'].append({'id':'bad','all':[],'requiresDefined':[]});add('malformed-condition-valid-sibling',c)
for name,s in [('null',None),('array',[]),('boolean',True),('integer',7),('string','hello'),('object',{'\U00010000':1,'\ue000':2,'null':None})]:
 c=case();c['snapshot']=s;add('malformed-snapshot-'+name,c)
c=case();c['conditions']*=2;add('duplicate-condition-id',c)
v={'family':'independent-probe','cases':[case(),case()]};add('duplicate-case-id',raw=json.dumps(v))
for name,raw in [('malformed-json','{"family":'),('nan','{"x":NaN}'),('infinity','{"x":Infinity}'),('nan-after-float','[1.0,NaN]'),('duplicate-key','{"x":1,"x":2}'),('escaped-duplicate-key','{"x":1,"\\u0078":2}'),('bom','\ufeff{}'),('trailing','{}{}'),('float','{"x":1.0}'),('exponent','{"x":1e0}'),('unsafe-integer','{"x":9007199254740992}'),('surrogate','{"x":"\\ud800"}'),('minus-zero','-0'),('top-array','[]')]:add('raw-'+name,raw=raw)
for name,t,v in [('unicode','string','é e\u0301 \U0001f600 \u2028 / \\ " \b\t\n\f\r\x01'),('false','boolean',False),('true','boolean',True),('zero','integer',0),('maxint','integer',9007199254740991),('minint','integer',-9007199254740991),('numeric-string','string','000123'),('null','string',None),('bool-as-int','integer',True),('int-as-bool','boolean',1),('integer-as-string','string',12)]:
 c=case({'value':(t,v)});c['conditions'][0]['all']=[{'fact':'value','op':'equals','value':v}];add('value-'+name,c)
for name,t,v,operand in [('date-instant','date','2026-09-30','2026-09-30T00:00:00Z'),('instant-date','date-time','2026-09-30T00:00:00Z','2026-09-30'),('offset-equal','date-time','2026-10-01T00:00:00+02:00','2026-09-30T22:00:00Z'),('year-one','date-time','0001-01-01T00:00:00Z','0001-01-01T00:00:00Z'),('leap-valid','date','2000-02-29','2000-02-29'),('leap-invalid','date','1900-02-29','1900-02-29'),('unknown-offset','date-time','2026-01-01T00:00:00-00:00','2026-01-01T00:00:00Z')]:
 c=case({'when':(t,v)});c['conditions'][0]['all']=[{'fact':'when','op':'equals','value':operand}];add('time-'+name,c)
for key in ['constructor','toString','hasOwnProperty']:
 add('special-fact-'+key,case({key:('string','value')}))
for name,mutation in [('missing-context',lambda c:c.pop('verificationContext')),('extra-case',lambda c:c.update(extra=True)),('duplicate-atoms',lambda c:c['conditions'][0]['all'].__imul__(2)),('missing-requires',lambda c:c['conditions'][0].pop('requiresDefined')),('bad-op',lambda c:c['conditions'][0]['all'][0].update(op='other')),('absent-operand',lambda c:c['conditions'][0]['all'][0].update(op='absent',value=None))]:
 c=case();mutation(c);add(name,c)
for name,raw in probes.items():(INPUTS/(name+'.json')).write_text(raw)
shutil.copytree(INPUTS,OUT/'probe-inputs',dirs_exist_ok=True)
(OUT/'probe-relationships.json').write_text(json.dumps(relationships,indent=2))
commands={'python':['python3',str(ROOT/'implementation-python'/'evaluate.py')],'node':['node',str(ROOT/'implementation-node'/'evaluate.mjs')]}
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'); results={}; metadata={}
for suite,paths in [('fixtures',sorted((ROOT/'frozen-contract'/'fixtures').glob('*.json'))),('regressions',sorted((ROOT/'frozen-contract'/'regressions'/'inputs').glob('*.json'))),('probes',sorted(INPUTS.glob('*.json')))]:
 for impl,cmd in commands.items():
  p=subprocess.run(cmd+list(map(str,paths)),cwd=TMP,env=env,capture_output=True)
  (OUT/(suite+'-'+impl+'.json')).write_bytes(p.stdout);(OUT/(suite+'-'+impl+'.stderr')).write_bytes(p.stderr)
  results[suite,impl]=json.loads(p.stdout)['results'];metadata[suite+'-'+impl]={'command':cmd+list(map(str,paths)),'cwd':str(TMP),'exitCode':p.returncode,'files':[p.name for p in paths],'records':len(results[suite,impl])}
# Freeze every output before inspecting expected/reference information.
frozen={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in [suite+'-'+impl+'.json' for suite in ['fixtures','regressions','probes'] for impl in ['python','node']]}
(OUT/'RESULTS-FROZEN.json').write_text(json.dumps(frozen,indent=2));(OUT/'execution.json').write_text(json.dumps(metadata,indent=2))
comparison={}
for suite in ['fixtures','regressions','probes']:
 a,b=results[suite,'python'],results[suite,'node'];comparison[suite]={'pythonRecords':len(a),'nodeRecords':len(b),'equal':a==b,'divergences':[{'index':i,'python':x,'node':y} for i,(x,y) in enumerate(zip(a,b)) if x!=y]}
# Split counter-probe output by re-running single files to retain robust filename boundaries.
byname={}
for path in sorted(INPUTS.glob('*.json')):
 byname[path.stem]={}
 for impl,cmd in commands.items():
  p=subprocess.run(cmd+[str(path)],cwd=TMP,env=env,capture_output=True);byname[path.stem][impl]=json.loads(p.stdout)['results']
(OUT/'probe-results-by-name.json').write_text(json.dumps(byname,indent=2))
checks=[]
for a,b,relation in relationships:
 for impl in commands:
  ah=byname[a][impl][0]['snapshotHash'];bh=byname[b][impl][0]['snapshotHash'];checks.append({'a':a,'b':b,'implementation':impl,'requirement':relation,'pass':ah==bh if relation=='equal' else ah!=bh})
comparison['identityChecks']=checks
(OUT/'comparison.json').write_text(json.dumps(comparison,indent=2))
print(json.dumps(comparison,indent=2));print('Probes:',len(probes))
