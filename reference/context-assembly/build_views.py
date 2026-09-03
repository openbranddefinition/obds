#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from canonical import identity_key, manifest_content_hash, sha256_id



def manifest_hash(manifest):
    approval = manifest.get("approval")
    clone = dict(manifest)
    clone.pop("approval", None)
    return sha256_id(clone)


# Section 28.1. Until 3.0.0 this file carried its own approximation of the
# governed reader — YAML 1.1 minus booleans — under which `017` bound 15 and
# `12:30` bound 750 while the compiler bound 17 and the string. Every Search
# Card claims exact binding to a `manifest.contentHash`; six of the seven
# readers in the release could not compute the value that hash covers.
#
# It also derived its loader as a bare subclass and then item-assigned into
# `yaml_implicit_resolvers`, which is inherited, so importing this module
# mutated PyYAML for every consumer in the process, including the governed
# writer. That is why the reader is imported here and no loader is built.
from governed_io import load_data as load


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
    # Section 8.0a: identities are compared on their canonical form.
    by_id = {identity_key(item["id"]): item for item in elements}
    if len(by_id) != len(elements):
        raise ValueError("duplicate element IDs")

    # Section 8.0a: the manifest identity is an identity, so it goes through the
    # identity rule before it is emitted into a governed view. Emitting it raw
    # let two manifests differing only CR-vs-LF share one `approval.contentHash`,
    # one `indexHash` and one `chapterSetHash` while the views declared two
    # different governed identities — the Class B invariant, reached through a
    # path Class B's tests never drove.
    # Section 7: the views publish `approval.contentHash` as their claim of exact
    # binding to an approved manifest, so they have to reproduce it. Copying it
    # let a manifest be edited after approval and still be published under the
    # old hash: two different governed identity sets in Search Cards, one claimed
    # approved manifest.
    declared_approval = (manifest.get("approval") or {}).get("contentHash")
    if declared_approval is not None and declared_approval != manifest_content_hash(manifest):
        raise ValueError(
            "manifest does not reproduce its approval contentHash, so a derived view "
            "cannot claim binding to it"
        )

    manifest_ref = {
        "id": identity_key(manifest["id"]),
        "version": manifest["version"],
        "contentHash": manifest.get("approval", {}).get("contentHash") or manifest_hash(manifest),
    }

    if chapter_map:
        groups = chapter_map.get("chapters", [])
    else:
        families = {}
        for item in elements:
            families.setdefault(item["family"], []).append(identity_key(item["id"]))
        groups = [
            {
                "id": f"chapter.{family}",
                "title": family.replace("-", " ").title(),
                "elementIds": sorted(identity_key(item) for item in ids),
            }
            for family, ids in sorted(families.items())
            if ids
        ]

    element_to_chapters = {element_id: [] for element_id in by_id}
    chapters = []
    for group in groups:
        ids = group["elementIds"]
        missing = [item for item in ids if identity_key(item) not in by_id]
        if missing:
            raise ValueError(f"chapter {group['id']} has missing elements: {missing}")
        blocks = []
        for raw_element_id in ids:
            element_id = identity_key(raw_element_id)
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
            "elementIds": [identity_key(item) for item in ids],
            "content": "\n\n".join(blocks),
            "renderer": {
                "id": "org.openbranddefinition.reference-chapter-renderer",
                "version": "1.0.0",
            },
        }
        chapter["chapterHash"] = sha256_id(chapter)
        chapters.append(chapter)

    cards = []
    for item in sorted(elements, key=lambda value: identity_key(value["id"])):
        element_id = identity_key(item["id"])
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
