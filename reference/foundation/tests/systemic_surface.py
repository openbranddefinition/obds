"""The machine-readable surfaces the systemic closure tests enumerate.

Eleven review rounds produced nineteen reproducible defects, and they had three
shapes, not nineteen causes:

1. a published contract constrains a field and the code does not;
2. a governed hash is copied instead of reproduced;
3. one semantic primitive is implemented twice and the two drift.

Point-fixing an instance of a shape closes that instance. These lists exist so
the *shape* can be closed instead: every systemic test enumerates its surface
from here, and a path that is added without an entry fails the enumeration test
rather than silently escaping coverage.

Nothing in this module is a test. It is the registry the tests read.
"""

from __future__ import annotations

from pathlib import Path

TESTS = Path(__file__).resolve().parent
FOUNDATION = TESTS.parent
REFERENCE = FOUNDATION.parent
PACKAGE_ROOT = REFERENCE.parent


# --------------------------------------------------------------------------
# Surface 1 — the published 3.0 contracts, and what executes each of them.
#
# Mechanism 1 drives every one of these: for each contract, every leaf the
# contract constrains must be constrained by the code as well, in both
# directions. A contract published without an executor here fails
# `test_every_published_3_0_contract_has_an_executor`.
# --------------------------------------------------------------------------

PUBLISHED_3_0_CONTRACTS = {
    "schemas/3.0.0/build-plan.schema.json": "build-plan",
    "schemas/3.0.0/compiled-context.schema.json": "compiled-context",
    "schemas/4.0.0/runtime-decision-record.schema.json": "runtime-decision-record",
    "value-schemas/3.0.0/rule.schema.json": "rule-value",
}


# --------------------------------------------------------------------------
# Surface 2 — every place a governed hash is verified.
#
# Mechanism 2 drives each: a valid payload with its correct hash passes; a
# mutated payload with the old hash fails; and a mutated payload whose own hash
# the caller recomputed still fails, because the binding one level up is broken.
# `where` names the function, `binds` names what the hash is a claim about.
# --------------------------------------------------------------------------

# Mechanism 2 enumerated hash *field names* found in the corpus. That is one
# name for many call sites: `package.modelInputHash` was registered once, driven
# once through the runtime, and every other function in the release comparing
# that field counted as covered. `validate_review` compared it between two
# supplied claims and reproduced neither, and the registry said the field was
# checked.
#
# So the unit is the call site, not the name. Two functions using
# `modelInputHash` are two verification responsibilities and need two proofs.
#
# Roles, and what each one claims:
#
#   PRODUCER          computes a hash and writes it into a document it produces
#   VERIFIER          reproduces the hash from the payload before governed use
#   COMPARISON_ONLY   compares values already verified elsewhere; names where
#   INTERNAL          a helper behind a gate that is itself registered
#   NON_GOVERNED      a hash use that gates no governed decision
#   RELEASE_BOOKKEEPING
#                     reproduces a published release metadata value against the
#                     artefact it describes. It gates the release, not a governed
#                     decision in Classes A-E, and it lives inside the gate's
#                     `main`, which cannot be driven per site in a test that runs
#                     in under a minute. Stated as its own role rather than
#                     dressed as a comparison after an unrelated boundary, which
#                     is what it was and what a reviewer correctly rejected.
#
# Every VERIFIER has a driver in `test_obds_300_systemic_hashes.py` proving that
# a mutated payload fails at that specific boundary. Every COMPARISON_ONLY names
# the prior verified boundary that makes comparing safe; a comment is not a
# proof, so the test requires the named boundary to exist and to be a VERIFIER.
PRODUCER = "producer"
VERIFIER = "verifier"
COMPARISON_ONLY = "comparison-only"
INTERNAL = "internal"
NON_GOVERNED = "non-governed"
RELEASE_BOOKKEEPING = "release-bookkeeping"

# The field names discovery looks for, and the primitives that produce a hash.
# A function that mentions neither is not a hash call site.
GOVERNED_HASH_FIELDS = (
    "artifactHash", "modelInputHash", "assemblyHash", "reviewHash", "contentHash",
    "compiledContextHash", "planHash", "schemaHash", "shapeHash", "cardHash",
    "chapterHash", "indexHash", "chapterSetHash", "searchIndexHash",
    "governedResultHash", "taskInputHash", "suiteHash", "testOutputHash", "generationId", "reportHash",
    "packageZipSha256", "websiteIndexSha256",
)

HASH_PRODUCING_CALLS = (
    "sha256_id(", "artefact_hash(", "artifact_hash(", "manifest_content_hash(",
    "text_hash(", "value_shape_hash(", "hashlib.sha256", "sha256_file(",
    # A local wrapper is still a hash producer. `tools/build-release.py` computes
    # every packaged file's digest through its own `sha256(...)` and the token
    # set could not see it, so the function that writes PACKAGE-MANIFEST.json was
    # outside the surface entirely.
    "sha256(",
)

