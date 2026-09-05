# OBDS 4.0.0 Production Boundary Closure

Status: RATIFIED — publisher decision in the implementation session, 5 September 2026.
Scope: F1–F5 only. Dependencies, CI, general refactoring, performance and unrelated documentation repairs are deferred.

## Bounded audit and version decision

All five counterexamples were reproduced against 3.0.4 despite its passing 1,079-case suite. The Runtime Decision Record 3.0.0 has a closed `decision` enum and `additionalProperties: false`; no existing extension mechanism expresses provider failure. `model_failed` requires a new record contract. Projection provenance and generation binding add required production semantics. This is OBDS **4.0.0**, not a patch or a backwards-compatible minor release. Previously published schemas and `spec/` snapshots remain immutable.

## Ratified boundaries

- **F1:** Logical target IDs retain their existing semantics. Files use a deterministic mapping of canonical identity to a safe name. Resolved paths and symlinks cannot escape the output root.
- **F2:** A generation identifies one exact manifest/plan/compiler build. Its artifacts and report are immutable. A request explicitly bound to B cannot use A when B fails, is absent, or omits that target. Explicit selection of A remains valid; no automatic revocation of historical releases occurs. The root report is a convenience view, not an implicit runtime selection mechanism.
- **F3:** All four governed package slots are reproducible from the bound compiled universe and a validated structured projection selection: hardBoundaries, factGrounding, stateMap, guidanceContext. External chapter text and self-resealed slots are not authoritative. Required facts, boundaries and compiled gaps cannot be omitted. The registered deterministic reference projection is verified before a model call and before a review decision. Existing compact rendering remains possible through a specified, verifiable renderer rather than through arbitrary supplied prose.
- **F4:** Execute the published manifest schema before identity or semantic iteration. Validate approval identity and RFC 3339 time, including actual calendar validity. Invalid documents yield structured validation diagnostics / ValidationFailure at build and CLI boundaries, never a shape-driven TypeError.
- **F5:** A provider exception or malformed adapter response yields `model_failed`, `modelCall.called: true`, withheld output and a Runtime Decision Record. `called` means the instrumented adapter was invoked, not that remote execution is known to have completed. Do not retry automatically or reinterpret this as a rule violation. Process termination and durable-storage failure require operational recovery; no in-process handler can guarantee completion after a killed process.

## Acceptance

F1: adversarial IDs, canonical equivalent IDs, case-sensitive identities, path and symlink containment. F2: A ready / B failed / B missing / removed target / explicit rollback A / repeated immutable generation / tampering. F3: independently mutate and reseal each slot, selections, chapter payloads and required-content omissions; zero model calls and review rejection. F4: malformed root and collections, schema-invalid metadata and approval types/calendar/timezone; controlled diagnostics. F5: both runtime entry points, provider exception and malformed response, append-only schema-valid evidence with no released output; old record contract rejects the new outcome.

Specification, schemas, implementation, migration and tests ship together. No deployment or external publication is part of this implementation task.

## Abschlussnachweis, 5. September 2026

F1–F5 sind in Spezifikation, Schemas, Referenzimplementierung und Migration umgesetzt. Der geschlossene Decision-Enum des bisherigen Runtime-Vertrags bestätigt die Major-Version **4.0.0**.

| Grenze | Umsetzung | Reproduzierbarer Nachweis |
|---|---|---|
| F1 | SHA-256-Dateinamensabbildung kanonischer targetId; resolved-path containment; Ablehnung von Symlinks einschließlich Output-Root | Traversal, absolute und lange IDs, kanonische Gleichheit, Groß-/Kleinschreibung, manipulierte Output-Pfade |
| F2 | Unveränderliche Generation aus Manifest-/Plan-Hash und Compiler-Identität; expliziter Generation-Loader | A bereit, B fehlgeschlagen/fehlend/ohne Target, kein Fallback, explizites Rollback A, unveränderte A-Bytes |
| F3 | Gemeinsamer deterministischer Renderer und Runtime-/Review-Verifikation sämtlicher vier Slots aus dem gebundenen Compiled Context | Jeden Slot ersetzen/leeren und neu hashen; erforderliche Auswahl entfernen; Chapter-Prosa manipulieren: Ablehnung vor Model Call |
| F4 | Published-Schema-Validierung vor semantischer Iteration; tatsächliche Kalender- und Zeitzonenprüfung für Approval-Zeitpunkte | Ungültige Root-/Collection-/Metadata-Typen und Approval-Werte liefern kontrollierte Diagnostik |
| F5 | model_failed mit called=true, zurückgehaltenem Output und Runtime Decision Record | Beide Runtime-Pfade, Timeout/Exception/ungültige Adapterantwort, persistierte Records, append-only Fehler- und Erfolgshistorie |

Die konkreten Regressionstests stehen in [test_obds_400_boundaries.py](../reference/foundation/tests/test_obds_400_boundaries.py). Die systemischen Hash- und Executor-Prüfungen wurden um den Generation-Loader erweitert.

Ausgeführte Abschlussprüfungen:

- `.venv/bin/python reference/run_all.py`: **1.158 bestanden**, 0 fehlgeschlagen, 0 übersprungen.
- `.venv/bin/python reference/release-gate.py`: **PASS**, 26/26 offizielle Foundation-Konformitätsfälle; 242 Paketdateien vorhanden und hashverifiziert.
- `.venv/bin/python tools/docs-smoke-test.py`: **PASS**, dokumentierte Befehle einschließlich vollständiger Suite und Release-Gate im Repository und im frisch entpackten Archiv.
- `git diff --check`: sauber. Historische `spec/`-Snapshots, veröffentlichte 1.x-/3.x-Schemas, Value-Schemas und `requirements.txt`: unverändert.

[Migration](../OBDS-4.0.0-MIGRATION.md) · [Testergebnis](../OBDS-4.0.0-TEST-RESULT.json) · [Testausgabe](../OBDS-4.0.0-TEST-OUTPUT.txt) · [Release-Archiv](../spec/4.0.0/OBDS-4.0.0-FINAL.zip).

Das Release-Paket ist lokal erstellt und geprüft. Es wurde weder committed noch gepusht oder deployed. Dependency/CI/Refactoring/Performance und unabhängige Link-Reparaturen bleiben geparkt.
