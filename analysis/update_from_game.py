from __future__ import annotations

import argparse
import json
from pathlib import Path

import build_party_animals_web_data as web_data
import extract_party_animals_web_assets as web_assets
from decrypt_party_animals import DEFAULT_GAME_DIR, decrypt_catalogs, decrypt_hybridclr
from extract_party_animals_web_assets import EXTRACTED_DIR, build_resources_manifest
from sync_site_animals import build_site_payload_with_stats, write_generated_js
from export_party_animals_resource_index import ANIMALS_CORE_JSON, OUT_JSON, build_index
from build_party_animals_achievement_map_index import (
    CORE_OUT_PATH as ACHIEVEMENTS_CORE_JSON,
    OUT_PATH as ACHIEVEMENTS_FULL_JSON,
    build_achievement_index,
    build_core_index,
)
from sync_site_achievements import (
    build_site_payload_with_stats as build_achievement_site_payload_with_stats,
    write_generated_js as write_achievement_generated_js,
)


ROOT = Path(__file__).resolve().parents[1]
DECRYPTED_DIR = ROOT / "analysis" / "decrypted"


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update site animal data from a local Party Animals install.")
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--skip-decrypt", action="store_true", help="Only rebuild site data from already decrypted files.")
    args = parser.parse_args()

    report: dict[str, object] = {
        "game_dir": str(args.game_dir),
        "decrypted_dir": str(DECRYPTED_DIR.relative_to(ROOT)),
        "steps": [],
    }
    web_assets.DEFAULT_GAME_DIR = args.game_dir
    web_data.DEFAULT_GAME_DIR = args.game_dir

    if not args.skip_decrypt:
        hybridclr = decrypt_hybridclr(args.game_dir, DECRYPTED_DIR)
        catalogs = decrypt_catalogs(args.game_dir, DECRYPTED_DIR)
        report["steps"].append(
            {
                "name": "decrypt",
                "hybridclr_files": len(hybridclr),
                "catalogs": len(catalogs),
            }
        )

    manifest = build_resources_manifest()
    manifest_path = EXTRACTED_DIR / "resources_manifest.json"
    write_json(manifest_path, manifest)
    report["steps"].append(
        {
            "name": "extract_resources",
            "groups": {
                name: {
                    "catalog_sprite_count": group["catalog_sprite_count"],
                    "exported_count": group["exported_count"],
                }
                for name, group in manifest["groups"].items()
            },
            "data_file": manifest_path.as_posix(),
        }
    )

    resources = build_index()
    write_json(OUT_JSON, resources)
    minimal_core = [
        {"name": row["name"], "image": row["image"], "features": row["features"]}
        for row in resources["animals_core"]
    ]
    write_json(ANIMALS_CORE_JSON, minimal_core)
    report["steps"].append(
        {
            "name": "extract_animals",
            "animals": len(resources["animals_core"]),
            "animals_with_image": sum(1 for row in resources["animals_core"] if row["image"]),
            "features": len({feature for row in resources["animals_core"] for feature in row["feature_ids"]}),
        }
    )

    payload, image_stats = build_site_payload_with_stats(resources)
    write_generated_js(payload)
    report["steps"].append(
        {
            "name": "sync_site",
            "animals": len(payload["items"]),
            "features": len(payload["features"]),
            **image_stats,
            "data_file": "data/animals.generated.js",
            "image_dir": "images/animals",
        }
    )

    achievements = build_achievement_index()
    achievements_core = build_core_index(achievements)
    write_json(ACHIEVEMENTS_FULL_JSON, achievements)
    write_json(ACHIEVEMENTS_CORE_JSON, achievements_core)
    achievement_payload, achievement_image_stats = build_achievement_site_payload_with_stats(achievements_core)
    write_achievement_generated_js(achievement_payload)
    report["steps"].append(
        {
            "name": "sync_achievements",
            "achievements": len(achievement_payload["items"]),
            "maps": len(achievement_payload["features"]),
            **achievement_image_stats,
            "data_file": "data/achievements.generated.js",
            "image_dir": "images/achievements",
        }
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
