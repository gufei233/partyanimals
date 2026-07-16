from __future__ import annotations

import json
import shutil
from pathlib import Path

from export_party_animals_resource_index import (
    ANIMALS_CORE_JSON,
    CORE_FEATURE_TAG_IDS,
    OUT_JSON,
    TAG_LABELS_EN,
    TAG_LABELS_ZH,
    build_index,
)


ROOT = Path(__file__).resolve().parents[1]
SITE_ANIMALS_DIR = ROOT / "images" / "animals"
SITE_DATA_DIR = ROOT / "data"
SITE_ANIMALS_JS = SITE_DATA_DIR / "animals.generated.js"


def copy_if_changed(source: Path, target: Path) -> bool:
    if target.exists() and target.read_bytes() == source.read_bytes():
        return False
    shutil.copyfile(source, target)
    return True


def prune_unreferenced_images(keep_paths: set[Path]) -> int:
    SITE_ANIMALS_DIR.mkdir(parents=True, exist_ok=True)
    removed = 0
    for path in SITE_ANIMALS_DIR.glob("*.png"):
        if path in keep_paths:
            continue
        path.unlink()
        removed += 1
    return removed


def sync_animal_images(animals: list[dict]) -> tuple[list[dict], dict[str, int]]:
    SITE_ANIMALS_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    keep_paths: set[Path] = set()
    stats = {
        "images_copied": 0,
        "images_unchanged": 0,
        "images_missing": 0,
        "images_removed": 0,
    }
    for animal in animals:
        target = SITE_ANIMALS_DIR / f"{animal['hero_id']}.png"
        keep_paths.add(target)
        source_value = animal.get("image")
        if not isinstance(source_value, str) or not source_value:
            stats["images_missing"] += 1
            copied.append({**animal, "image": None})
            continue
        source = ROOT / source_value
        if not source.exists():
            stats["images_missing"] += 1
            copied.append({**animal, "image": None})
            continue
        if copy_if_changed(source, target):
            stats["images_copied"] += 1
        else:
            stats["images_unchanged"] += 1
        copied.append(
            {
                **animal,
                "image": target.relative_to(ROOT).as_posix(),
            }
        )
    stats["images_removed"] = prune_unreferenced_images(keep_paths)
    return copied, stats


def build_site_payload_with_stats(resources: dict) -> tuple[dict, dict[str, int]]:
    feature_ids = [
        tag_id
        for tag_id in CORE_FEATURE_TAG_IDS
        if any(tag_id in animal["feature_ids"] for animal in resources["animals_core"])
    ]
    animals, image_stats = sync_animal_images(resources["animals_core"])
    payload = {
        "features": [
            {
                "id": tag_id,
                "name": TAG_LABELS_ZH.get(tag_id, tag_id),
                "nameEn": TAG_LABELS_EN.get(tag_id, tag_id),
            }
            for tag_id in feature_ids
        ],
        "items": [
            {
                "id": animal["hero_id"],
                "variantId": animal["variant_item_id"],
                "name": animal["name"],
                "nameEn": animal["name_en"],
                "image": animal["image"],
                "assetId": animal["full_asset_id"],
                "featureIds": animal["feature_ids"],
                "features": animal["features"],
            }
            for animal in animals
        ],
    }
    return payload, image_stats


def build_site_payload(resources: dict) -> dict:
    payload, _ = build_site_payload_with_stats(resources)
    return payload


def write_generated_js(payload: dict) -> None:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    SITE_ANIMALS_JS.write_text(
        "window.PARTY_ANIMALS_SITE_DATA = window.PARTY_ANIMALS_SITE_DATA || {};\n"
        f"window.PARTY_ANIMALS_SITE_DATA.animals = {body};\n",
        encoding="utf-8",
    )


def main() -> int:
    resources = build_index()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(resources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    minimal_core = [
        {"name": row["name"], "image": row["image"], "features": row["features"]}
        for row in resources["animals_core"]
    ]
    ANIMALS_CORE_JSON.write_text(json.dumps(minimal_core, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload, image_stats = build_site_payload_with_stats(resources)
    write_generated_js(payload)

    print(
        json.dumps(
            {
                "animals": len(payload["items"]),
                "features": len(payload["features"]),
                **image_stats,
                "data_file": SITE_ANIMALS_JS.relative_to(ROOT).as_posix(),
                "image_dir": SITE_ANIMALS_DIR.relative_to(ROOT).as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
