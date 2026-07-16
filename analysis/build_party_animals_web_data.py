from __future__ import annotations

import json
import re
import shutil
import struct
import sys
from pathlib import Path
from typing import Any

from collections import defaultdict

import UnityPy

sys.path.insert(0, str(Path(__file__).resolve().parent))

from decrypt_party_animals import DEFAULT_GAME_DIR, decrypt_bundles
from extract_party_animals_web_assets import (
    CATALOG_PATH,
    DECRYPTED_BUNDLE_DIR,
    EXTRACTED_DIR,
    WEB_ACHIEVEMENTS_DIR,
    catalog_asset,
    catalog_entry_rows,
    parse_catalog_entries,
    parse_catalog_keys,
    recover_unity_binary_text,
    resolve_dependency_bundles,
    safe_filename,
)


LOCALIZATION_PRIMARY_KEYS = {
    "inventory_item": "config data-hotupdate/I2LanguagesFull_Inventory_Item",
    "achievement_title": "config data-hotupdate/I2LanguagesFull_Achievement_Title",
    "achievement_action": "config data-hotupdate/I2LanguagesFull_Achievement_Action",
    "loading_maps": "config data-hotupdate/I2LanguagesFull_LoadingMaps",
    "perk": "config data-hotupdate/I2LanguagesFull_Perk",
}
ZH_CN = "Chinese (Simplified)"
VARIANT_AVATAR_DIR = EXTRACTED_DIR / "variant_avatars"
FORCE_BUNDLE_REFRESH = False
_REFRESHED_BUNDLES: set[str] = set()


def set_bundle_refresh_mode(enabled: bool) -> None:
    global FORCE_BUNDLE_REFRESH
    FORCE_BUNDLE_REFRESH = enabled
    _REFRESHED_BUNDLES.clear()


def read_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def localization_dependency_report(catalog: dict[str, Any]) -> dict[str, Any]:
    assets = {}
    for group, key in LOCALIZATION_PRIMARY_KEYS.items():
        asset = catalog_asset(catalog, key, "I2.Loc.LanguageSourceData")
        assets[group] = {
            "primary_key": key,
            "asset_id": asset["asset_id"],
            "resource_type": asset["resource_type"],
            "dependency_key": asset["dependency_key"],
            "dependency_bundles": asset.get("dependency_bundles", []),
            "dependency_bundle": asset.get("dependency_bundle"),
        }
    return {
        "assets": assets,
        "bundles": sorted({asset["dependency_bundle"] for asset in assets.values() if asset["dependency_bundle"]}),
    }


def ensure_bundle(bundle: str) -> None:
    out_path = DECRYPTED_BUNDLE_DIR / bundle
    needs_forced_refresh = FORCE_BUNDLE_REFRESH and bundle not in _REFRESHED_BUNDLES
    if not needs_forced_refresh and out_path.exists() and out_path.read_bytes().startswith(b"UnityFS"):
        return
    decrypt_bundles(DEFAULT_GAME_DIR, Path("analysis/decrypted"), CATALOG_PATH, 0, bundle.removesuffix(".bundle"))
    _REFRESHED_BUNDLES.add(bundle)


def extract_localization_terms() -> dict[str, Any]:
    catalog = read_catalog()
    result: dict[str, Any] = {}
    for group, primary_key in LOCALIZATION_PRIMARY_KEYS.items():
        asset = catalog_asset(catalog, primary_key, "I2.Loc.LanguageSourceData")
        bundle = asset.get("dependency_bundle")
        if not isinstance(bundle, str):
            raise ValueError(f"cannot resolve localization bundle for {primary_key}")
        ensure_bundle(bundle)
        env = UnityPy.load(str(DECRYPTED_BUNDLE_DIR / bundle))
        tree = env.container.container_dict[asset["asset_id"]].read_typetree()
        source = tree["mSource"]
        languages = [item["Name"] for item in source["mLanguages"]]
        zh_index = languages.index(ZH_CN)
        terms = []
        for term in source["mTerms"]:
            values = term.get("Languages") or []
            terms.append(
                {
                    "term": term.get("Term"),
                    "en": values[0] if len(values) > 0 else "",
                    "zh-CN": values[zh_index] if len(values) > zh_index else "",
                }
            )
        result[group] = {
            "asset_id": asset["asset_id"],
            "resource_type": asset["resource_type"],
            "asset_name": tree.get("m_Name"),
            "language_index": zh_index,
            "languages": languages,
            "count": len(terms),
            "bundle": bundle,
            "terms": terms,
        }
    return result


class MsgpackReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.offset = 0

    def read_byte(self) -> int:
        value = self.data[self.offset]
        self.offset += 1
        return value

    def read(self, size: int) -> bytes:
        value = self.data[self.offset : self.offset + size]
        self.offset += size
        return value

    def read_uint(self, size: int) -> int:
        return int.from_bytes(self.read(size), "big", signed=False)

    def read_int(self, size: int) -> int:
        return int.from_bytes(self.read(size), "big", signed=True)

    def unpack(self) -> Any:
        code = self.read_byte()
        if code <= 0x7F:
            return code
        if code >= 0xE0:
            return code - 0x100
        if 0xA0 <= code <= 0xBF:
            return self.read(code & 0x1F).decode("utf-8", errors="surrogateescape")
        if 0x90 <= code <= 0x9F:
            return [self.unpack() for _ in range(code & 0x0F)]
        if 0x80 <= code <= 0x8F:
            return [(self.unpack(), self.unpack()) for _ in range(code & 0x0F)]
        if code == 0xC0:
            return None
        if code == 0xC2:
            return False
        if code == 0xC3:
            return True
        if code == 0xC4:
            return self.read(self.read_uint(1))
        if code == 0xC5:
            return self.read(self.read_uint(2))
        if code == 0xC6:
            return self.read(self.read_uint(4))
        if code == 0xC7:
            size = self.read_uint(1)
            ext_type = self.read_int(1)
            return {"__ext_type__": ext_type, "data": self.read(size)}
        if code == 0xC8:
            size = self.read_uint(2)
            ext_type = self.read_int(1)
            return {"__ext_type__": ext_type, "data": self.read(size)}
        if code == 0xC9:
            size = self.read_uint(4)
            ext_type = self.read_int(1)
            return {"__ext_type__": ext_type, "data": self.read(size)}
        if code == 0xCA:
            return struct.unpack(">f", self.read(4))[0]
        if code == 0xCB:
            return struct.unpack(">d", self.read(8))[0]
        if code == 0xCC:
            return self.read_uint(1)
        if code == 0xCD:
            return self.read_uint(2)
        if code == 0xCE:
            return self.read_uint(4)
        if code == 0xCF:
            return self.read_uint(8)
        if code == 0xD0:
            return self.read_int(1)
        if code == 0xD1:
            return self.read_int(2)
        if code == 0xD2:
            return self.read_int(4)
        if code == 0xD3:
            return self.read_int(8)
        if 0xD4 <= code <= 0xD8:
            sizes = {0xD4: 1, 0xD5: 2, 0xD6: 4, 0xD7: 8, 0xD8: 16}
            ext_type = self.read_int(1)
            return {"__ext_type__": ext_type, "data": self.read(sizes[code])}
        if code == 0xD9:
            return self.read(self.read_uint(1)).decode("utf-8", errors="surrogateescape")
        if code == 0xDA:
            return self.read(self.read_uint(2)).decode("utf-8", errors="surrogateescape")
        if code == 0xDB:
            return self.read(self.read_uint(4)).decode("utf-8", errors="surrogateescape")
        if code == 0xDC:
            return [self.unpack() for _ in range(self.read_uint(2))]
        if code == 0xDD:
            return [self.unpack() for _ in range(self.read_uint(4))]
        if code == 0xDE:
            return [(self.unpack(), self.unpack()) for _ in range(self.read_uint(2))]
        if code == 0xDF:
            return [(self.unpack(), self.unpack()) for _ in range(self.read_uint(4))]
        raise ValueError(f"unsupported msgpack code 0x{code:02x} at {self.offset - 1}")


def text_asset_bytes(name: str) -> bytes:
    catalog = read_catalog()
    asset = catalog_asset(catalog, f"config data binary/{name}", "UnityEngine.TextAsset")
    bundle = asset.get("dependency_bundle")
    if not isinstance(bundle, str):
        raise ValueError(f"cannot resolve text asset bundle for {name}")
    ensure_bundle(bundle)
    env = UnityPy.load(str(DECRYPTED_BUNDLE_DIR / bundle))
    obj = env.container.container_dict[asset["asset_id"]].read()
    return recover_unity_binary_text(obj.m_Script)


