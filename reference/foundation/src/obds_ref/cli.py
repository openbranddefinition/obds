from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from .canonical import artefact_hash, sha256_id
from .checks import CompiledCheckContractError, UnicodeAdmissibilityError, execute_checks
from .runtime import (
    COMPILED_CONTEXT_SCHEMA_VERSION,
    _governed_artefact_errors,
    run_with_model,
)
from .compiler import (
    ValidationFailure,
    build_all,
    load_data,
    validate_manifest,
    validate_plan,
    manifest_change_report,
)


def _load_conformance_fixture(path):
    """Section 28.1: the conformance runner reads under the governed contract.

    A canonical fixture decides a published conformance result, so a reader
    that is more permissive than the specification can pass a case the
    specification fails. It also never met the section 28.1 bound, so a deep
    document crashed the runner with a RecursionError instead of failing the
    case, which is the one failure mode a conformance runner must not have.
    """
    return load_data(path)


def _parser_isolation_case(base):
    """Import every shipped module in a fresh interpreter; PyYAML must not move.

    The 2.0.0 release derived a loader as a bare subclass and item-assigned into
    the inherited resolver table, so importing one view builder changed what
    `yaml.safe_load` meant for every consumer in the process — and what the
    governed *writer* emitted, which made `load_data` refuse its own output.
    """
    import subprocess, sys, textwrap

    root = Path(base).resolve()
    package_root = root.parents[1]
    script = textwrap.dedent(
        f"""
        import sys, json, importlib.util
        from pathlib import Path
        sys.path.insert(0, {str(root / "src")!r})
        import yaml

        def snapshot():
            return json.dumps({{
                "resolver": sorted((ch or "", [t for t, _ in items])
                                   for ch, items in yaml.resolver.Resolver.yaml_implicit_resolvers.items()),
                "safe": sorted((ch or "", [t for t, _ in items])
                               for ch, items in yaml.SafeLoader.yaml_implicit_resolvers.items()),
                "probe": repr(yaml.safe_load("a: true")) + repr(yaml.safe_load("a: 1e3")),
                "dump": yaml.safe_dump({{"b": "true", "c": "1e3"}}, sort_keys=True),
            }}, sort_keys=True)

        before = snapshot()
        import obds_ref.governed_io, obds_ref.canonical, obds_ref.compiler
        import obds_ref.checks, obds_ref.runtime, obds_ref.model_input, obds_ref.cli
        for directory in ["context-assembly", "context-delivery", "design-space"]:
            path = Path({str(package_root)!r}) / directory
            if not path.is_dir():
                continue
            sys.path.insert(0, str(path))
            for name in ("canonical", "governed_io", "model_input", "build_views",
                         "assemble_context", "design_space_ref"):
                target = path / (name + ".py")
                if not target.is_file():
                    continue
                spec = importlib.util.spec_from_file_location(directory.replace("-", "_") + "_" + name, target)
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
        print("SAME" if snapshot() == before else "CHANGED")
        """
    )
    completed = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    unchanged = completed.returncode == 0 and completed.stdout.startswith("SAME")
    return unchanged, {"parserTablesUnchanged": unchanged, "stderr": completed.stderr[-400:]}


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _compiled_context_errors(document) -> list[str]:
    """Section 14: the CLI is a Compiled Brand Context executor like any other.

    It validated by `artifactHash` alone and then read fields, so a correctly
    re-sealed artefact carrying a property the published contract forbids was
    reported valid — and `compiledChecks` was read with `.get(..., [])`, which
    turns a missing required property into "this artefact enforces nothing", the
    exact default the runtime refuses to invent.

    The order is the contract's: governed parse, then schema, then integrity,
    then fields. The hash is asked second because a payload that is not a
    Compiled Brand Context has nothing worth sealing.
    """
    violations = _governed_artefact_errors(document)
    if violations:
        return violations
    if document.get("artifactHash") != artefact_hash(document):
        return ["artifactHash mismatch"]
    return []