# Keyed `path::function::field`, or `path::function::*` for a function that
# produces or reproduces a hash without naming a governed field.
HASH_CALL_SITES = {
    "reference/foundation/src/obds_ref/canonical.py::sha256_id::*": {
        "role": PRODUCER,
        "note": "the canonical SHA-256 primitive itself",
    },
    "reference/foundation/src/obds_ref/canonical.py::manifest_content_hash::*": {
        "role": PRODUCER,
        "note": "the manifest content-hash primitive itself",
    },
    "reference/foundation/src/obds_ref/canonical.py::artefact_hash::artifactHash": {
        "role": PRODUCER,
        "note": "the artefact seal primitive itself",
    },
    "reference/foundation/src/obds_ref/canonical.py::text_hash::*": {
        "role": PRODUCER,
        "note": "the governed text-hash primitive itself",
    },
    "reference/foundation/src/obds_ref/canonical.py::value_shape_hash::*": {
        "role": PRODUCER,
        "note": "the value-shape primitive itself",
    },
    "reference/context-assembly/canonical.py::sha256_id::*": {
        "role": PRODUCER,
        "note": "the canonical SHA-256 primitive itself",
    },
    "reference/context-assembly/canonical.py::manifest_content_hash::*": {
        "role": PRODUCER,
        "note": "the manifest content-hash primitive itself",
    },
    "reference/context-assembly/canonical.py::artefact_hash::artifactHash": {
        "role": PRODUCER,
        "note": "the artefact seal primitive itself",
    },
    "reference/context-assembly/canonical.py::text_hash::*": {
        "role": PRODUCER,
        "note": "the governed text-hash primitive itself",
    },
    "reference/context-assembly/canonical.py::value_shape_hash::*": {
        "role": PRODUCER,
        "note": "the value-shape primitive itself",
    },
    "reference/context-delivery/canonical.py::sha256_id::*": {
        "role": PRODUCER,
        "note": "the canonical SHA-256 primitive itself",
    },
    "reference/context-delivery/canonical.py::manifest_content_hash::*": {
        "role": PRODUCER,
        "note": "the manifest content-hash primitive itself",
    },
    "reference/context-delivery/canonical.py::artefact_hash::artifactHash": {
        "role": PRODUCER,
        "note": "the artefact seal primitive itself",
    },
    "reference/context-delivery/canonical.py::text_hash::*": {
        "role": PRODUCER,
        "note": "the governed text-hash primitive itself",
    },
    "reference/context-delivery/canonical.py::value_shape_hash::*": {
        "role": PRODUCER,
        "note": "the value-shape primitive itself",
    },
    "reference/design-space/canonical.py::sha256_id::*": {
        "role": PRODUCER,
        "note": "the canonical SHA-256 primitive itself",
    },
    "reference/design-space/canonical.py::manifest_content_hash::*": {
        "role": PRODUCER,
        "note": "the manifest content-hash primitive itself",
    },
    "reference/design-space/canonical.py::artefact_hash::artifactHash": {
        "role": PRODUCER,
        "note": "the artefact seal primitive itself",
    },
    "reference/design-space/canonical.py::text_hash::*": {
        "role": PRODUCER,
        "note": "the governed text-hash primitive itself",
    },
    "reference/design-space/canonical.py::value_shape_hash::*": {
        "role": PRODUCER,
        "note": "the value-shape primitive itself",
    },
    "reference/context-assembly/assemble_context.py::artifact_hash::artifactHash": {
        "role": PRODUCER,
        "note": "the flat package's copy of the artefact seal primitive",
    },
    "reference/context-assembly/assemble_context.py::_validate_compiled_context::artifactHash": {
        "gate": 'if compiled_context.get("artifactHash") != artifact_hash(compiled_context):',
        "neutralised": 'if False and compiled_context.get("artifactHash") != artifact_hash(compiled_context):',
        "role": VERIFIER,
        "note": "the compiled artefact's seal, before the assembler reads a field of it",
        "reproduces": "artifact_hash(compiled_context)",
    },
    "reference/context-assembly/assemble_context.py::_validate_resolution_manifest::contentHash": {
        "gate": 'or actual_hash != expected.get("contentHash")',
        "neutralised": 'or (False and actual_hash != expected.get("contentHash"))',
        "role": VERIFIER,
        "note": "the resolution snapshot is the manifest the artefact names",
        "reproduces": "manifest_content_hash(resolution_manifest)",
    },
    "reference/context-assembly/assemble_context.py::_assert_view_integrity::*": {
        "role": INTERNAL,
        "note": "is the reproduction the four assemble() view-hash sites invoke",
    },
    "reference/context-assembly/assemble_context.py::assemble::artifactHash": {
        "role": COMPARISON_ONLY,
        "note": "published into the package's sources",
        "after": "reference/context-assembly/assemble_context.py::_validate_compiled_context::artifactHash",
    },
    "reference/context-assembly/assemble_context.py::assemble::contentHash": {
        "role": COMPARISON_ONLY,
        "note": "the derived views must name the manifest the verified artefact names",
        "after": "reference/context-assembly/assemble_context.py::_validate_compiled_context::artifactHash",
    },
    "reference/context-assembly/assemble_context.py::assemble::cardHash": {
        "gate": '_assert_view_integrity(search_index, "indexHash", "cards", "cardHash", "Search Card")',
        "neutralised": 'None and _assert_view_integrity(search_index, "indexHash", "cards", "cardHash", "Search Card")',
        "role": VERIFIER,
        "note": "a derived view's own hash, reproduced before its content is rendered",
        "reproduces": "sha256_id over the view payload, via _assert_view_integrity",
    },
    "reference/context-assembly/assemble_context.py::assemble::chapterHash": {
        "gate": '_assert_view_integrity(chapter_set, "chapterSetHash", "chapters", "chapterHash", "Reasoning Chapter")',
        "neutralised": 'None and _assert_view_integrity(chapter_set, "chapterSetHash", "chapters", "chapterHash", "Reasoning Chapter")',
        "role": VERIFIER,
        "note": "a derived view's own hash, reproduced before its content is rendered",
        "reproduces": "sha256_id over the view payload, via _assert_view_integrity",
    },
    "reference/context-assembly/assemble_context.py::assemble::indexHash": {
        "gate": '_assert_view_integrity(search_index, "indexHash", "cards", "cardHash", "Search Card")',
        "neutralised": 'None and _assert_view_integrity(search_index, "indexHash", "cards", "cardHash", "Search Card")',
        "role": VERIFIER,
        "note": "a derived view's own hash, reproduced before its content is rendered",
        "reproduces": "sha256_id over the view payload, via _assert_view_integrity",
    },
    "reference/context-assembly/assemble_context.py::assemble::chapterSetHash": {
        "gate": '_assert_view_integrity(chapter_set, "chapterSetHash", "chapters", "chapterHash", "Reasoning Chapter")',
        "neutralised": 'None and _assert_view_integrity(chapter_set, "chapterSetHash", "chapters", "chapterHash", "Reasoning Chapter")',
        "role": VERIFIER,
        "note": "a derived view's own hash, reproduced before its content is rendered",
        "reproduces": "sha256_id over the view payload, via _assert_view_integrity",
    },
    "reference/context-assembly/assemble_context.py::assemble::compiledContextHash": {
        "role": PRODUCER,
        "note": "written into the Model Input Package this call produces",
    },
    "reference/context-assembly/assemble_context.py::assemble::modelInputHash": {
        "role": PRODUCER,
        "note": "written into the Model Input Package this call produces",
    },
    "reference/context-assembly/assemble_context.py::assemble::assemblyHash": {
        "role": PRODUCER,
        "note": "written into the Model Input Package this call produces",
    },
    "reference/context-assembly/assemble_context.py::assemble::searchIndexHash": {
        "role": PRODUCER,
        "note": "written into the Model Input Package this call produces",
    },
    "reference/context-assembly/build_views.py::manifest_hash::*": {
        "role": INTERNAL,
        "note": "is the reproduction build_views() invokes",
    },
    "reference/context-assembly/build_views.py::build_views::contentHash": {
        "gate": 'if declared_approval is not None and declared_approval != manifest_content_hash(manifest):',
        "neutralised": 'if False and declared_approval is not None and declared_approval != manifest_content_hash(manifest):',
        "role": VERIFIER,
        "note": "the manifest a derived view claims is the manifest it was built from",
        "reproduces": "manifest_content_hash(manifest)",
    },
    "reference/context-assembly/build_views.py::build_views::cardHash": {
        "role": PRODUCER,
        "note": "written into the derived view this call produces",
    },
    "reference/context-assembly/build_views.py::build_views::chapterHash": {
        "role": PRODUCER,
        "note": "written into the derived view this call produces",
    },
    "reference/context-assembly/build_views.py::build_views::chapterSetHash": {
        "role": PRODUCER,
        "note": "written into the derived view this call produces",
    },
    "reference/context-assembly/build_views.py::build_views::indexHash": {
        "role": PRODUCER,
        "note": "written into the derived view this call produces",
    },
    "reference/context-delivery/build_views.py::manifest_hash::*": {
        "role": INTERNAL,
        "note": "is the reproduction build_views() invokes",
    },
    "reference/context-delivery/build_views.py::build_views::contentHash": {
        "gate": 'if declared_approval is not None and declared_approval != manifest_content_hash(manifest):',
        "neutralised": 'if False and declared_approval is not None and declared_approval != manifest_content_hash(manifest):',
        "role": VERIFIER,
        "note": "the manifest a derived view claims is the manifest it was built from",
        "reproduces": "manifest_content_hash(manifest)",
    },
    "reference/context-delivery/build_views.py::build_views::cardHash": {
        "role": PRODUCER,
        "note": "written into the derived view this call produces",
    },
    "reference/context-delivery/build_views.py::build_views::chapterHash": {
        "role": PRODUCER,
        "note": "written into the derived view this call produces",
    },
    "reference/context-delivery/build_views.py::build_views::chapterSetHash": {
        "role": PRODUCER,
        "note": "written into the derived view this call produces",
    },
    "reference/context-delivery/build_views.py::build_views::indexHash": {
        "role": PRODUCER,
        "note": "written into the derived view this call produces",
    },
    "reference/context-assembly/validate_review.py::validate_review::contentHash": {
        "role": COMPARISON_ONLY,
        "note": "the package's manifest identity triple against the artefact's",
        "after": "reference/context-assembly/validate_review.py::validate_review::artifactHash",
    },
    "reference/context-assembly/validate_review.py::validate_review::artifactHash": {
        "gate": 'if compiled_context.get("artifactHash") != computed:',
        "neutralised": 'if False and compiled_context.get("artifactHash") != computed:',
        "role": VERIFIER,
        "note": "the compiled artefact's seal, before elementRecords decide anything",
        "reproduces": "artifact_hash(compiled_context)",
    },
    "reference/context-assembly/validate_review.py::validate_review::compiledContextHash": {
        "gate": 'if package["sources"]["compiledContextHash"] != computed:',
        "neutralised": 'if False and package["sources"]["compiledContextHash"] != computed:',
        "role": VERIFIER,
        "note": "the package names the artefact this review was derived from",
        "reproduces": "artifact_hash(compiled_context)",
    },
    "reference/context-assembly/validate_review.py::validate_review::assemblyHash": {
        "gate": 'if package.get("assemblyHash") != sha256_id(package_payload):',
        "neutralised": 'if False and package.get("assemblyHash") != sha256_id(package_payload):',
        "role": VERIFIER,
        "note": "the package's own seal, so selection and slots cannot be edited under it",
        "reproduces": "sha256_id(package without assemblyHash)",
    },
    "reference/context-assembly/validate_review.py::validate_review::modelInputHash": {
        "gate": 'rendered_hash = text_hash(render_model_input(package["slots"]))',
        "neutralised": 'rendered_hash = package.get("modelInputHash")',
        "role": VERIFIER,
        "note": "package and review both name the model input the slots actually render",
        "reproduces": "text_hash(render_model_input(package['slots']))",
    },
    "reference/context-assembly/validate_review.py::validate_review::reviewHash": {
        "gate": 'if review["reviewHash"] != expected_hash:',
        "neutralised": 'if False and review["reviewHash"] != expected_hash:',
        "role": VERIFIER,
        "note": "the review's own seal over the decision and findings",
        "reproduces": "sha256_id(review without reviewHash)",
    },
    "reference/foundation/src/obds_ref/cli.py::_compiled_context_errors::artifactHash": {
        "gate": 'if document.get("artifactHash") != artefact_hash(document):',
        "neutralised": 'if False and document.get("artifactHash") != artefact_hash(document):',
        "role": VERIFIER,
        "note": "the artefact's seal, in the gate both CLI executors call",
        "reproduces": "artefact_hash(document)",
    },
    "reference/foundation/src/obds_ref/cli.py::command_conformance::artifactHash": {
        "gate": 'a=fixture["artefact"]["expectedArtifactHash"]==artefact_hash(fixture["artefact"]["input"])',
        "neutralised": 'a=True',
        "role": VERIFIER,
        "note": "the declared hash conformance case reproduces the seal it publishes",
        "reproduces": "artefact_hash(fixture['artefact']['input'])",
    },
    "reference/foundation/src/obds_ref/cli.py::command_conformance::suiteHash": {
        "role": PRODUCER,
        "note": "written into the conformance result this call produces",
    },
    "reference/foundation/src/obds_ref/compiler.py::_validate_contract_value::schemaHash": {
        "role": COMPARISON_ONLY,
        "note": "reproduces the same value a second time, after validate_manifest has already "
                "reproduced and reported it; it is reached only for contracts that passed there",
        "after": "reference/foundation/src/obds_ref/compiler.py::validate_manifest::schemaHash",
    },
    "reference/foundation/src/obds_ref/compiler.py::_optional_hash::*": {
        "role": INTERNAL,
        "note": "is the reproduction validate_manifest invokes",
    },
    "reference/foundation/src/obds_ref/compiler.py::manifest_change_report::contentHash": {
        "role": NON_GOVERNED,
        "note": "produces a change report between two manifests; it gates no governed decision",
    },
    "reference/foundation/src/obds_ref/compiler.py::manifest_change_report::schemaHash": {
        "role": NON_GOVERNED,
        "note": "produces a change report between two manifests; it gates no governed decision",
    },
    "reference/foundation/src/obds_ref/compiler.py::manifest_change_report::shapeHash": {
        "role": NON_GOVERNED,
        "note": "produces a change report between two manifests; it gates no governed decision",
    },
    "reference/foundation/src/obds_ref/compiler.py::validate_manifest::contentHash": {
        "gate": 'if approval["contentHash"] != expected:',
        "neutralised": 'if False and approval["contentHash"] != expected:',
        "role": VERIFIER,
        "note": "the approved manifest's own seal",
        "reproduces": "manifest_content_hash(manifest)",
    },
    "reference/foundation/src/obds_ref/compiler.py::validate_manifest::schemaHash": {
        "gate": 'if actual_schema_hash != schema_hash:',
        "neutralised": 'if False and actual_schema_hash != schema_hash:',
        "role": VERIFIER,
        "note": "the value schema a contract gates on is the schema on disk",
        "reproduces": "sha256_id over the resolved schema document",
    },
    "reference/foundation/src/obds_ref/compiler.py::validate_manifest::shapeHash": {
        "gate": 'if actual != contract.get("shapeHash"):',
        "neutralised": 'if False and actual != contract.get("shapeHash"):',
        "role": VERIFIER,
        "note": "the element value has the shape its contract declares",
        "reproduces": "value_shape_hash(element['value'])",
    },
    "reference/foundation/src/obds_ref/compiler.py::governed_result_hash::*": {
        "role": PRODUCER,
        "note": "the governed result hash primitive",
    },
    "reference/foundation/src/obds_ref/compiler.py::governed_result_payload::artifactHash": {
        "role": PRODUCER,
        "note": "assembles the payload the governed result hash is taken over",
    },
    "reference/foundation/src/obds_ref/compiler.py::governed_result_payload::contentHash": {
        "role": PRODUCER,
        "note": "assembles the payload the governed result hash is taken over",
    },
    "reference/foundation/src/obds_ref/compiler.py::governed_result_payload::governedResultHash": {
        "role": PRODUCER,
        "note": "assembles the payload the governed result hash is taken over",
    },
    "reference/foundation/src/obds_ref/compiler.py::build_target::contentHash": {
        "gate": 'or manifest_ref.get("contentHash") != expected_manifest_hash',
        "neutralised": 'or (False and manifest_ref.get("contentHash") != expected_manifest_hash)',
        "role": VERIFIER,
        "note": "the plan's manifestRef names the manifest actually being built",
        "reproduces": "manifest_content_hash(manifest)",
    },
    "reference/foundation/src/obds_ref/compiler.py::build_target::artifactHash": {
        "role": PRODUCER,
        "note": "written into the artefact this call produces and seals",
    },
    "reference/foundation/src/obds_ref/compiler.py::build_target::governedResultHash": {
        "role": PRODUCER,
        "note": "written into the artefact this call produces and seals",
    },
    "reference/foundation/src/obds_ref/compiler.py::build_target::planHash": {
        "role": PRODUCER,
        "note": "written into the artefact this call produces and seals",
    },
    "reference/foundation/src/obds_ref/compiler.py::build_all::artifactHash": {
        "role": PRODUCER,
        "note": "copied from an artefact this call just produced into the build report",
    },
    "reference/foundation/src/obds_ref/compiler.py::build_all::planHash": {
        "role": PRODUCER,
        "note": "copied from an artefact this call just produced into the build report",
    },
    "reference/foundation/src/obds_ref/compiler.py::render_markdown::artifactHash": {
        "role": INTERNAL,
        "note": "prints the seal of an artefact build_target produced and sealed; it verifies nothing and gates nothing",
    },
    "reference/foundation/src/obds_ref/runtime.py::_task_input_hash::taskInputHash": {
        "role": PRODUCER,
        "note": "written into the Runtime Decision Record this attempt produces",
    },
    "reference/foundation/src/obds_ref/runtime.py::_assert_artefact_identity::artifactHash": {
        "role": INTERNAL,
        "note": "kind and version, behind the executors' contract gate",
    },
    "reference/foundation/src/obds_ref/runtime.py::_new_record::artifactHash": {
        "role": INTERNAL,
        "note": "copies verified evidence into the Runtime Decision Record; it verifies nothing itself",
    },
    "reference/foundation/src/obds_ref/runtime.py::_new_record::assemblyHash": {
        "role": INTERNAL,
        "note": "copies verified evidence into the Runtime Decision Record; it verifies nothing itself",
    },
    "reference/foundation/src/obds_ref/runtime.py::_new_record::modelInputHash": {
        "role": INTERNAL,
        "note": "copies verified evidence into the Runtime Decision Record; it verifies nothing itself",
    },
    "reference/foundation/src/obds_ref/runtime.py::_new_record::taskInputHash": {
        "role": INTERNAL,
        "note": "copies verified evidence into the Runtime Decision Record; it verifies nothing itself",
    },
    "reference/foundation/src/obds_ref/runtime.py::_context_validator::artifactHash": {
        "role": INTERNAL,
        "note": "is the contract execution, not a hash site",
    },
    "reference/foundation/src/obds_ref/runtime.py::_governed_artefact_errors::artifactHash": {
        "role": INTERNAL,
        "note": "is the contract and identity gate the executors call; the field names appear in the enumerated positions",
    },
    "reference/foundation/src/obds_ref/runtime.py::_governed_artefact_errors::contentHash": {
        "role": INTERNAL,
        "note": "is the contract and identity gate the executors call; the field names appear in the enumerated positions",
    },
    "reference/foundation/src/obds_ref/runtime.py::run_with_model::artifactHash": {
        "gate": 'if artefact.get("artifactHash") != artefact_hash(artefact):',
        "neutralised": 'if False and artefact.get("artifactHash") != artefact_hash(artefact):',
        "role": VERIFIER,
        "note": "the compiled artefact's seal, before any governed decision",
        "reproduces": "artefact_hash(artefact)",
    },
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::artifactHash": {
        "gate": 'if artefact.get("artifactHash") != artefact_hash(artefact):',
        "neutralised": 'if False and artefact.get("artifactHash") != artefact_hash(artefact):',
        "role": VERIFIER,
        "note": "the compiled artefact's seal, on the assembled path too",
        "reproduces": "artefact_hash(artefact)",
    },
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::compiledContextHash": {
        "gate": 'if compiled_hash != artefact.get("artifactHash"):',
        "neutralised": 'if False and compiled_hash != artefact.get("artifactHash"):',
        "role": VERIFIER,
        "note": "the package names the artefact it was assembled from",
        "reproduces": "artefact.get('artifactHash') after that seal was reproduced",
    },
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::modelInputHash": {
        "gate": 'rendered_hash = text_hash(model_input_text)',
        "neutralised": 'rendered_hash = package.get("modelInputHash")',
        "role": VERIFIER,
        "note": "the rendered model input is the one the verified slots produce",
        "reproduces": "text_hash(render_model_input(package['slots']))",
    },
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::assemblyHash": {
        "gate": 'if package.get("assemblyHash") != sha256_id(payload):',
        "neutralised": 'if False and package.get("assemblyHash") != sha256_id(payload):',
        "role": VERIFIER,
        "note": "the package's own seal",
        "reproduces": "sha256_id(package without assemblyHash)",
    },
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::contentHash": {
        "role": COMPARISON_ONLY,
        "note": "the package's manifest identity triple against the artefact's",
        "after": "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::artifactHash",
    },
    "reference/release-gate.py::sha256_file::*": {
        "role": PRODUCER,
        "note": "the gate's file digest primitive",
    },
    "reference/release-gate.py::_canon_fingerprint::*": {
        "role": PRODUCER,
        "note": "the gate's canonicalisation fingerprint primitive",
    },
    "reference/release-gate.py::suite_hash::*": {
        "role": PRODUCER,
        "note": "produces the suite identity; the value is verified against it in the gate's main",
    },
    "reference/release-gate.py::check_governed_contract_copies::*": {
        "gate": 'len(digests) <= 1,',
        "neutralised": 'True,',
        "role": VERIFIER,
        "note": "the byte-identical governed contract copies, recomputed per file",
        "reproduces": "sha256_file over each registered copy",
    },
    "reference/release-gate.py::check_manifest::*": {
        "role": RELEASE_BOOKKEEPING,
        "note": "recomputes every packaged file's digest for the release; it reads "
                "PACKAGE-MANIFEST.json from the gate's own ROOT, so it cannot be driven "
                "per site without rewriting a file in the repository under test",
    },
    "reference/release-gate.py::main::suiteHash": {
        "role": RELEASE_BOOKKEEPING,
        "note": "the gate reproduces this published release value from the artefact it describes",
    },
    "reference/release-gate.py::main::testOutputHash": {
        "role": RELEASE_BOOKKEEPING,
        "note": "the gate reproduces this published release value from the artefact it describes",
    },
    "reference/release-gate.py::main::packageZipSha256": {
        "role": RELEASE_BOOKKEEPING,
        "note": "the gate reproduces this published release value from the artefact it describes",
    },
    "reference/release-gate.py::main::websiteIndexSha256": {
        "role": RELEASE_BOOKKEEPING,
        "note": "the gate reproduces this published release value from the artefact it describes",
    },
    "reference/release-gate.py::main::governedResultHash": {
        "role": RELEASE_BOOKKEEPING,
        "note": "the gate reproduces this published release value from the artefact it describes",
    },
    "tools/build-release.py::write_manifest::*": {
        "role": PRODUCER,
        "note": "writes PACKAGE-MANIFEST.json, whose digests the release gate reproduces",
    },
    "tools/build-release.py::sha256::*": {
        "role": PRODUCER,
        "note": "the build script's file digest primitive",
    },
    "tools/build-release.py::release_notes::suiteHash": {
        "role": NON_GOVERNED,
        "note": "renders release notes text",
    },
    "tools/build-release.py::conformance_profiles::suiteHash": {
        "role": NON_GOVERNED,
        "note": "renders the declared profile list",
    },
    "tools/build-release.py::write_metadata::suiteHash": {
        "role": PRODUCER,
        "note": "writes the release metadata this script generates",
    },
    "tools/build-release.py::write_metadata::testOutputHash": {
        "role": PRODUCER,
        "note": "writes the release metadata this script generates",
    },
    "tools/build-release.py::sync_publication_surface::packageZipSha256": {
        "role": PRODUCER,
        "note": "writes the publication surface this script generates",
    },
    "tools/build-release.py::sync_publication_surface::testOutputHash": {
        "role": PRODUCER,
        "note": "writes the publication surface this script generates",
    },
    "tools/build-release.py::sync_publication_surface::websiteIndexSha256": {
        "role": PRODUCER,
        "note": "writes the publication surface this script generates",
    },
}