def read_chained_table(name: str) -> list[list[Any]]:
    rows: list[list[Any]] = []
    reader = MsgpackReader(text_asset_bytes(name))
    roots = []
    while reader.offset < len(reader.data):
        roots.append(reader.unpack())

    def walk(value: Any) -> None:
        if isinstance(value, tuple):
            for child in value:
                walk(child)
        elif isinstance(value, list):
            if value and isinstance(value[0], str):
                rows.append(value)
            for child in value:
                walk(child)
        elif isinstance(value, dict):
            if isinstance(value.get("__ext_type__"), int):
                return
            for key, child in value.items():
                walk(key)
                walk(child)

    for root in roots:
        walk(root)
    deduped: list[list[Any]] = []
    seen: set[str] = set()
    for row in rows:
        row_id = row[0]
        if isinstance(row_id, str) and row_id not in seen:
            seen.add(row_id)
            deduped.append(row)
    return deduped


def term_lookup(localization: dict[str, Any], group: str, suffix: str) -> dict[str, dict[str, str]]:
    result = {}
    for row in localization[group]["terms"]:
        term = row["term"]
        if not isinstance(term, str) or not term.endswith(suffix):
            continue
        item_id = term.rsplit("/", 1)[-1].removesuffix(suffix)
        item_id = item_id.removeprefix("zItem_").removeprefix("zTitle_").removeprefix("zAction_")
        result[item_id] = {"term": term, "en": row["en"], "zh-CN": row["zh-CN"]}
    return result


def build_portraits(localization: dict[str, Any], resources: dict[str, Any]) -> list[dict[str, Any]]:
    account_rows = read_chained_table("AccountPortrait")
    display_names = term_lookup(localization, "inventory_item", "_DisplayName")
    by_leaf = {
        row["primary_key"].rsplit("/", 1)[-1]: row
        for row in resources["resources"]
        if row["group"] == "portraits"
    }
    portraits = []
    for row in account_rows:
        item_id, portrait_asset, sorting_order, hero_name = row[:4]
        loc = display_names.get(item_id)
        profile_asset = portrait_asset.removesuffix("_Portrait") + "_Profile"
        image = by_leaf.get(profile_asset)
        portraits.append(
            {
                "item_id": item_id,
                "hero_name": hero_name,
                "display_name": (loc or {}).get("zh-CN") or (loc or {}).get("en") or "",
                "display_name_en": (loc or {}).get("en") or "",
                "display_name_term": (loc or {}).get("term"),
                "portrait_asset_id": portrait_asset,
                "profile_asset_id": profile_asset,
                "sorting_order": sorting_order,
                "image": image["output"] if image else None,
                "primary_key": image["primary_key"] if image else None,
            }
        )
    return sorted(portraits, key=lambda item: item["sorting_order"])


def build_achievements(localization: dict[str, Any], resources: dict[str, Any]) -> list[dict[str, Any]]:
    title_by_id = term_lookup(localization, "achievement_title", "")
    action_by_id = term_lookup(localization, "achievement_action", "")
    achievements = read_chained_table("Achievement")
    by_leaf = {
        row["primary_key"].rsplit("/", 1)[-1]: row
        for row in resources["resources"]
        if row["group"] == "achievements"
    }
    rows = []
    for row in achievements:
        if not isinstance(row[0], str) or not row[0].startswith("ACV"):
            continue
        ach_id = row[0]
        icon_asset = row[3] if len(row) > 3 else ""
        title = title_by_id.get(f"zTitle_{ach_id}", {})
        action_key = row[2] if len(row) > 2 else ""
        action = action_by_id.get(f"zAction_{action_key}", {})
        image = by_leaf.get(icon_asset)
        rows.append(
            {
                "achievement_id": ach_id,
                "title": title.get("zh-CN") or title.get("en") or "",
                "title_en": title.get("en") or "",
                "title_term": title.get("term"),
                "action_key": action_key,
                "action": action.get("zh-CN") or action.get("en") or "",
                "action_en": action.get("en") or "",
                "action_term": action.get("term"),
                "icon_asset_id": icon_asset,
                "image": image["output"] if image else None,
                "primary_key": image["primary_key"] if image else None,
                "raw": row,
            }
        )
    return rows


