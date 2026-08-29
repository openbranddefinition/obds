# OBDS 1.0 Derived Views Reference

This small reference package builds:

- one Search Card per Brand Element;
- deterministic Reasoning Chapters from an explicit chapter map.

## Run

```bash
python build_views.py examples/manifest.yaml   --chapter-map examples/chapter-map.yaml   --out build/
```

## Test

```bash
pytest -q
```

## Important

Search Cards and Reasoning Chapters are generated, non-authoritative views.

Search Cards are for finding. Full elements are for exact answers. Chapters are for relationships and multi-rule reasoning.