# --------------------------------------------------------------------------
# Surface 3 — semantic primitives implemented more than once.
#
# Mechanism 3 executes one normative vector set against every implementation of
# each primitive. `authoritative` names the single shared implementation where
# there is one; `implementations` lists every executable copy that must agree.
# --------------------------------------------------------------------------

SEMANTIC_PRIMITIVE_IMPLEMENTATIONS = {
    "governed-json-reading": {
        "authoritative": "reference/foundation/src/obds_ref/governed_io.py",
        "implementations": [
            "reference/foundation/src/obds_ref/governed_io.py",
            "reference/adversarial/canonical_js.mjs",
        ],
        "note": (
            "Python is authoritative; the JavaScript reader exists so the release can "
            "show two implementations agreeing, which is worth nothing unless they do."
        ),
    },
    "canonicalisation": {
        "authoritative": "reference/foundation/src/obds_ref/canonical.py",
        "implementations": [
            "reference/foundation/src/obds_ref/canonical.py",
            "reference/adversarial/canonical_js.mjs",
        ],
        "note": "Section 14.3, the vector set the release already publishes.",
    },
    "model-input-rendering": {
        "authoritative": "reference/foundation/src/obds_ref/model_input.py",
        "implementations": ["reference/foundation/src/obds_ref/model_input.py"],
        "note": (
            "One implementation by construction: the assembler imports it and the "
            "runtime derives the expected bytes from it, so there is nothing to drift."
        ),
    },
    "word-segmentation": {
        "authoritative": "reference/foundation/fixtures/word-boundary-ci.json",
        "implementations": ["reference/foundation/src/obds_ref/checks.py"],
        "note": (
            "Delegated to a pinned engine, so the fixtures are authoritative rather "
            "than any code: the declared Unicode version is read from the engine and "
            "the fixtures pin the behaviour."
        ),
    },
}

