#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import yaml

from canonical import canonical_json_bytes, sha256_id



def manifest_hash(manifest):
    approval = manifest.get("approval")
    clone = dict(manifest)
    clone.pop("approval", None)
    return sha256_id(clone)


class _StrictJSONDuplicate(ValueError):
    pass


def _strict_pairs(pairs):
    import unicodedata
    result = {}
    seen = set()
    for key, value in pairs:
        nkey = unicodedata.normalize("NFC", key)
        if nkey in seen:
            raise _StrictJSONDuplicate(f"duplicate object key: {key}")
        seen.add(nkey)
        result[key] = value
    return result


class _OBDSSafeLoader(yaml.SafeLoader):
    pass


for ch, resolvers in list(_OBDSSafeLoader.yaml_implicit_resolvers.items()):
    _OBDSSafeLoader.yaml_implicit_resolvers[ch] = [
        item for item in resolvers if item[0] != "tag:yaml.org,2002:bool"
    ]
_OBDSSafeLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|false|True|False|TRUE|FALSE)$"),
    list("tTfF"),
)


def _construct_mapping(loader, node, deep=False):
    import unicodedata
    mapping = {}
    seen = set()
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise yaml.constructor.ConstructorError(None, None, "mapping keys must be strings", key_node.start_mark)
        nkey = unicodedata.normalize("NFC", key)
        if nkey in seen:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate mapping key: {key}", key_node.start_mark)
        seen.add(nkey)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_OBDSSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _strict_parse_int(text):
    import math
    value = int(text)
    try:
        f = float(value)
    except OverflowError as exc:
        raise ValueError("integer is outside IEEE-754 binary64") from exc
    if not math.isfinite(f) or int(f) != value:
        raise ValueError("integer is not exactly representable as IEEE-754 binary64")
    return value


def _reject_constant(text):
    raise ValueError(f"non-finite JSON number is invalid: {text}")


def load(path):
    text = Path(path).read_text(encoding="utf-8")
    if str(path).lower().endswith(".json"):
        data = json.loads(
            text,
            object_pairs_hook=_strict_pairs,
            parse_int=_strict_parse_int,
            parse_constant=_reject_constant,
        )
    else:
        data = yaml.load(text, Loader=_OBDSSafeLoader)
    canonical_json_bytes(data)
    return data


def words(value):
    return [part.lower() for part in re.findall(r"[A-Za-z0-9]+", value)]


def humanise_id(element_id):
    tail = element_id.split(".")[-1]
    return re.sub(r"[-_]+", " ", tail).strip().title()


def first_text(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("statement", "summary", "description", "canonicalWording", "name", "title"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return ""


def shorten(text, limit=180):
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "…"


def render_value(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_views(manifest, chapter_map=None):
    elements = manifest.get("elements", [])
    by_id = {item["id"]: item for item in elements}
    if len(by_id) != len(elements):
        raise ValueError("duplicate element IDs")

    manifest_ref = {
        "id": manifest["id"],
        "version": manifest["version"],
        "contentHash": manifest.get("approval", {}).get("contentHash") or manifest_hash(manifest),
    }

    if chapter_map:
        groups = chapter_map.get("chapters", [])
    else:
        families = {}
        for item in elements:
            families.setdefault(item["family"], []).append(item["id"])
        groups = [
            {
                "id": f"chapter.{family}",
                "title": family.replace("-", " ").title(),
                "elementIds": sorted(ids),
            }
            for family, ids in sorted(families.items())
            if ids
        ]

    element_to_chapters = {element_id: [] for element_id in by_id}
    chapters = []
    for group in groups:
        ids = group["elementIds"]
        missing = [item for item in ids if item not in by_id]
        if missing:
            raise ValueError(f"chapter {group['id']} has missing elements: {missing}")
        blocks = []
        for element_id in ids:
            item = by_id[element_id]
            element_to_chapters[element_id].append(group["id"])
            blocks.append(
                f"## {element_id} [{item.get('family')}/{item.get('kind')}/{item.get('state')}]\n"
                f"{render_value(item.get('value')) if 'value' in item else 'No value.'}"
            )
        chapter = {
            "kind": "obds-reasoning-chapter",
            "schemaVersion": "1.0.0",
            "id": group["id"],
            "title": group["title"],
            "manifest": manifest_ref,
            "elementIds": ids,
            "content": "\n\n".join(blocks),
            "renderer": {
                "id": "org.openbranddefinition.reference-chapter-renderer",
                "version": "1.0.0",
            },
        }
        chapter["chapterHash"] = sha256_id(chapter)
        chapters.append(chapter)

    cards = []
    for item in sorted(elements, key=lambda value: value["id"]):
        element_id = item["id"]
        text = first_text(item.get("value"))
        label = (
            item.get("value", {}).get("name")
            if isinstance(item.get("value"), dict) and isinstance(item["value"].get("name"), str)
            else humanise_id(element_id)
        )
        summary = shorten(text) if text else f"{item['family']} {item['kind']} element: {label}."
        alias_set = set(words(element_id.replace(".", " ")))
        alias_set.update(words(label))
        if isinstance(item.get("value"), dict):
            for key in ("name", "title", "canonicalWording"):
                value = item["value"].get(key)
                if isinstance(value, str):
                    alias_set.update(words(value))
        card = {
            "kind": "obds-search-card",
            "schemaVersion": "1.0.0",
            "id": f"urn:obds:search-card:{element_id}",
            "manifest": manifest_ref,
            "elementId": element_id,
            "label": label,
            "summary": summary,
            "aliases": sorted(alias_set),
            "chapterRefs": sorted(element_to_chapters[element_id]),
            "generator": {
                "id": "org.openbranddefinition.reference-search-card-renderer",
                "version": "1.0.0",
            },
        }
        card["cardHash"] = sha256_id(card)
        cards.append(card)

    index = {
        "kind": "obds-search-index",
        "schemaVersion": "1.0.0",
        "manifest": manifest_ref,
        "cards": cards,
    }
    index["indexHash"] = sha256_id(index)

    chapter_set = {
        "kind": "obds-reasoning-chapter-set",
        "schemaVersion": "1.0.0",
        "manifest": manifest_ref,
        "chapters": chapters,
    }
    chapter_set["chapterSetHash"] = sha256_id(chapter_set)

    return index, chapter_set


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--chapter-map")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    manifest = load(args.manifest)
    chapter_map = load(args.chapter_map) if args.chapter_map else None
    index, chapters = build_views(manifest, chapter_map)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "search-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "reasoning-chapters.json").write_text(
        json.dumps(chapters, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
