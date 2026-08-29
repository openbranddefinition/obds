# OBDS 1.0.0 Reference Compiler

Neutral reference implementation for OBDS Foundation 1.0.0.

```bash
obds validate manifest.yaml
obds build manifest.yaml build-plan.yaml --out build/
obds diff old.yaml new.yaml
obds check context.json --phase postflight --text "candidate"
obds conformance conformance-suite.yaml --out result.json
```

Checks unique IDs, internal references, Build Plan references, sRGB HEX/RGB consistency, manifest diffs, Runtime Decision Records and instrumented zero-call behaviour.
