from pathlib import Path
import importlib.util
import json
import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("build_views", ROOT / "build_views.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_views_are_deterministic_and_traceable(tmp_path):
    manifest = yaml.safe_load((ROOT / "examples" / "manifest.yaml").read_text(encoding="utf-8"))
    chapter_map = yaml.safe_load((ROOT / "examples" / "chapter-map.yaml").read_text(encoding="utf-8"))
    first_index, first_chapters = module.build_views(manifest, chapter_map)
    second_index, second_chapters = module.build_views(manifest, chapter_map)

    assert first_index == second_index
    assert first_chapters == second_chapters
    assert len(first_index["cards"]) == len(manifest["elements"])

    element_ids = {item["id"] for item in manifest["elements"]}
    for card in first_index["cards"]:
        assert card["elementId"] in element_ids
        assert card["summary"]
        assert card["cardHash"] == module.sha256_id({key: value for key, value in card.items() if key != "cardHash"})

    for chapter in first_chapters["chapters"]:
        assert set(chapter["elementIds"]).issubset(element_ids)
        assert chapter["chapterHash"] == module.sha256_id({key: value for key, value in chapter.items() if key != "chapterHash"})


def test_schemas_validate():
    manifest = yaml.safe_load((ROOT / "examples" / "manifest.yaml").read_text(encoding="utf-8"))
    chapter_map = yaml.safe_load((ROOT / "examples" / "chapter-map.yaml").read_text(encoding="utf-8"))
    index, chapters = module.build_views(manifest, chapter_map)

    card_schema = json.loads((ROOT / "schemas" / "search-card.schema.json").read_text(encoding="utf-8"))
    chapter_schema = json.loads((ROOT / "schemas" / "reasoning-chapter.schema.json").read_text(encoding="utf-8"))

    for card in index["cards"]:
        jsonschema.validate(card, card_schema)
    for chapter in chapters["chapters"]:
        jsonschema.validate(chapter, chapter_schema)


def test_missing_chapter_element_fails():
    manifest = yaml.safe_load((ROOT / "examples" / "manifest.yaml").read_text(encoding="utf-8"))
    chapter_map = {
        "chapters": [{
            "id": "chapter.bad",
            "title": "Bad",
            "elementIds": ["identity.phantom"],
        }]
    }
    try:
        module.build_views(manifest, chapter_map)
    except ValueError as error:
        assert "missing elements" in str(error)
    else:
        raise AssertionError("expected ValueError")
