from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import msgpack

from build_party_animals_web_data import (
    EXTRACTED_DIR,
    catalog_rows_for_primary_keys,
    export_variant_avatars,
    extract_localization_terms,
    read_catalog,
    read_chained_table,
    term_lookup,
    text_asset_bytes,
)


OUT_DIR = EXTRACTED_DIR / "resource_index"
OUT_JSON = OUT_DIR / "party_animals_resources.json"
ANIMALS_CORE_JSON = OUT_DIR / "animals_core.json"

CORE_FEATURE_TAG_IDS = [
    "WithHornHero",
    "CanFlyHero",
    "CanDiveHero",
    "EggLayingHero",
    "FurryHero",
    "BigEyesHero",
    "FelidaeHero",
    "CanidaeHero",
    "MeatEaterHero",
    "PlantEaterHero",
    "LongTailHero",
]

TAG_LABELS_ZH = {
    "CanidaeHero": "犬科",
    "EggLayingHero": "会下蛋",
    "FelidaeHero": "猫科",
    "MeatEaterHero": "吃肉",
    "PlantEaterHero": "吃植物",
    "FurryHero": "毛茸茸",
    "CanFlyHero": "会飞",
    "CanDiveHero": "会潜水",
    "WithHornHero": "头上有角",
    "BigEyesHero": "眼睛大",
    "LongTailHero": "尾巴长",
    "DogHero": "狗",
    "CatHero": "猫",
    "DogPluralHero": "狗",
    "CatPluralHero": "猫",
    "LloydHero": "阿呆",
    "HarryHero": "阿瓜",
    "CocoHero": "鳄霸",
    "Luckin2024Variant": "瑞幸 2024",
    "SpecialAnimatedVariant": "特殊动态皮肤",
}


TAG_LABELS_EN = {
    "CanidaeHero": "Canidae",
    "EggLayingHero": "Egg laying",
    "FelidaeHero": "Felidae",
    "MeatEaterHero": "Meat eater",
    "PlantEaterHero": "Plant eater",
    "FurryHero": "Furry",
    "CanFlyHero": "Can fly",
    "CanDiveHero": "Can dive",
    "WithHornHero": "With horn",
    "BigEyesHero": "Big eyes",
    "LongTailHero": "Long tail",
    "DogHero": "Dog",
    "CatHero": "Cat",
    "DogPluralHero": "Dogs",
    "CatPluralHero": "Cats",
    "LloydHero": "Lloyd",
    "HarryHero": "Harry",
    "CocoHero": "Coco",
    "Luckin2024Variant": "Luckin 2024",
    "SpecialAnimatedVariant": "Special animated variant",
}


def read_config_dict(name: str) -> dict[str, list[Any]]:
    return msgpack.unpackb(text_asset_bytes(name), raw=False, strict_map_key=False)


def read_item_rows() -> dict[str, list[Any]]:
    rows: dict[str, list[Any]] = {}
    for row in read_chained_table("Item"):
        if not row or not isinstance(row[0], str):
            continue
        if len(row) < 12:
            continue
        rows[row[0]] = row
    return rows


def avatar_primary_key(full_asset_id: str | None) -> tuple[str | None, str | None]:
    if not full_asset_id:
        return None, None
    match = re.match(r"(AC_\d+)", full_asset_id)
    if not match:
        return None, None
    short_asset = f"{match.group(1)}_Avatar"
    return short_asset, f"heoui-item-variant/{short_asset}"


def local_name(display_names: dict[str, dict[str, str]], item_id: str) -> dict[str, str | None]:
    loc = display_names.get(item_id, {})
    return {
        "name": loc.get("zh-CN") or loc.get("en") or "",
        "name_en": loc.get("en") or "",
        "name_term": loc.get("term"),
    }