def command_validate(args: argparse.Namespace) -> int:
    data = load_data(args.file)
    if not isinstance(data, dict):
        _print_json({"valid": False, "errors": ["unsupported document kind"]})
        return 1
    if data.get("kind") == "brand-manifest":
        errors = validate_manifest(data)
    elif data.get("kind") == "obds-build-plan":
        errors = validate_plan(data)
    elif data.get("kind") == "obds-compiled-brand-context":
        errors = _compiled_context_errors(data)
    else:
        errors = ["unsupported document kind"]

    _print_json({"valid": not errors, "errors": errors})
    return 0 if not errors else 1


def command_build(args: argparse.Namespace) -> int:
    manifest = load_data(args.manifest)
    plan = load_data(args.plan)
    try:
        report = build_all(manifest, plan, output_dir=args.out)
    except ValidationFailure as error:
        _print_json({"valid": False, "errors": error.errors})
        return 1

    _print_json(report)
    return 0 if all(item["status"] == "ready" for item in report["targets"]) else 2


def command_check(args: argparse.Namespace) -> int:
    artefact = load_data(args.artifact)
    errors = _compiled_context_errors(artefact)
    if errors:
        _print_json({"valid": False, "errors": errors})
        return 1

    text = Path(args.text_file).read_text(encoding="utf-8") if args.text_file else args.text
    # The contract has been executed, so the property is there to index. An
    # unmaterialised check or inadmissible text is a governed refusal here too,
    # not a traceback out of the command.
    try:
        findings = execute_checks(artefact["compiledChecks"], phase=args.phase, text=text or "")
    except (CompiledCheckContractError, UnicodeAdmissibilityError) as exc:
        _print_json({"valid": False, "errors": [str(exc)]})
        return 1
    payload = [
        {
            "ruleElementId": item.rule_element_id,
            "primitive": item.primitive,
            "phase": item.phase,
            "enforcement": item.enforcement,
            "passed": item.passed,
            "message": item.message,
        }
        for item in findings
    ]
    _print_json(payload)
    return 0 if all(item["passed"] or item["enforcement"] != "block" for item in payload) else 3


def command_test(args: argparse.Namespace) -> int:
    suite = load_data(args.suite)
    base = Path(args.suite).resolve().parent
    results = []
    all_passed = True

    for case in suite.get("cases", []):
        manifest = load_data(base / case["manifest"])
        plan = load_data(base / case["plan"])
        report = build_all(manifest, plan)
        actual = {item["targetId"]: item["status"] for item in report["targets"]}
        passed = actual == case["expectedTargets"]
        all_passed = all_passed and passed
        results.append({
            "id": case["id"],
            "passed": passed,
            "expectedTargets": case["expectedTargets"],
            "actualTargets": actual,
        })

    _print_json({"passed": all_passed, "cases": results})
    return 0 if all_passed else 4



def command_diff(args):
    old,new=load_data(args.old),load_data(args.new)
    errors=validate_manifest(old,verify_hash=False)+validate_manifest(new,verify_hash=False)
    if errors: _print_json({"valid":False,"errors":errors}); return 1
    report=manifest_change_report(old,new)
    if args.out: Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    _print_json(report); return 0

def _validate_document(data):
    # The official conformance runner's `validate` case type. It answered the
    # same question as `command_validate` with a weaker rule, so a re-sealed
    # schema-invalid artefact passed a declared conformance case.
    if not isinstance(data, dict): return ["unsupported document kind"]
    if data.get("kind")=="brand-manifest": return validate_manifest(data,verify_hash=False)
    if data.get("kind")=="obds-build-plan": return validate_plan(data)
    if data.get("kind")=="obds-compiled-brand-context": return _compiled_context_errors(data)
    return ["unsupported document kind"]