# Modules copied verbatim across packages. One spelling of a shared contract, or
# it is two contracts. The release gate pins these; the systemic test asserts the
# registry and the gate agree about which files those are.
BYTE_IDENTICAL_COPIES = {
    "projection.py": ["reference/foundation/src/obds_ref/projection.py", "reference/context-assembly/projection.py"],
    "governed_io.py": [
        "reference/foundation/src/obds_ref/governed_io.py",
        "reference/context-assembly/governed_io.py",
        "reference/context-delivery/governed_io.py",
        "reference/design-space/governed_io.py",
    ],
    "canonical.py": [
        "reference/foundation/src/obds_ref/canonical.py",
        "reference/context-assembly/canonical.py",
        "reference/context-delivery/canonical.py",
        "reference/design-space/canonical.py",
    ],
    "model_input.py": [
        "reference/foundation/src/obds_ref/model_input.py",
        "reference/context-assembly/model_input.py",
        "reference/context-delivery/model_input.py",
        "reference/design-space/model_input.py",
    ],
    "build_views.py": [
        "reference/context-assembly/build_views.py",
        "reference/context-delivery/build_views.py",
    ],
}


# --------------------------------------------------------------------------
# Surface 4 — every code path that consumes a Compiled Brand Context.
#
# The runtime validated the published contract and the CLI did not, so the same
# re-sealed schema-invalid artefact was refused by one path and reported valid by
# another. Registering `run_with_model` as *the* compiled-context executor is
# what let that happen: the enumeration described one call site, not the surface.
#
# `MARKERS` is the discovery heuristic — what to *look* at. This registry is what
# is *allowed*: every discovered function must be classified, and everything
# classified `executor` is driven against the adversarial artefacts in
# `test_obds_300_systemic_executors.py`. A new consumer added without an entry
# fails the enumeration test rather than escaping coverage.
#
# Discovery covers production and official-conformance modules under reference/
# and tools/. Test modules are excluded by construction: a test is not a governed
# executor, and the executors a test drives are these.
# --------------------------------------------------------------------------