def build_index() -> dict[str, Any]:
    catalog = read_catalog()
    localization = extract_localization_terms()
    display_names = term_lookup(localization, "inventory_item", "_DisplayName")

    heroes_table = read_config_dict("Hero")
    occupations_table = read_config_dict("Occupation")
    variants_table = read_config_dict("Variant")
    item_tags_table = read_config_dict("ItemTag")
    item_rows = read_item_rows()

    hero_tag_ids: dict[str, list[str]] = {hero_id: [] for hero_id in heroes_table}
    variant_tag_ids: dict[str, list[str]] = {}
    tags = []
    for tag_id, row in sorted(item_tags_table.items()):
        item_type = row[1]
        item_ids = row[2]
        tag = {
            "tag_id": tag_id,
            "label": TAG_LABELS_ZH.get(tag_id, tag_id),
            "label_en": TAG_LABELS_EN.get(tag_id, tag_id),
            "item_type": item_type,
            "item_ids": item_ids,
            "count": len(item_ids),
        }
        tags.append(tag)
        if item_type == 0:
            for hero_id in item_ids:
                hero_tag_ids.setdefault(hero_id, []).append(tag_id)
        elif item_type == 7:
            for variant_id in item_ids:
                variant_tag_ids.setdefault(variant_id, []).append(tag_id)

    default_variant_ids = {
        occupations_table[hero_row[1]][2]
        for hero_row in heroes_table.values()
        if hero_row[1] in occupations_table
    }
    primary_keys = set()
    variants = []
    for variant_id, variant_row in sorted(variants_table.items()):
        item_row = item_rows.get(variant_id)
        full_asset_id = item_row[3] if item_row and len(item_row) > 3 else None
        short_asset_id, primary_key = avatar_primary_key(full_asset_id)
        if primary_key and variant_id in default_variant_ids:
            primary_keys.add(primary_key)
        name = local_name(display_names, variant_id)
        occupation_id = variant_row[1]
        hero_id = variant_row[2]
        occupation_row = occupations_table.get(occupation_id)
        hero_row = heroes_table.get(hero_id)
        variants.append(
            {
                "variant_item_id": variant_id,
                **name,
                "hero_id": hero_id,
                "occupation_id": occupation_id,
                "skin_asset_id": variant_row[3],
                "masked_thumbnail_id": variant_row[4],
                "full_asset_id": full_asset_id,
                "short_asset_id": short_asset_id,
                "primary_key": primary_key,
                "item_type": item_row[2] if item_row and len(item_row) > 2 else None,
                "rarity": item_row[4] if item_row and len(item_row) > 4 else None,
                "hide_if_not_owned": item_row[7] if item_row and len(item_row) > 7 else None,
                "available_from": item_row[8] if item_row and len(item_row) > 8 else None,
                "available_to": item_row[9] if item_row and len(item_row) > 9 else None,
                "next_item_id": item_row[11] if item_row and len(item_row) > 11 else None,
                "is_default_hero_variant": bool(
                    hero_row
                    and occupation_row
                    and hero_row[1] == occupation_id
                    and occupation_row[2] == variant_id
                ),
                "is_default_occupation_variant": bool(occupation_row and occupation_row[2] == variant_id),
                "is_base_original_original": bool(
                    isinstance(full_asset_id, str) and full_asset_id.endswith("_Original_Original_Avatar")
                ),
                "tag_ids": variant_tag_ids.get(variant_id, []),
            }
        )

    exported = export_variant_avatars(catalog_rows_for_primary_keys(catalog, primary_keys))
    for row in variants:
        image = exported.get(row["primary_key"])
        row["image"] = image["output"] if image else None
        row["image_width"] = image["width"] if image else None
        row["image_height"] = image["height"] if image else None
        row["image_bundle"] = image["dependency_bundle"] if image else None

    variants_by_id = {row["variant_item_id"]: row for row in variants}
    heroes = []
    animals_core = []
    for hero_id, hero_row in sorted(heroes_table.items(), key=lambda item: item[1][3]):
        default_occupation_id = hero_row[1]
        default_occupation = occupations_table[default_occupation_id]
        default_variant_id = default_occupation[2]
        default_variant = variants_by_id.get(default_variant_id)
        tag_ids = [tag_id for tag_id in hero_tag_ids.get(hero_id, []) if tag_id in CORE_FEATURE_TAG_IDS]
        occupation_ids = hero_row[2]
        variant_ids = []
        for occupation_id in occupation_ids:
            occupation_row = occupations_table.get(occupation_id)
            if occupation_row:
                variant_ids.extend(occupation_row[3])
        heroes.append(
            {
                "hero_id": hero_id,
                "sort_order": hero_row[3],
                "name": (default_variant or {}).get("name", ""),
                "name_en": (default_variant or {}).get("name_en", ""),
                "default_occupation_id": default_occupation_id,
                "default_variant_item_id": default_variant_id,
                "default_image": (default_variant or {}).get("image"),
                "default_full_asset_id": (default_variant or {}).get("full_asset_id"),
                "tag_ids": tag_ids,
                "tags": [TAG_LABELS_ZH.get(tag_id, tag_id) for tag_id in tag_ids],
                "occupation_ids": occupation_ids,
                "occupation_count": len(occupation_ids),
                "variant_item_ids": variant_ids,
                "variant_count": len(variant_ids),
            }
        )
        animals_core.append(
            {
                "name": (default_variant or {}).get("name", ""),
                "image": (default_variant or {}).get("image"),
                "features": [TAG_LABELS_ZH.get(tag_id, tag_id) for tag_id in tag_ids],
                "feature_ids": tag_ids,
                "hero_id": hero_id,
                "variant_item_id": default_variant_id,
                "full_asset_id": (default_variant or {}).get("full_asset_id"),
                "name_en": (default_variant or {}).get("name_en", ""),
            }
        )

    occupations = []
    for occupation_id, row in sorted(occupations_table.items()):
        default_variant = variants_by_id.get(row[2])
        occupations.append(
            {
                "occupation_id": occupation_id,
                "hero_id": row[1],
                "default_variant_item_id": row[2],
                "name": (default_variant or {}).get("name", ""),
                "name_en": (default_variant or {}).get("name_en", ""),
                "variant_item_ids": row[3],
                "variant_count": len(row[3]),
            }
        )

    base_variants = [
        row for row in variants if row["is_default_hero_variant"] or row["is_base_original_original"]
    ]
    missing_images = [row["variant_item_id"] for row in variants if not row["image"]]

    return {
        "sources": {
            "game_config_tables": ["Hero", "Occupation", "Variant", "Item", "ItemTag"],
            "localization_bundle": "65f88cd7ee145a83ce36a3f779cd0d95.bundle",
            "avatar_catalog_prefix": "heoui-item-variant/",
        },
        "counts": {
            "heroes": len(heroes),
            "occupations": len(occupations),
            "variants": len(variants),
            "variants_with_image": sum(1 for row in variants if row["image"]),
            "default_hero_variants": sum(1 for row in variants if row["is_default_hero_variant"]),
            "base_original_original_variants": sum(1 for row in variants if row["is_base_original_original"]),
            "hero_tags": sum(1 for row in tags if row["item_type"] == 0),
            "variant_tags": sum(1 for row in tags if row["item_type"] == 7),
            "missing_variant_images": len(missing_images),
            "animals_core": len(animals_core),
            "animals_core_with_image": sum(1 for row in animals_core if row["image"]),
        },
        "tags": tags,
        "heroes": heroes,
        "occupations": occupations,
        "variants": variants,
        "base_variants": sorted(base_variants, key=lambda row: (row["hero_id"], row["variant_item_id"])),
        "animals_core": animals_core,
        "missing_variant_images": missing_images,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = build_index()
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    animals_core_minimal = [
        {
            "name": row["name"],
            "image": row["image"],
            "features": row["features"],
        }
        for row in data["animals_core"]
    ]
    ANIMALS_CORE_JSON.write_text(
        json.dumps(animals_core_minimal, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(data["counts"], ensure_ascii=False, indent=2))
    print(OUT_JSON)
    print(ANIMALS_CORE_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