def build_perks(localization: dict[str, Any], resources: dict[str, Any]) -> list[dict[str, Any]]:
    icon_by_stem = {
        row["primary_key"].rsplit("/", 1)[-1].removesuffix("_PerkIcon"): row
        for row in resources["resources"]
        if row["group"] == "perks" and row["primary_key"].endswith("_PerkIcon")
    }
    terms = localization["perk"]["terms"]
    by_perk: dict[str, dict[str, Any]] = {}
    pattern = re.compile(r"^Perk/(?P<key>.+)_(?P<kind>Title|Desc)_Lv(?P<level>[12])$")
    for row in terms:
        match = pattern.match(row["term"] or "")
        if not match:
            continue
        perk_key = match.group("key")
        kind = match.group("kind").lower()
        level = match.group("level")
        entry = by_perk.setdefault(perk_key, {"perk_key": perk_key, "levels": {}})
        level_entry = entry["levels"].setdefault(level, {})
        level_entry[kind] = row["zh-CN"] or row["en"]
        level_entry[f"{kind}_en"] = row["en"]
        level_entry[f"{kind}_term"] = row["term"]
    rows = []
    for index, entry in enumerate(sorted(by_perk.values(), key=lambda item: item["perk_key"])):
        icon = icon_by_stem.get(entry["perk_key"])
        rows.append(
            {
                **entry,
                "icon_asset_id": f"{entry['perk_key']}_PerkIcon" if icon else None,
                "image": icon["output"] if icon else None,
                "primary_key": icon["primary_key"] if icon else None,
                "icon_match": "exact_stem" if icon else "missing",
                "index": index,
            }
        )
    return rows


def catalog_rows_for_primary_keys(catalog: dict[str, Any], primary_keys: set[str]) -> list[dict[str, Any]]:
    rows = []
    for row in catalog_entry_rows(catalog):
        if row["primary_key"] not in primary_keys or row["resource_type"] != "UnityEngine.Sprite":
            continue
        bundles = resolve_dependency_bundles(catalog, row.get("dependency_key"))
        rows.append(
            {
                **row,
                "dependency_bundles": bundles,
                "dependency_bundle": bundles[0] if bundles else None,
            }
        )
    return rows


