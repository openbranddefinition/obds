"""Ratified F1–F5 production boundaries, including adversarial lifecycle cases."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import jsonschema
import pytest

from obds_ref.canonical import artefact_hash, manifest_content_hash, sha256_id, text_hash
from obds_ref.compiler import build_all, build_target, load_data, validate_manifest, validate_plan, ValidationFailure
from obds_ref.generation import target_filename, load_generation_artifact, generation_relative
from obds_ref.runtime import run_generation_with_model, run_with_model, run_assembled_with_model
from obds_ref.model_input import render_model_input

ROOT = Path(__file__).resolve().parents[3]
ASSEMBLY = ROOT / 'reference/context-assembly'


def minimal():
    return load_data(ROOT/'examples/foundation-minimal/manifest.yaml'), load_data(ROOT/'examples/foundation-minimal/build-plan.yaml')


def assembly():
    sys.path.insert(0, str(ASSEMBLY))
    try:
        from assemble_context import assemble
        import validate_review
        from build_views import build_views
        base = ASSEMBLY/'examples'
        manifest = load_data(base/'manifest.yaml')
        context = load_data(base/'compiled-social-copy-global-en.json')
        index, chapters = build_views(manifest, load_data(base/'chapter-map.yaml'))
        request = load_data(base/'assembly-request-create.yaml')
        package, text = assemble(context, index, chapters, request)
        return context, package, text, index, chapters, request
    finally:
        sys.path.pop(0)


def reseal(package):
    rendered = render_model_input(package['slots'])
    package['modelInputHash'] = text_hash(rendered)
    package['assemblyHash'] = sha256_id({k:v for k,v in package.items() if k!='assemblyHash'})
    return rendered


@pytest.mark.parametrize('target_id', ['../escaped', '/absolute/path', '.', '..', 'CON', 'x/y', 'x\\y', 'a'*400, 'é', 'e\u0301', 'TARGET', 'target'])
def test_f1_safe_target_mapping_without_id_restriction(tmp_path, target_id):
    manifest, plan = minimal()
    plan['targets'][0]['id'] = target_id
    assert validate_plan(plan) == []
    report = build_all(manifest, plan, output_dir=tmp_path/'out')
    target = report['targets'][0]
    artifact = tmp_path/'out'/target['artifactRef']
    assert artifact.resolve().is_relative_to((tmp_path/'out').resolve())
    assert artifact.name == target_filename(target_id)+'.context.json'
    assert load_generation_artifact(tmp_path/'out', report['generationId'], target_id)['targetId'] == target_id
    assert not (tmp_path/'escaped.context.json').exists()


def test_f1_canonical_ids_and_distinct_case_have_correct_names():
    assert target_filename('é') == target_filename('e\u0301')
    assert target_filename('A') != target_filename('a')


@pytest.mark.parametrize('where', ['generations', 'generation', 'artifact', 'latest'])
def test_f1_output_symlinks_are_refused(tmp_path, where):
    manifest, plan = minimal()
    out = tmp_path/'out'; out.mkdir()
    external = tmp_path/'external'; external.mkdir()
    if where == 'generations':
        (out/'generations').symlink_to(external, target_is_directory=True)
    elif where == 'latest':
        (out/'build-report.yaml').symlink_to(external/'untouched')
    else:
        report = build_all(manifest, plan, output_dir=out)
        if where == 'generation':
            import shutil
            dest = out/generation_relative(report['generationId'])
            shutil.rmtree(dest)
            dest.symlink_to(external, target_is_directory=True)
        else:
            dest = out/report['targets'][0]['artifactRef']
            dest.unlink()
            dest.symlink_to(external/'untouched')
    with pytest.raises(ValidationFailure):
        build_all(manifest, plan, output_dir=out)
    assert list(external.iterdir()) == []
    root_link = tmp_path/'linked-output'
    root_link.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValidationFailure):
        build_all(manifest, plan, output_dir=root_link)
    assert list(external.iterdir()) == []


def test_f2_failed_generation_never_falls_back_and_rollback_is_explicit(tmp_path):
    manifest, plan = minimal()
    a = build_all(manifest, plan, output_dir=tmp_path)
    old_bytes = (tmp_path/a['targets'][0]['artifactRef']).read_bytes()
    manifest['elements'][0]['state'] = 'unknown'
    manifest['elements'][0].pop('value')
    manifest['approval']['contentHash'] = manifest_content_hash(manifest)
    plan['manifestRef']['contentHash'] = manifest['approval']['contentHash']
    b = build_all(manifest, plan, output_dir=tmp_path)
    assert a['generationId'] != b['generationId']
    assert b['targets'][0]['status'] == 'failed'
    assert not list((tmp_path/generation_relative(b['generationId'])).glob('*.context.json'))
    calls=[]
    kwargs = dict(target_id=plan['targets'][0]['id'], task_input='hello', model=lambda prompt:(calls.append(prompt) or 'hello'))
    failed = run_generation_with_model(tmp_path, b['generationId'], **kwargs)
    assert failed['decision'] == 'build_failed' and calls == []
    assert failed['generationId'] == b['generationId']
    missing = run_generation_with_model(tmp_path, 'sha256:'+'0'*64, **kwargs)
    assert missing['decision'] == 'no_valid_artifact' and calls == []
    rollback = run_generation_with_model(tmp_path, a['generationId'], **kwargs)
    assert rollback['decision'] == 'released' and len(calls) == 1
    assert (tmp_path/a['targets'][0]['artifactRef']).read_bytes() == old_bytes


def test_f2_removed_target_and_same_generation_rebuild(tmp_path):
    manifest, plan = minimal()
    a = build_all(manifest, plan, output_dir=tmp_path)
    assert build_all(manifest, plan, output_dir=tmp_path) == a
    old_id = plan['targets'][0]['id']
    plan['targets'][0]['id'] = 'replacement'
    b = build_all(manifest, plan, output_dir=tmp_path)
    result = run_generation_with_model(tmp_path, b['generationId'], target_id=old_id, task_input='hello', model=lambda _:pytest.fail('fallback model call'))
    assert result['decision'] == 'no_valid_artifact'


def test_f2_foreign_artifact_under_requested_generation_is_rejected(tmp_path):
    manifest, plan = minimal()
    a = build_all(manifest, plan, output_dir=tmp_path)
    artifact = tmp_path/a['targets'][0]['artifactRef']
    payload = load_data(artifact)
    payload['slots']['factGrounding'] = 'tampered'
    payload['artifactHash'] = artefact_hash(payload)
    artifact.write_text(json.dumps(payload))
    result = run_generation_with_model(tmp_path, a['generationId'], target_id=plan['targets'][0]['id'], task_input='hello', model=lambda _:pytest.fail('tampered model call'))
    assert result['decision'] == 'no_valid_artifact'


@pytest.mark.parametrize('slot', ['hardBoundaries','factGrounding','stateMap','guidanceContext'])
@pytest.mark.parametrize('change', ['replace', 'erase'])
def test_f3_resealed_slot_cannot_reach_model_or_review(slot, change):
    context, package, _, *_ = assembly()
    package['slots'][slot] = 'foreign brand truth' if change == 'replace' else ''
    rendered = reseal(package)
    result = run_assembled_with_model(context, package, rendered, task_input=package['slots']['taskInput'], model=lambda _:pytest.fail('foreign projection model call'), target_id=context['targetId'])
    assert result['decision'] == 'assembly_failed'
    from validate_review import validate_review
    review = {'kind':'obds-review-result','schemaVersion':'1.0.0','targetId':context['targetId'], 'applicationMode':'review','modelInputHash':package['modelInputHash'],'decision':'pass','findings':[]}
    review['reviewHash'] = sha256_id(review)
    with pytest.raises(ValueError, match='provenance'):
        validate_review(context, package, review)


@pytest.mark.parametrize('selection', ['hardBoundaryElementIds','factElementIds','gapElementIds'])
def test_f3_resealed_required_selection_omission_is_refused(selection):
    context, package, _, *_ = assembly()
    package['selection'][selection] = []
    result = run_assembled_with_model(context, package, reseal(package), task_input=package['slots']['taskInput'], model=lambda _:pytest.fail('omitted required model call'))
    assert result['decision'] == 'assembly_failed'


def test_f3_resealed_chapter_prose_is_not_authoritative():
    context, package, _, index, chapters, request = assembly()
    from assemble_context import assemble
    chapters = deepcopy(chapters)
    chapter = next(c for c in chapters['chapters'] if c['id'] in request['selection']['reasoningChapterIds'])
    chapter['content'] += '\nForeign approved claim.'
    chapter['chapterHash'] = sha256_id({k:v for k,v in chapter.items() if k!='chapterHash'})
    chapters['chapterSetHash'] = sha256_id({k:v for k,v in chapters.items() if k!='chapterSetHash'})
    with pytest.raises(ValueError, match='derive'):
        assemble(context, index, chapters, request)


@pytest.mark.parametrize('field,value', [('owner',None),('name',12),('elements',5),('elements',{}),('valueContracts',5),('profiles',{}),('approval',[])])
def test_f4_schema_before_semantics(field, value):
    manifest, plan = minimal()
    manifest[field] = value
    assert validate_manifest(manifest)
    with pytest.raises(ValidationFailure):
        build_all(manifest, plan)


@pytest.mark.parametrize('value', [None, 5, [], 'manifest'])
def test_f4_non_object_manifest_is_controlled(value):
    assert validate_manifest(value)
    with pytest.raises(ValidationFailure):
        build_all(value, minimal()[1])


@pytest.mark.parametrize('field,value', [('approvedBy',True),('approvedBy',' '),('approvedAt','not-a-date'),('approvedAt','2026-02-30T12:00:00Z'),('approvedAt','2026-09-05T12:00:00'),('approvedAt',True),('approvedAt','2026-09-05T12:00:00+99:99')])
def test_f4_approval_format_is_actually_checked(field, value):
    manifest, plan = minimal()
    manifest['approval'][field] = value
    assert validate_manifest(manifest)
    with pytest.raises(ValidationFailure):
        build_all(manifest, plan)


@pytest.mark.parametrize('assembled', [False, True])
@pytest.mark.parametrize('failure', ['timeout','exception','none','tuple','request_id'])
def test_f5_model_failed_is_recorded_and_never_released(tmp_path, assembled, failure):
    context, package, text, *_ = assembly()
    calls=[]
    def model(prompt):
        calls.append(prompt)
        if failure == 'timeout': raise TimeoutError('provider timeout')
        if failure == 'exception': raise RuntimeError('provider failure')
        return {'none':None, 'tuple':('text',), 'request_id':('text',5)}[failure]
    path = tmp_path/'records.jsonl'
    kwargs = dict(task_input=package['slots']['taskInput'], model=model, target_id=context['targetId'], record_path=path)
    if assembled:
        result = run_assembled_with_model(context, package, text, **kwargs)
    else:
        result = run_with_model(context, **kwargs)
    assert result['decision'] == 'model_failed' and result['output'] is None
    assert result['modelCall']['called'] is True and len(calls)==1
    from obds_ref.governed_io import read_governed_text
    record = read_governed_text(path.read_text(), is_json=True)
    schema = load_data(ROOT/'schemas/4.0.0/runtime-decision-record.schema.json')
    jsonschema.validate(record, schema)
    old = load_data(ROOT/'schemas/3.0.0/runtime-decision-record.schema.json')
    assert list(jsonschema.Draft202012Validator(old).iter_errors(record))
    assert record['decision'] == 'model_failed' and 'output' not in record


def test_f2_invalid_generation_is_recorded_without_fallback(tmp_path):
    result = run_generation_with_model(tmp_path, '../latest', target_id='x', task_input='hello',
        model=lambda _:pytest.fail('invalid generation model call'), record_path=tmp_path/'record.jsonl')
    assert result['decision']=='no_valid_artifact' and result['generationId'] is None
    assert (tmp_path/'record.jsonl').exists()


def test_f3_valid_generation_assembly_and_failed_generation(tmp_path):
    base = ASSEMBLY/'examples'
    manifest = load_data(base/'manifest.yaml'); plan=load_data(base/'build-plan.yaml')
    a = build_all(manifest, plan, output_dir=tmp_path)
    context, package, text, *_ = assembly()
    calls=[]
    kwargs=dict(target_id=context['targetId'],task_input=package['slots']['taskInput'],
        model=lambda prompt:(calls.append(prompt) or 'A useful product.'),package=package,model_input_text=text)
    good=run_generation_with_model(tmp_path,a['generationId'],**kwargs)
    assert good['decision']=='released' and calls==[text]
    # New generation has no usable context; the old valid package cannot select A.
    plan['targets']=[t for t in plan['targets'] if t['id']!=context['targetId']]
    b=build_all(manifest,plan,output_dir=tmp_path)
    refused=run_generation_with_model(tmp_path,b['generationId'],**kwargs)
    assert refused['decision']=='no_valid_artifact' and len(calls)==1


def test_f4_low_level_target_build_also_checks_schema_first():
    manifest,plan=minimal();manifest['elements']=5
    with pytest.raises(ValidationFailure):
        build_target(manifest,plan,plan['targets'][0])


def test_f5_failure_and_success_are_append_only(tmp_path):
    manifest,plan=minimal();context=build_target(manifest,plan,plan['targets'][0]).artefact
    path=tmp_path/'records.jsonl'
    def timeout(_):raise TimeoutError('simulated')
    run_with_model(context,task_input='hello',model=timeout,record_path=path)
    before=path.read_bytes()
    result=run_with_model(context,task_input='hello',model=lambda _:('hello','request-2'),record_path=path)
    assert result['decision']=='released' and path.read_bytes().startswith(before)
    from obds_ref.governed_io import read_governed_text
    records=[read_governed_text(line,is_json=True) for line in path.read_text().splitlines()]
    assert [r['decision'] for r in records]==['model_failed','released']
    assert len({r['recordId'] for r in records})==2