def command_conformance(args):
    suite=load_data(args.suite); base=Path(args.suite).resolve().parent; results=[]
    for case in suite.get("cases",[]):
        typ=case.get("type"); passed=False; details={}
        if typ=="build":
            manifest,plan=load_data(base/case["manifest"]),load_data(base/case["plan"])
            try:
                report=build_all(manifest,plan); actual={x["targetId"]:x["status"] for x in report["targets"]}; passed=actual==case.get("expectedTargets"); details={"actualTargets":actual}
            except ValidationFailure as err:
                passed=case.get("expectedValidationFailure") is True; details={"errors":err.errors}
        elif typ=="validate":
            errors=_validate_document(load_data(base/case["document"])); passed=((not errors)==case["expectedValid"])
            if case.get("errorContains"): passed=passed and any(case["errorContains"] in x for x in errors)
            details={"errors":errors}
        elif typ=="diff":
            old,new=load_data(base/case["old"]),load_data(base/case["new"]); a,b=manifest_change_report(old,new),manifest_change_report(old,new); counts={k:len(a[k]) for k in ("added","changed","removed")}; passed=a==b and counts==case["expectedCounts"]; details={"counts":counts,"reportHash":sha256_id(a)}
        elif typ=="runtime":
            artefact=load_data(base/case["artifact"]) if case.get("artifact") else None; calls=[]
            def model(prompt): calls.append(prompt); return case.get("modelOutput",""),"conformance-request-1"
            record=run_with_model(artefact,task_input=case.get("taskInput",""),model=model,target_id=case.get("targetId"),provider="conformance-adapter",model_id="instrumented-model"); passed=record["decision"]==case["expectedDecision"] and len(calls)==case["expectedModelCalls"]; details={"decision":record["decision"],"modelCalls":len(calls)}
        elif typ=="governed-input":
            # Section 26 / 28.1, added in 3.0.0. Until then the official suite
            # had no governed-input case at all, so an implementation could pass
            # every case while violating every section 28.1 MUST — which is
            # exactly what the 2.0.0 release did.
            try:
                load_data(base/case["document"]); errors=[]
            except ValidationFailure as err:
                errors=err.errors
            passed=((not errors)==case["expectedGovernable"])
            if case.get("errorContains"): passed=passed and any(case["errorContains"] in x for x in errors)
            details={"errors":errors}
        elif typ=="parser-isolation":
            # No module changes another module's parser. A process-level property,
            # so it is executed in a fresh interpreter.
            passed,details=_parser_isolation_case(base)
        elif typ=="canonical":
            fixture=_load_conformance_fixture(base/case["document"]); from .canonical import manifest_content_hash; m=fixture["manifest"]["expectedContentHash"]==manifest_content_hash(fixture["manifest"]["input"]); a=fixture["artefact"]["expectedArtifactHash"]==artefact_hash(fixture["artefact"]["input"]); passed=m and a; details={"manifestHash":m,"artifactHash":a}
        results.append({"id":case["id"],"type":typ,"passed":passed,**details})
    pc=sum(1 for x in results if x["passed"]); fc=len(results)-pc
    from datetime import datetime,timezone
    payload={"kind":"obds-conformance-result","schemaVersion":"1.0.0","profile":suite.get("profile","foundation"),"implementation":{"name":"obds-reference","version":"1.0.0"},"suiteHash":sha256_id(suite),"executedAt":datetime.now(timezone.utc).isoformat(),"passed":fc==0,"passedCount":pc,"failedCount":fc,"cases":results}
    if args.out: Path(args.out).write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    _print_json(payload); return 0 if fc==0 else 5

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="obds")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("file")
    validate.set_defaults(handler=command_validate)

    build = subparsers.add_parser("build")
    build.add_argument("manifest")
    build.add_argument("plan")
    build.add_argument("--out", required=True)
    build.set_defaults(handler=command_build)

    check = subparsers.add_parser("check")
    check.add_argument("artifact")
    check.add_argument("--phase", choices=["preflight", "postflight"], required=True)
    source = check.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--text-file")
    check.set_defaults(handler=command_check)

    test = subparsers.add_parser("test")
    test.add_argument("suite")
    test.set_defaults(handler=command_test)

    diff = subparsers.add_parser("diff")
    diff.add_argument("old")
    diff.add_argument("new")
    diff.add_argument("--out")
    diff.set_defaults(handler=command_diff)

    conformance = subparsers.add_parser("conformance")
    conformance.add_argument("suite")
    conformance.add_argument("--out")
    conformance.set_defaults(handler=command_conformance)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = args.handler(args)
    except ValidationFailure as error:
        _print_json({"valid": False, "errors": error.errors})
        code = 1
    sys.exit(code)


if __name__ == "__main__":
    main()
