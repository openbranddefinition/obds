# Compatibility analysis and version recommendation

Informative. Baseline sources are pinned in BASELINE-SOURCES.json.

Existing manifests, plans and profile claims retain their contracts. Absence of Task Facts does not invalidate Foundation conformance. Brand States remain defined, unknown, not_defined and not_applicable; Task Facts states and outcomes never replace them. Scope, precedence, authority and Value Contracts remain unchanged.

OBDS 4.0.4 section 13.1 requires exact Brand Element IDs: dependencies cannot silently become subject selectors or select different overrides. Static requirements remain required. Sections 14.3–14.3c define normalized governed canonicalization separately from TFJ, which does not normalize Unicode and preserves array serialization order. Thus snapshotHash is not governedResultHash, modelInputHash, assemblyHash, taskInputHash or manifest contentHash. inputPackageHash identifies exact inspected package bytes excluding the sidecar, rather than aliasing an existing internal package hash.

Pinned Model Input Package, Runtime Decision Record and build-report schemas have closed roots. Adding Task Facts fields would fail current validation. The Build Plan has a different extension posture, but that does not authorize portable new semantics. External sidecars avoid this issue; no existing schema changes are proposed. A host opting into Task Facts cannot rely on a legacy consumer to enforce conditions it does not understand.

Integration remains unproven, limiting the proposed claim to evaluator interoperability. This independent optional claim and unchanged existing requirements make the addition backwards compatible. Under section 27's version classes, recommend MINOR: prospective 4.1.0. PATCH would misclassify a new capability; MAJOR is unnecessary here. Later mandatory use, field reinterpretation, changed acceptance or changed hashes would require renewed analysis. Candidate-v1 itself is not OBDS 4.1.0.
