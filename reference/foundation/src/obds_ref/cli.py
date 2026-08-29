from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from .canonical import artefact_hash, sha256_id
from .checks import execute_checks
from .runtime import run_with_model
from .compiler import (
    ValidationFailure,
    build_all,
    load_data,
    validate_manifest,
    validate_plan,
    manifest_change_report,
)


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def command_validate(args: argparse.Namespace) -> int:
    data = load_data(args.file)
    if data.get("kind") == "brand-manifest":
        errors = validate_manifest(data)
    elif data.get("kind") == "obds-build-plan":
        errors = validate_plan(data)
    elif data.get("kind") == "obds-compiled-brand-context":
        errors = [] if data.get("artifactHash") == artefact_hash(data) else ["artifactHash mismatch"]
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
    if artefact.get("artifactHash") != artefact_hash(artefact):
        _print_json({"valid": False, "errors": ["artifactHash mismatch"]})
        return 1

    text = Path(args.text_file).read_text(encoding="utf-8") if args.text_file else args.text
    findings = execute_checks(artefact.get("compiledChecks", []), phase=args.phase, text=text or "")
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
    if data.get("kind")=="brand-manifest": return validate_manifest(data,verify_hash=False)
    if data.get("kind")=="obds-build-plan": return validate_plan(data)
    if data.get("kind")=="obds-compiled-brand-context": return [] if data.get("artifactHash")==artefact_hash(data) else ["artifactHash mismatch"]
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
        elif typ=="canonical":
            fixture=json.loads((base/case["document"]).read_text(encoding="utf-8")); from .canonical import manifest_content_hash; m=fixture["manifest"]["expectedContentHash"]==manifest_content_hash(fixture["manifest"]["input"]); a=fixture["artefact"]["expectedArtifactHash"]==artefact_hash(fixture["artefact"]["input"]); passed=m and a; details={"manifestHash":m,"artifactHash":a}
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
