from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from build_party_animals_web_data import (
    EXTRACTED_DIR,
    MsgpackReader,
    extract_localization_terms,
    text_asset_bytes,
)


OUT_PATH = EXTRACTED_DIR / "achievement_map_index.json"
CORE_OUT_PATH = EXTRACTED_DIR / "achievement_map_index_core.json"
RESOURCES_MANIFEST_PATH = EXTRACTED_DIR / "resources_manifest.json"


def read_map16_count(reader: MsgpackReader) -> int:
    code = reader.read_byte()
    if 0x80 <= code <= 0x8F:
        return code & 0x0F
    if code == 0xDE:
        return reader.read_uint(2)
    if code == 0xDF:
        return reader.read_uint(4)
    raise ValueError(f"expected msgpack map header, got 0x{code:02x}")


def read_array_len(reader: MsgpackReader) -> int:
    code = reader.read_byte()
    if 0x90 <= code <= 0x9F:
        return code & 0x0F
    if code == 0xDC:
        return reader.read_uint(2)
    if code == 0xDD:
        return reader.read_uint(4)
    raise ValueError(f"expected msgpack array header, got 0x{code:02x}")


def read_lenient_array(reader: MsgpackReader) -> list[Any]:
    length = read_array_len(reader)
    row = []
    for _ in range(length):
        if reader.offset >= len(reader.data):
            break
        row.append(reader.unpack())
    return row


def decode_embedded_ascii(values: list[Any]) -> tuple[str, list[Any]]:
    if not values:
        return "", []
    if not isinstance(values[0], int) or values[0] >= 0:
        return "", values

    size = values[0] + 32
    chars: list[str] = []
    index = 1
    while len(chars) < size and index < len(values):
        value = values[index]
        if not isinstance(value, int) or not 0 <= value <= 127:
            break
        chars.append(chr(value))
        index += 1
    return "".join(chars), values[index:]


def read_achievement_rows() -> list[list[Any]]:
    reader = MsgpackReader(text_asset_bytes("Achievement"))
    count = read_map16_count(reader)
    current_key = reader.unpack()
    rows: list[list[Any]] = []

    for _ in range(count):
        row = read_lenient_array(reader)
        if row and isinstance(row[0], str) and row[0].startswith("ACV"):
            current_key = row[0]
        if not row and current_key:
            row = [current_key]

        if row and row[-1] == current_key:
            row = row[:-1]
        if row and isinstance(row[-1], str) and row[-1].startswith("ACV") and row[-1] != row[0]:
            current_key = row[-1]
            row = row[:-1]
        rows.append(row)

    return rows


def read_selectable_scene_rows() -> list[dict[str, Any]]:
    reader = MsgpackReader(text_asset_bytes("SelectableScene"))
    expected_count = read_map16_count(reader)
    values: list[Any] = []
    while reader.offset < len(reader.data):
        values.append(reader.unpack())

    scene_indices = [
        index
        for index, value in enumerate(values)
        if (
            isinstance(value, list)
            and len(value) >= 4
            and isinstance(value[0], int)
            and isinstance(value[1], str)
            and value[1].startswith("map-")
        )
    ]

    scenes: list[dict[str, Any]] = []
    for order, start_index in enumerate(scene_indices):
        end_index = scene_indices[order + 1] if order + 1 < len(scene_indices) else len(values)
        row_values = values[start_index:end_index]
        base = row_values[0]
        game_mode, remainder = decode_embedded_ascii(base[4:])
        scalar_tail = remainder + row_values[1:]
        scenes.append(
            {
                "scene_id": base[0],
                "bundle_name": base[1],
                "scene_name": base[2],
                "display_name": base[3],
                "game_mode": game_mode,
                "sort_order": scalar_tail[0] if scalar_tail and isinstance(scalar_tail[0], int) else None,
                "raw_tail": scalar_tail,
            }
        )

    if len(scenes) != expected_count:
        # The table declares selectable ids, while a few scalar-only values are chain markers.
        # Keep the parsed scene rows and expose the mismatch in counts for debugging.
        pass
    return scenes


