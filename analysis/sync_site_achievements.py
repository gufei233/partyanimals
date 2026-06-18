from __future__ import annotations

import json
import shutil
from pathlib import Path

from build_party_animals_achievement_map_index import build_achievement_index, build_core_index
from build_party_animals_achievement_map_index import CORE_OUT_PATH, OUT_PATH
from extract_party_animals_web_assets import safe_filename


ROOT = Path(__file__).resolve().parents[1]
SITE_ACHIEVEMENTS_DIR = ROOT / "images" / "achievements"
SITE_DATA_DIR = ROOT / "data"
SITE_ACHIEVEMENTS_JS = SITE_DATA_DIR / "achievements.generated.js"


def copy_if_changed(source: Path, target: Path) -> bool:
    if target.exists() and target.read_bytes() == source.read_bytes():
        return False
    shutil.copyfile(source, target)
    return True


def prune_unreferenced_images(keep_paths: set[Path]) -> int:
    SITE_ACHIEVEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    removed = 0
    for path in SITE_ACHIEVEMENTS_DIR.glob("*"):
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        if path in keep_paths:
            continue
        path.unlink()
        removed += 1
    return removed


def sync_achievement_images(achievements: list[dict]) -> tuple[list[dict], dict[str, int]]:
    SITE_ACHIEVEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    keep_paths: set[Path] = set()
    stats = {
        "images_copied": 0,
        "images_unchanged": 0,
        "images_missing": 0,
        "images_removed": 0,
    }
    for achievement in achievements:
        source_value = achievement.get("icon")
        if not source_value:
            stats["images_missing"] += 1
            copied.append({**achievement, "icon": None})
            continue
        source = ROOT / source_value
        target = SITE_ACHIEVEMENTS_DIR / f"{achievement['achievement_id']}.png"
        keep_paths.add(target)
        if not source.exists():
            stats["images_missing"] += 1
            copied.append({**achievement, "icon": None})
            continue
        if copy_if_changed(source, target):
            stats["images_copied"] += 1
        else:
            stats["images_unchanged"] += 1
        copied.append({**achievement, "icon": target.relative_to(ROOT).as_posix()})
    if achievements and stats["images_missing"] == len(achievements):
        raise RuntimeError(
            "all achievement icons are missing; run extract_party_animals_web_assets.py "
            "or check analysis/extracted/resources_manifest.json before pruning site images"
        )
    stats["images_removed"] = prune_unreferenced_images(keep_paths)
    return copied, stats


def build_site_payload_with_stats(core: dict) -> tuple[dict, dict[str, int]]:
    copied, image_stats = sync_achievement_images(core["achievements"])
    map_names = []
    seen_maps = set()
    for achievement in copied:
        name = achievement.get("map_name") or "其他"
        if name not in seen_maps:
            seen_maps.add(name)
            map_names.append(name)

    map_index = {name: index for index, name in enumerate(map_names)}
    items = [
        {
            "id": achievement["achievement_id"],
            "name": achievement["title"],
            "condition": achievement["condition"],
            "image": achievement["icon"],
            "mapName": achievement.get("map_name") or "其他",
            "features": [map_index[achievement.get("map_name") or "其他"]],
        }
        for achievement in copied
    ]
    missing_features = [item["id"] for item in items if not item["features"]]
    if missing_features:
        raise ValueError(f"achievements without generated feature indexes: {missing_features}")

    payload = {
        "counts": core["counts"],
        "features": [{"id": safe_filename(name), "name": name} for name in map_names],
        "items": items,
        "maps": core["maps"],
    }
    return payload, image_stats


def build_site_payload(core: dict) -> dict:
    payload, _ = build_site_payload_with_stats(core)
    return payload


def write_generated_js(payload: dict) -> None:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    SITE_ACHIEVEMENTS_JS.write_text(
        "window.PARTY_ANIMALS_SITE_DATA = window.PARTY_ANIMALS_SITE_DATA || {};\n"
        f"window.PARTY_ANIMALS_SITE_DATA.achievements = {body};\n",
        encoding="utf-8",
    )


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    data = build_achievement_index()
    core = build_core_index(data)
    write_json(OUT_PATH, data)
    write_json(CORE_OUT_PATH, core)
    payload, image_stats = build_site_payload_with_stats(core)
    write_generated_js(payload)
    print(
        json.dumps(
            {
                "achievements": len(payload["items"]),
                "maps": len(payload["features"]),
                **image_stats,
                "data_file": SITE_ACHIEVEMENTS_JS.relative_to(ROOT).as_posix(),
                "image_dir": SITE_ACHIEVEMENTS_DIR.relative_to(ROOT).as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