def export_variant_avatars(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_bundle: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        bundle = row["dependency_bundle"]
        if isinstance(bundle, str):
            by_bundle[bundle].append(row)

    exported: dict[str, dict[str, Any]] = {}
    for bundle, bundle_rows in sorted(by_bundle.items()):
        ensure_bundle(bundle)
        env = UnityPy.load(str(DECRYPTED_BUNDLE_DIR / bundle))
        containers = env.container.container_dict
        for row in bundle_rows:
            ptr = containers.get(row["asset_id"])
            if ptr is None:
                continue
            sprite = ptr.read()
            image = sprite.image
            leaf = row["primary_key"].rsplit("/", 1)[-1]
            out_path = VARIANT_AVATAR_DIR / f"{safe_filename(leaf)}.png"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(out_path)
            exported[row["primary_key"]] = {
                **row,
                "output": str(out_path.as_posix()),
                "width": image.width,
                "height": image.height,
            }
    return exported


def build_heroes(localization: dict[str, Any], catalog: dict[str, Any]) -> list[dict[str, Any]]:
    import msgpack

    hero = msgpack.unpackb(text_asset_bytes("Hero"), raw=False, strict_map_key=False)
    occupation = msgpack.unpackb(text_asset_bytes("Occupation"), raw=False, strict_map_key=False)
    item = {row[0]: row for row in read_chained_table("Item") if row and isinstance(row[0], str)}
    display_names = term_lookup(localization, "inventory_item", "_DisplayName")

    heroes = []
    primary_keys = set()

    def add_hero(
        *,
        hero_id: str | None,
        occupation_id: str | None,
        variant_id: str,
        sort_order: int,
        source: str,
    ) -> None:
        item_row = item.get(variant_id)
        if not item_row:
            return
        full_asset = item_row[3]
        match = re.match(r"(AC_\d+)", full_asset or "")
        short_asset = f"{match.group(1)}_Avatar" if match else None
        primary_key = f"heoui-item-variant/{short_asset}" if short_asset else None
        if primary_key:
            primary_keys.add(primary_key)
        loc = display_names.get(variant_id, {})
        heroes.append(
            {
                "hero_id": hero_id,
                "occupation_id": occupation_id,
                "variant_item_id": variant_id,
                "sort_order": sort_order,
                "source": source,
                "name": loc.get("zh-CN") or loc.get("en") or "",
                "name_en": loc.get("en") or "",
                "name_term": loc.get("term"),
                "full_asset_id": full_asset,
                "short_asset_id": short_asset,
                "primary_key": primary_key,
            }
        )

    for hero_id, hero_row in hero.items():
        occupation_id = hero_row[1]
        variant_id = occupation[occupation_id][2]
        add_hero(
            hero_id=hero_id,
            occupation_id=occupation_id,
            variant_id=variant_id,
            sort_order=hero_row[3],
            source="hero_default",
        )

    existing_names = {row["name"] for row in heroes if row["name"]}
    site_names = {path.stem for path in Path("images/animals").glob("*.png")}
    next_order = max((row["sort_order"] for row in heroes), default=0) + 1
    display_by_zh = {
        value["zh-CN"]: key
        for key, value in display_names.items()
        if value.get("zh-CN") and key.startswith("VA")
    }
    for name in sorted(site_names - existing_names):
        variant_id = display_by_zh.get(name)
        if not variant_id:
            continue
        add_hero(
            hero_id=None,
            occupation_id=None,
            variant_id=variant_id,
            sort_order=next_order,
            source="site_name_lookup",
        )
        next_order += 1

    exported = export_variant_avatars(catalog_rows_for_primary_keys(catalog, primary_keys))
    for hero_row in heroes:
        image = exported.get(hero_row["primary_key"])
        hero_row["image"] = image["output"] if image else None
        hero_row["image_width"] = image["width"] if image else None
        hero_row["image_height"] = image["height"] if image else None
        hero_row["image_bundle"] = image["dependency_bundle"] if image else None
    deduped = {}
    for row in heroes:
        deduped[row["variant_item_id"]] = row
    return sorted(deduped.values(), key=lambda item: item["sort_order"])


def copy_achievement_images(achievements: list[dict[str, Any]]) -> dict[str, Any]:
    WEB_ACHIEVEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    missing = []
    for achievement in achievements:
        if not achievement["image"] or not achievement["title"]:
            missing.append(achievement["achievement_id"])
            continue
        source = Path(achievement["image"])
        target = WEB_ACHIEVEMENTS_DIR / f"{safe_filename(achievement['title'])}.jpg"
        shutil.copyfile(source, target)
        copied.append(str(target.as_posix()))
    return {"copied_count": len(copied), "missing_count": len(missing), "missing": missing}


def main() -> int:
    catalog = read_catalog()
    resources_path = EXTRACTED_DIR / "resources_manifest.json"
    resources = json.loads(resources_path.read_text(encoding="utf-8"))
    localization = extract_localization_terms()
    portraits = build_portraits(localization, resources)
    heroes = build_heroes(localization, catalog)
    try:
        achievements = build_achievements(localization, resources)
    except Exception as exc:
        achievements = []
        achievements_error = repr(exc)
    else:
        achievements_error = None
    perks = build_perks(localization, resources)
    output = {
        "sources": {
            "catalog": str(CATALOG_PATH.as_posix()),
            "localization_dependency": localization_dependency_report(catalog),
            "resources_manifest": str(resources_path.as_posix()),
        },
        "counts": {
            "portraits": len(portraits),
            "heroes": len(heroes),
            "heroes_with_image": sum(1 for item in heroes if item["image"]),
            "achievements": len(achievements),
            "perks": len(perks),
            "perks_with_exact_icon": sum(1 for item in perks if item["icon_match"] == "exact_stem"),
        },
        "errors": {"achievements": achievements_error},
        "localization": {
            key: {k: value[k] for k in ["asset_id", "asset_name", "language_index", "languages", "count"]}
            for key, value in localization.items()
        },
        "portraits": portraits,
        "heroes": heroes,
        "achievements": achievements,
        "perks": perks,
        "site_copy": {"achievements": copy_achievement_images(achievements)},
    }
    out_path = EXTRACTED_DIR / "web_assets_data.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    terms_path = EXTRACTED_DIR / "localization_full_terms.json"
    terms_path.write_text(json.dumps(localization, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["counts"], ensure_ascii=False, indent=2))
    print(json.dumps(output["site_copy"], ensure_ascii=False, indent=2))
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