def term_lookup(localization: dict[str, Any], group: str, prefix: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in localization[group]["terms"]:
        term = row.get("term")
        if not isinstance(term, str) or not term.startswith(prefix):
            continue
        result[term.removeprefix(prefix)] = {
            "term": term,
            "en": row.get("en") or "",
            "zh-CN": row.get("zh-CN") or "",
        }
    return result


def loading_map_lookup(localization: dict[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in localization.get("loading_maps", {}).get("terms", []):
        term = row.get("term")
        if not isinstance(term, str) or not term.startswith("LoadingMaps/LoadingMaps_"):
            continue
        scene_name = term.removeprefix("LoadingMaps/LoadingMaps_")
        if scene_name.endswith("_Description"):
            continue
        result[scene_name] = {
            "term": term,
            "en": row.get("en") or "",
            "zh-CN": row.get("zh-CN") or "",
        }
    return result


def load_achievement_icons() -> dict[str, dict[str, Any]]:
    if not RESOURCES_MANIFEST_PATH.exists():
        return {}
    manifest = json.loads(RESOURCES_MANIFEST_PATH.read_text(encoding="utf-8"))
    icons: dict[str, dict[str, Any]] = {}
    for row in manifest.get("resources", []):
        if row.get("group") != "achievements":
            continue
        leaf = str(row.get("primary_key", "")).rsplit("/", 1)[-1]
        icons[leaf] = row
    return icons


def extract_quoted_map_name(text: str) -> str | None:
    match = re.search(r"在猛兽卡丁车[「\"]([^」\"]+)[」\"]", text)
    if match:
        return f"猛兽卡丁车「{match.group(1)}」"
    match = re.search(r"在[「\"]([^」\"]+)[」\"]", text)
    if match:
        return match.group(1)
    match = re.search(r"[「\"]([^」\"]+)[」\"]", text)
    if match:
        return match.group(1)
    match = re.search(r"^In ([^,]+),", text)
    if match:
        return match.group(1)
    return None


def normalize_name(value: str) -> str:
    if any(ord(char) > 127 for char in value):
        return value.strip().lower()
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def format_condition(text: str, target_value: Any) -> str:
    if "[i2p_One]" in text:
        text = text.split("[i2p_One]", 1)[0]
    if target_value is not None:
        text = text.replace("{[PARAM]}", str(target_value))
    return text


ACTION_SCENE_ALIASES = {
    "MapArcade": "AE_001716_IntoTheGame_Original",
    "MapBalloon": "BalloonRunner",
    "MapBhole": "AE_001712_BlackHole_Original",
    "MapBlz": "Blizzard",
    "MapBrg": "HangingBridge",
    "MapEball": "ElectroBall",
    "MapGarfatArena": "GarfieldArena",
    "MapHockey": "AE_001715_IceHockey",
    "MapIce": "FloatingIce",
    "MapIchiban": "Ichiban",
    "MapLollipop": "101_LollipopFactory",
    "MapPlane": "BrokenArrow",
    "MapRugby": "Rugbiii",
    "MapShkwv": "AE_001713_ShockWave_Original",
    "MapSiege": "Siege",
    "MapSoccer": "AE_001743_PunchBall_Original",
    "MapSub": "RedOctober",
    "MapTrain": "102_SteamTrainRush",
    "MapWpark": "WaterPark",
    "QuickMatchKart": "AnimalKartDoubleDash",
    "Tutorial2": "TutorialNewPt2",
}

DERIVED_ACTION_SCENES = {
    "Tutorial": {
        "scene_id": None,
        "scene_name": "AE_002441_TutorialNewPt1_V2",
        "display_name": "Tutorial Pt1",
        "display_name_zh": "实验室",
        "bundle_name": "AE_002441_TutorialNewPt1_V2",
        "game_mode": "Tutorial",
        "source": "catalog_scene",
    },
    "Tutorial3": {
        "scene_id": None,
        "scene_name": "AE_001991_TutorialNewPt3_Original",
        "display_name": "Tutorial Pt3",
        "display_name_zh": "荒岛",
        "bundle_name": "AE_001991_TutorialNewPt3_Original",
        "game_mode": "Tutorial",
        "source": "catalog_scene",
    },
}


def build_scene_match_index(
    scenes: list[dict[str, Any]],
    action_terms: dict[str, dict[str, str]],
    loading_maps: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    names_by_en: dict[str, str] = {}
    for action in action_terms.values():
        zh_name = extract_quoted_map_name(action.get("zh-CN", ""))
        en_name = extract_quoted_map_name(action.get("en", ""))
        if zh_name and en_name:
            names_by_en.setdefault(normalize_name(en_name), zh_name)

    by_name: dict[str, dict[str, Any]] = {}
    for scene in scenes:
        map_term = loading_maps.get(str(scene["scene_name"]))
        zh_name = (map_term or {}).get("zh-CN") or names_by_en.get(normalize_name(str(scene["display_name"])))
        en_name = (map_term or {}).get("en") or scene["display_name"]
        enriched = {
            **scene,
            "display_name": en_name,
            "selectable_display_name": scene["display_name"],
            "display_name_zh": zh_name,
            "display_name_term": (map_term or {}).get("term"),
        }
        for candidate in [scene["display_name"], en_name, scene["scene_name"], zh_name]:
            if candidate:
                by_name[normalize_name(str(candidate))] = enriched
        if zh_name:
            by_name[zh_name] = enriched
    return [by_name[normalize_name(str(scene["display_name"]))] for scene in scenes], by_name


def find_scene_for_action(
    action_id: str, action: dict[str, str], scene_by_name: dict[str, dict[str, Any]]
) -> tuple[str | None, dict[str, Any] | None]:
    zh_hint = extract_quoted_map_name(action.get("zh-CN", ""))
    en_hint = extract_quoted_map_name(action.get("en", ""))
    for hint in [zh_hint, en_hint]:
        if not hint:
            continue
        scene = scene_by_name.get(hint) or scene_by_name.get(normalize_name(hint))
        if scene:
            return hint, scene
    for prefix, scene_name in ACTION_SCENE_ALIASES.items():
        if action_id.startswith(prefix):
            scene = scene_by_name.get(scene_name) or scene_by_name.get(normalize_name(scene_name))
            if scene:
                return zh_hint or en_hint, scene
    for prefix, scene in sorted(DERIVED_ACTION_SCENES.items(), key=lambda item: len(item[0]), reverse=True):
        if action_id.startswith(prefix):
            return zh_hint or en_hint or scene.get("display_name_zh"), scene
    return zh_hint or en_hint, None


def build_achievement_index() -> dict[str, Any]:
    localization = extract_localization_terms()
    title_terms = term_lookup(localization, "achievement_title", "Achievement/zTitle_")
    action_terms = term_lookup(localization, "achievement_action", "Achievement/zAction_")
    loading_maps = loading_map_lookup(localization)
    raw_scenes = read_selectable_scene_rows()
    scenes, scene_by_name = build_scene_match_index(raw_scenes, action_terms, loading_maps)
    icons = load_achievement_icons()
    achievements = read_achievement_rows()

    rows: list[dict[str, Any]] = []
    for row in achievements:
        if not row or not isinstance(row[0], str) or not row[0].startswith("ACV"):
            continue
        ach_id = row[0]
        title = title_terms.get(ach_id, {})
        action_id = row[2] if len(row) > 2 else ""
        action = action_terms.get(str(action_id), {})
        target_value = row[3] if len(row) > 3 else None
        icon_asset_id = row[5] if len(row) > 5 else ""
        icon = icons.get(str(icon_asset_id)) or icons.get(f"UI_Achievements_{ach_id}")
        scene_hint, scene = find_scene_for_action(str(action_id), action, scene_by_name)
        condition = format_condition(action.get("zh-CN") or action.get("en") or "", target_value)
        condition_en = format_condition(action.get("en") or "", target_value)

        rows.append(
            {
                "achievement_id": ach_id,
                "numeric_id": row[1] if len(row) > 1 else None,
                "title": title.get("zh-CN") or title.get("en") or "",
                "title_en": title.get("en") or "",
                "title_term": title.get("term"),
                "action_id": action_id,
                "condition": condition,
                "condition_en": condition_en,
                "action_term": action.get("term"),
                "target_value": target_value,
                "reward_score": row[4] if len(row) > 4 else None,
                "icon_asset_id": icon_asset_id,
                "icon": icon.get("output") if icon else None,
                "icon_primary_key": icon.get("primary_key") if icon else None,
                "related_achievements": row[6] if len(row) > 6 and isinstance(row[6], list) else [],
                "reward_items": row[7] if len(row) > 7 and isinstance(row[7], list) else [],
                "scene_hint": scene_hint,
                "scene_id": scene.get("scene_id") if scene else None,
                "scene_name": scene.get("scene_name") if scene else None,
                "scene_display_name": scene.get("display_name") if scene else None,
                "scene_display_name_zh": (scene.get("display_name_zh") if scene else None) or scene_hint,
                "scene": scene,
                "is_map_achievement": bool(scene_hint),
                "scene_match": (
                    "derived"
                    if scene and scene.get("source") == "catalog_scene"
                    else ("matched" if scene else ("hint_only" if scene_hint else "none"))
                ),
                "raw": row,
            }
        )

    return {
        "counts": {
            "achievements": len(rows),
            "achievements_with_title": sum(1 for row in rows if row["title"]),
            "achievements_with_condition": sum(1 for row in rows if row["condition"]),
            "achievements_with_icon": sum(1 for row in rows if row["icon"]),
            "map_achievement_hints": sum(1 for row in rows if row["is_map_achievement"]),
            "achievements_matched_to_scene_or_derived_scene": sum(
                1 for row in rows if row["scene_match"] in {"matched", "derived"}
            ),
            "scenes": len(scenes),
            "raw_selectable_scene_declared_count": read_map16_count(MsgpackReader(text_asset_bytes("SelectableScene"))),
            "loading_map_terms": len(loading_maps),
            "scenes_with_loading_map_name": sum(1 for scene in scenes if scene.get("display_name_term")),
        },
        "scenes": scenes,
        "achievements": rows,
        "unmatched_map_hints": sorted(
            {
                str(row["scene_hint"])
                for row in rows
                if row["scene_hint"] and row["scene_match"] not in {"matched", "derived"}
            }
        ),
        "extra_achievement_icons": sorted(
            set(icons) - {str(row["icon_asset_id"]) for row in rows if row["icon_asset_id"]}
        ),
    }


def build_core_index(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "counts": data["counts"],
        "maps": [
            {
                "scene_id": scene["scene_id"],
                "scene_name": scene["scene_name"],
                "display_name": scene["display_name"],
                "display_name_zh": scene.get("display_name_zh"),
                "bundle_name": scene["bundle_name"],
                "game_mode": scene.get("game_mode"),
            }
            for scene in data["scenes"]
        ],
        "achievements": [
            {
                "achievement_id": row["achievement_id"],
                "title": row["title"],
                "condition": row["condition"],
                "icon": row["icon"],
                "icon_asset_id": row["icon_asset_id"],
                "scene_id": row["scene_id"],
                "scene_name": row["scene_name"],
                "map_name": row["scene_display_name_zh"],
                "map_name_en": row["scene_display_name"],
                "scene_match": row["scene_match"],
            }
            for row in data["achievements"]
        ],
    }


def main() -> int:
    data = build_achievement_index()
    core = build_core_index(data)
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CORE_OUT_PATH.write_text(json.dumps(core, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data["counts"], ensure_ascii=False, indent=2))
    print(OUT_PATH)
    print(CORE_OUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