COMPILED_CONTEXT_MARKERS = (
    "compiledChecks",
    "artifactHash",
    "obds-compiled-brand-context",
    "_compiled_checks",
    "_contract_errors",
    "compiled_context_contract_errors",
    # `validate_review` derives a governed review decision from `elementRecords`
    # and was found by `artifactHash` alone — one substring away from not being
    # found at all. The decision-bearing field and the parameter name are markers
    # too, and so is reading an artefact field by this project's own convention.
    "elementRecords",
    "compiled_context",
    "artefact[",
    "artefact.get(",
)

EXECUTOR = "executor"

COMPILED_CONTEXT_CONSUMERS = {
    # Executors. Each must run: governed parse, 3.0 schema, integrity, fields.
    "reference/foundation/src/obds_ref/runtime.py::run_with_model": EXECUTOR,
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model": EXECUTOR,
    "reference/foundation/src/obds_ref/cli.py::command_validate": EXECUTOR,
    "reference/foundation/src/obds_ref/cli.py::command_check": EXECUTOR,
    "reference/foundation/src/obds_ref/cli.py::_validate_document": EXECUTOR,
    "reference/context-assembly/assemble_context.py::_validate_compiled_context": EXECUTOR,
    # Registered late, and wrongly, the first time: the entry said it "never
    # executes the artefact". It reads `elementRecords` and decides from them
    # whether a governed review result is valid, which is executing it.
    "reference/context-assembly/validate_review.py::validate_review": EXECUTOR,

    # Not executors, with the reason each is not one.
    "reference/foundation/src/obds_ref/canonical.py::artefact_hash":
        "computes the seal over a payload; it consumes no contract and decides nothing",
    "reference/context-assembly/canonical.py::artefact_hash":
        "byte-identical copy of the same sealing function",
    "reference/context-delivery/canonical.py::artefact_hash":
        "byte-identical copy of the same sealing function",
    "reference/design-space/canonical.py::artefact_hash":
        "byte-identical copy of the same sealing function",
    "reference/context-assembly/assemble_context.py::artifact_hash":
        "the flat package's copy of the sealing function",
    "reference/context-assembly/assemble_context.py::compiled_context_contract_errors":
        "is the contract execution its executor calls",
    "reference/context-assembly/assemble_context.py::model_input_package_contract_errors":
        "is the Model Input Package contract execution validate_review calls",
    "reference/context-assembly/assemble_context.py::review_result_contract_errors":
        "is the Review Result contract execution validate_review calls",
    "reference/context-assembly/assemble_context.py::assemble":
        "delegates to _validate_compiled_context before reading any field",
    "reference/foundation/src/obds_ref/cli.py::_compiled_context_errors":
        "is the contract execution the CLI executors call",
    "reference/foundation/src/obds_ref/cli.py::command_conformance":
        "dispatches declared cases to the registered executors above",
    "reference/foundation/src/obds_ref/compiler.py::governed_result_payload":
        "produces a governed result payload; the marker it matches is in a comment",
    "reference/foundation/src/obds_ref/compiler.py::validate_manifest":
        "executes the manifest contract, a different contract; the marker is in a comment",
    "reference/foundation/src/obds_ref/compiler.py::build_target":
        "produces a compiled context and seals it",
    "reference/foundation/src/obds_ref/compiler.py::build_all":
        "produces compiled contexts and seals them",
    "reference/foundation/src/obds_ref/compiler.py::render_markdown":
        "renders a produced artefact for publication",
    "reference/context-assembly/assemble_context.py::_validate_resolution_manifest":
        "internal to assemble(), reached only after _validate_compiled_context",
    "reference/foundation/src/obds_ref/runtime.py::_artifact_valid_at":
        "internal to the runtime executors, after their contract gate",
    "reference/foundation/src/obds_ref/runtime.py::_requested_target_is_bound":
        "internal to the runtime executors, after their contract gate; binds the "
        "requested targetId to the artefact's own and decides nothing else",
    "reference/foundation/src/obds_ref/runtime.py::_assert_artefact_identity":
        "internal to the runtime executors, after their contract gate",
    "reference/foundation/src/obds_ref/runtime.py::_compiled_checks":
        "internal to the runtime executors, after their contract gate",
    "reference/foundation/src/obds_ref/runtime.py::_execute_governed_checks":
        "internal to the runtime executors, after their contract gate",
    "reference/foundation/src/obds_ref/runtime.py::_new_record":
        "builds the Runtime Decision Record; it reads no artefact field that is not type-guarded",
    "reference/foundation/src/obds_ref/runtime.py::_context_validator":
        "is the contract execution the runtime executors call",
    "reference/foundation/src/obds_ref/runtime.py::_contract_errors":
        "is the contract execution the runtime executors call",
    "reference/foundation/src/obds_ref/runtime.py::_governed_artefact_errors":
        "is the gate itself: the published contract plus section 8.0a identity admissibility",
    "reference/foundation/src/obds_ref/compiler.py::_conflict_is_decision_relevant":
        "decides section 10.2a relevance from manifest elements and the build target, "
        "before any compiled context exists; the marker it matches is in a comment",
    "reference/foundation/src/obds_ref/compiler.py::_manifest_identity_positions":
        "enumerates identity positions in a manifest; it reads no compiled context and decides nothing",
    "reference/foundation/src/obds_ref/canonical.py::compiled_context_identity_positions":
        "enumerates identity positions; it reads no value and decides nothing",
    "reference/context-assembly/canonical.py::compiled_context_identity_positions":
        "byte-identical copy of the same enumeration",
    "reference/context-delivery/canonical.py::compiled_context_identity_positions":
        "byte-identical copy of the same enumeration",
    "reference/design-space/canonical.py::compiled_context_identity_positions":
        "byte-identical copy of the same enumeration",
}


