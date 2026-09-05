"""OBDS 4.0 production output: safe names and explicitly selected generations."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from .formats import format_checker
from .canonical import canonical_json_bytes, artefact_hash, identity_key, sha256_id
from .governed_io import ValidationFailure, load_data, save_json, save_yaml


def target_filename(target_id: str) -> str:
    # Hash *canonical identity*, not case-folded text or a lossy sanitisation.
    # Fixed ASCII size also handles long IDs and platform-reserved file names.
    return 'target-' + hashlib.sha256(identity_key(target_id).encode('utf-8')).hexdigest()


def generation_identity(manifest_hash, plan_hash, compiler_id, compiler_version):
    return sha256_id({'manifestContentHash': manifest_hash, 'planHash': plan_hash,
                      'compilerId': compiler_id, 'compilerVersion': compiler_version})


def _contained(root, relative):
    root = Path(root)
    if root.is_symlink():
        raise ValidationFailure(["output root must not be a symlink"])
    root = root.resolve()
    path = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValidationFailure(['output path is not relative and contained'])
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValidationFailure(['output path must not traverse a symlink'])
    if not path.resolve().is_relative_to(root):
        raise ValidationFailure(['output path escapes its root'])
    return path


def generation_relative(generation_id):
    if not isinstance(generation_id, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', generation_id):
        raise ValidationFailure(['invalid generation identity'])
    return Path('generations') / generation_id.removeprefix('sha256:')


def _report_hash(report):
    return sha256_id({k: v for k, v in report.items() if k != 'reportHash'})


def _read_report(root, generation_id):
    report = load_data(_contained(root, generation_relative(generation_id) / 'build-report.yaml'))
    import jsonschema
    schema = load_data(Path(__file__).resolve().parents[2] / 'schemas' / 'build-report.schema.json')
    errors = list(jsonschema.Draft202012Validator(schema, format_checker=format_checker()).iter_errors(report))
    if errors:
        raise ValidationFailure(['invalid generation report: ' + errors[0].message])
    if report['reportHash'] != _report_hash(report):
        raise ValidationFailure(['generation reportHash mismatch'])
    expected = generation_identity(report['manifestContentHash'], report['planHash'],
                                   report['compilerId'], report['compilerVersion'])
    if report['generationId'] != generation_id or expected != generation_id:
        raise ValidationFailure(['generation binding mismatch'])
    ids = [identity_key(t['targetId']) for t in report['targets']]
    if len(ids) != len(set(ids)):
        raise ValidationFailure(['duplicate generation target'])
    return report


def load_generation_artifact(root, generation_id, target_id):
    """Never consult a latest pointer, another generation, or a legacy flat file."""
    try:
        report = _read_report(root, generation_id)
        key = identity_key(target_id)
        matches = [t for t in report['targets'] if identity_key(t['targetId']) == key]
        if len(matches) != 1:
            raise ValidationFailure(['target is absent from requested generation'])
        target = matches[0]
        if target['status'] == 'failed':
            if target['artifactRef'] is not None or target['artifactHash'] is not None:
                raise ValidationFailure(['failed generation target claims an artifact'])
            return None
        relative = generation_relative(generation_id) / (target_filename(target_id) + '.context.json')
        if target['artifactRef'] != relative.as_posix():
            raise ValidationFailure(['generation artifactRef is not the safe target mapping'])
        artifact = load_data(_contained(root, relative))
        from .runtime import _governed_artefact_errors
        violations = _governed_artefact_errors(artifact)
        if violations:
            raise ValidationFailure(violations)
        if artifact.get('artifactHash') != target['artifactHash'] or artefact_hash(artifact) != target['artifactHash']:
            raise ValidationFailure(['generation artifactHash mismatch'])
        if (identity_key(artifact['targetId']) != key
            or artifact['manifest']['contentHash'] != report['manifestContentHash']
            or identity_key(artifact['manifest']['id']) != identity_key(report['manifestId'])
            or artifact['manifest']['version'] != report['manifestVersion']
            or artifact['build']['planHash'] != report['planHash']
            or artifact['build']['compilerId'] != report['compilerId']
            or artifact['build']['compilerVersion'] != report['compilerVersion']):
            raise ValidationFailure(['artifact does not belong to requested generation'])
        return artifact
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise ValidationFailure(['cannot load requested generation: ' + str(exc)]) from exc


def publish_generation(root, report, artifacts, render_markdown):
    """Publish a complete directory with one rename; never overwrite a generation."""
    root = Path(root)
    if root.is_symlink():
        raise ValidationFailure(["output root must not be a symlink"])
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve()
    relative = generation_relative(report['generationId'])
    parent = _contained(root, 'generations')
    parent.mkdir(exist_ok=True)
    destination = _contained(root, relative)
    report['reportHash'] = _report_hash(report)
    staging = Path(tempfile.mkdtemp(prefix='.staging-', dir=parent))
    try:
        for target_id, artifact in artifacts.items():
            name = target_filename(target_id)
            save_json(staging / (name + '.context.json'), artifact)
            (staging / (name + '.context.md')).write_text(render_markdown(artifact), encoding='utf-8')
        save_yaml(staging / 'build-report.yaml', report)
        # Recheck immediately before publication; no existing symlink is followed.
        destination = _contained(root, relative)
        if not destination.exists():
            try:
                os.rename(staging, destination)
            except OSError:
                if not destination.is_dir():
                    raise
        existing = _read_report(root, report['generationId'])
        if canonical_json_bytes({k:v for k,v in existing.items() if k not in {'builtAt','reportHash'}}) != canonical_json_bytes({k:v for k,v in report.items() if k not in {'builtAt','reportHash'}}):
            raise ValidationFailure(['immutable generation has different results'])
        for target_id, artifact in artifacts.items():
            if canonical_json_bytes(load_generation_artifact(root, report['generationId'], target_id)) != canonical_json_bytes(artifact):
                raise ValidationFailure(['immutable generation has different artifact bytes'])
        # Convenience report only. Runtime generation loading never reads this.
        latest = _contained(root, 'build-report.yaml')
        fd, tmp = tempfile.mkstemp(prefix='.report-', dir=root)
        os.close(fd)
        try:
            save_yaml(tmp, existing)
            _contained(root, 'build-report.yaml')
            os.replace(tmp, latest)
        finally:
            Path(tmp).unlink(missing_ok=True)
        return existing
    finally:
        if staging.exists():
            shutil.rmtree(staging)