# --------------------------------------------------------------------------
# Surface 5 — every consumer of the contract/version inventory.
#
# `contract_directories()` replaced two hand-kept lists of contract directories.
# There was a third, in `manifest_path()`, and it resolved every `schemas/3.0.0/`
# entry under the frozen 1.0.0 directory. One discovered surface means every
# consumer derives from it; the exceptions are the deliberate historical pins,
# which are named here rather than found by reading the code and guessing.
# --------------------------------------------------------------------------

CONTRACT_VERSION_MARKERS = (
    "contract_directories",
    "SCHEMAS_DIR",
    "VALUE_SCHEMAS_DIR",
    "schema_dirs",
)

CONTRACT_VERSION_CONSUMERS = {
    "reference/release-gate.py::contract_directories":
        "derived: the single discovered contract surface",
    "reference/release-gate.py::package_paths":
        "derived: enumerates contract_directories()",
    "reference/release-gate.py::manifest_path":
        "derived: resolves archive paths from contract_directories()",
    "reference/release-gate.py::main":
        "frozen-surface checks: the 1.0.0 count and the 1.1.0 file set are deliberate "
        "historical pins, and the served-contract inventory it builds is derived",
    "tools/build-release.py::schema_dirs":
        "derived: imports contract_directories() from the gate",
    "tools/build-release.py::package_files":
        "derived: packages exactly what schema_dirs() reports",
}

# The files discovery reads for surface 5. Release tooling only: the reference
# implementation resolves contracts by the version a document declares, not by a
# packaging inventory.
CONTRACT_VERSION_MODULES = (
    "reference/release-gate.py",
    "tools/build-release.py",
    "tools/docs-smoke-test.py",
)

# Deliberate historical pins. These name a frozen version on purpose: the point
# of a frozen surface is that it does not move when a new one is discovered.
FROZEN_CONTRACT_PINS = (
    "EXPECTED_PUBLIC_SCHEMAS",
    "EXPECTED_PUBLIC_VALUE_SCHEMAS",
    "EXPECTED_V11_SCHEMAS",
)

# 4.0 F1/F2: generation production and the two independent verified boundaries.
HASH_CALL_SITES.update({
    "reference/foundation/src/obds_ref/generation.py::target_filename::*": {"role": PRODUCER, "note": "safe mapping of canonical target identity"},
    "reference/foundation/src/obds_ref/generation.py::generation_identity::planHash": {"role": PRODUCER, "note": "generation identity binds manifest, plan and compiler"},
    "reference/foundation/src/obds_ref/generation.py::_report_hash::reportHash": {"role": PRODUCER, "note": "report seal excludes itself"},
    "reference/foundation/src/obds_ref/compiler.py::build_all::generationId": {"role": PRODUCER, "note": "publishes exact build identity"},
    "reference/foundation/src/obds_ref/compiler.py::build_all::reportHash": {"role": PRODUCER, "note": "seals in-memory report; output reports are sealed at publication"},
    "reference/foundation/src/obds_ref/cli.py::command_conformance::reportHash": {"role": PRODUCER, "note": "hashes the deterministic diff report, not a generation report"},
    "reference/foundation/src/obds_ref/generation.py::_read_report::reportHash": {
        "role": VERIFIER, "note": "reproduces the stored generation report seal",
        "gate": "if report['reportHash'] != _report_hash(report):",
        "neutralised": "if False and report['reportHash'] != _report_hash(report):",
        "reproduces": "_report_hash(report)",
    },
    "reference/foundation/src/obds_ref/generation.py::_read_report::generationId": {
        "role": VERIFIER, "note": "binds the report to the explicitly requested generation",
        "gate": "if report['generationId'] != generation_id or expected != generation_id:",
        "neutralised": "if False and (report['generationId'] != generation_id or expected != generation_id):",
        "reproduces": "generation_identity(report['manifestContentHash'], report['planHash'],",
    },
    "reference/foundation/src/obds_ref/generation.py::_read_report::planHash": {
        "role": COMPARISON_ONLY, "note": "a component of the reproduced generation binding",
        "after": "reference/foundation/src/obds_ref/generation.py::_read_report::generationId",
    },
    "reference/foundation/src/obds_ref/generation.py::load_generation_artifact::artifactHash": {
        "role": VERIFIER, "note": "compares reproduced artifact bytes to the generation's seal",
        "gate": "if artifact.get('artifactHash') != target['artifactHash'] or artefact_hash(artifact) != target['artifactHash']:",
        "neutralised": "if False and (artifact.get('artifactHash') != target['artifactHash'] or artefact_hash(artifact) != target['artifactHash']):",
        "reproduces": "artefact_hash(artifact)",
    },
    "reference/foundation/src/obds_ref/generation.py::load_generation_artifact::contentHash": {
        "role": COMPARISON_ONLY, "note": "compares sealed artifact identity against verified generation report",
        "after": "reference/foundation/src/obds_ref/generation.py::load_generation_artifact::artifactHash",
    },
    "reference/foundation/src/obds_ref/generation.py::load_generation_artifact::planHash": {
        "role": COMPARISON_ONLY, "note": "compares sealed artifact plan against verified report",
        "after": "reference/foundation/src/obds_ref/generation.py::load_generation_artifact::artifactHash",
    },
    "reference/foundation/src/obds_ref/generation.py::publish_generation::generationId": {"role": PRODUCER, "note": "publishes one immutable verified output generation"},
    "reference/foundation/src/obds_ref/generation.py::publish_generation::reportHash": {"role": PRODUCER, "note": "seals report before atomic publication"},
    "reference/foundation/src/obds_ref/runtime.py::_new_record::generationId": {"role": INTERNAL, "note": "initialises explicit in-memory execution with no generation discovery"},
    "reference/foundation/src/obds_ref/runtime.py::run_generation_with_model::generationId": {"role": INTERNAL, "note": "calls verified generation loader and records requested generation even on refusal"},
})
COMPILED_CONTEXT_CONSUMERS.update({
    "reference/foundation/src/obds_ref/generation.py::load_generation_artifact": EXECUTOR,
    "reference/foundation/src/obds_ref/projection.py::derive_projection": "internal deterministic renderer; runtime and assembly execute contract and seal before calling it; F3 adversarial tests drive both boundaries",
    "reference/context-assembly/projection.py::derive_projection": "byte-identical copy of the same internal projection renderer",
})
