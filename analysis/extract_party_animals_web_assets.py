from __future__ import annotations

import base64
import json
import re
import shutil
import struct
from collections import defaultdict
from pathlib import Path
from typing import Any

import msgpack
import UnityPy
from PIL import Image

from decrypt_party_animals import DEFAULT_GAME_DIR, decrypt_bundles


CATALOG_PATH = Path("analysis/decrypted/aa/catalog.json")
DECRYPTED_BUNDLE_DIR = Path("analysis/decrypted/aa/StandaloneWindows64")
EXTRACTED_DIR = Path("analysis/extracted")
WEB_ANIMALS_DIR = Path("images/animals")
WEB_ACHIEVEMENTS_DIR = Path("images/achievements")

TARGET_GROUPS = {
    "portraits": {
        "prefix": "heoui-item-portrait/",
        "out": EXTRACTED_DIR / "portraits",
    },
    "portrait_alpha": {
        "prefix": "heoui-item-portrait-alpha/",
        "out": EXTRACTED_DIR / "portrait_alpha",
    },
    "achievements": {
        "prefix": "heoui-thumb-achv/",
        "out": EXTRACTED_DIR / "achievements",
    },
    "perks": {
        "prefix": "heoui-thumb-perk/",
        "out": EXTRACTED_DIR / "perks",
    },
}
CONFIG_BUNDLE_FALLBACK = "6211be75bb61a3367a285a634b14207d.bundle"
ACCOUNT_PORTRAIT_PRIMARY_KEY = "config data binary/AccountPortrait"


def parse_catalog_keys(encoded: str) -> list[str | int]:
    data = base64.b64decode(encoded)
    count = struct.unpack_from("<i", data, 0)[0]
    offset = 4
    keys: list[str | int] = []
    for index in range(count):
        value_type = data[offset]
        offset += 1
        if value_type == 0:
            length = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            raw = data[offset : offset + length]
            offset += length
            if raw.endswith(b"\0"):
                raw = raw[:-1]
            keys.append(raw.decode("utf-8", errors="replace"))
        elif value_type == 4:
            keys.append(struct.unpack_from("<I", data, offset)[0])
            offset += 4
        else:
            raise ValueError(f"unsupported catalog key type {value_type} at key {index}")
    if offset != len(data):
        raise ValueError(f"catalog key data not fully consumed: {offset} != {len(data)}")
    return keys


def parse_catalog_entries(encoded: str) -> list[tuple[int, int, int, int, int, int, int]]:
    data = base64.b64decode(encoded)
    count = struct.unpack_from("<i", data, 0)[0]
    expected = 4 + count * 28
    if expected != len(data):
        raise ValueError(f"catalog entry data size mismatch: {expected} != {len(data)}")
    return [struct.unpack_from("<7i", data, 4 + index * 28) for index in range(count)]


def catalog_key_offsets(encoded: str) -> tuple[list[str | int], list[int]]:
    data = base64.b64decode(encoded)
    count = struct.unpack_from("<i", data, 0)[0]
    offset = 4
    keys: list[str | int] = []
    offsets: list[int] = []
    for index in range(count):
        offsets.append(offset)
        value_type = data[offset]
        offset += 1
        if value_type == 0:
            length = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            raw = data[offset : offset + length]
            offset += length
            if raw.endswith(b"\0"):
                raw = raw[:-1]
            keys.append(raw.decode("utf-8", errors="replace"))
        elif value_type == 4:
            keys.append(struct.unpack_from("<I", data, offset)[0])
            offset += 4
        else:
            raise ValueError(f"unsupported catalog key type {value_type} at key {index}")
    if offset != len(data):
        raise ValueError(f"catalog key data not fully consumed: {offset} != {len(data)}")
    return keys, offsets


def parse_catalog_buckets(encoded: str) -> dict[int, list[int]]:
    raw = base64.b64decode(encoded)
    count = struct.unpack_from("<i", raw, 0)[0]
    offset = 4
    buckets: dict[int, list[int]] = {}
    for _ in range(count):
        key_offset = struct.unpack_from("<i", raw, offset)[0]
        item_count = struct.unpack_from("<i", raw, offset + 4)[0]
        offset += 8
        buckets[key_offset] = [
            struct.unpack_from("<i", raw, offset + index * 4)[0]
            for index in range(item_count)
        ]
        offset += item_count * 4
    if offset != len(raw):
        raise ValueError(f"catalog bucket data not fully consumed: {offset} != {len(raw)}")
    return buckets


def catalog_entry_rows(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    keys = parse_catalog_keys(catalog["m_KeyDataString"])
    entries = parse_catalog_entries(catalog["m_EntryDataString"])
    internal_ids = catalog["m_InternalIds"]
    provider_ids = catalog["m_ProviderIds"]
    resource_types = [item["m_ClassName"] for item in catalog["m_resourceTypes"]]
    rows = []
    for entry_index, entry in enumerate(entries):
        internal_index, provider_index, dependency_index, _, data_index, primary_index, type_index = entry
        rows.append(
            {
                "entry_index": entry_index,
                "primary_key": keys[primary_index] if 0 <= primary_index < len(keys) else None,
                "asset_id": internal_ids[internal_index] if 0 <= internal_index < len(internal_ids) else None,
                "dependency_key": keys[dependency_index] if 0 <= dependency_index < len(keys) else None,
                "provider": provider_ids[provider_index] if 0 <= provider_index < len(provider_ids) else None,
                "data_index": data_index,
                "resource_type": resource_types[type_index] if 0 <= type_index < len(resource_types) else None,
            }
        )
    return rows


def catalog_rows_for_primary(catalog: dict[str, Any], primary_key: str) -> list[dict[str, Any]]:
    return [row for row in catalog_entry_rows(catalog) if row["primary_key"] == primary_key]


def resolve_dependency_bundles(catalog: dict[str, Any], dependency_key: str | int | None) -> list[str]:
    if isinstance(dependency_key, str) and dependency_key.endswith(".bundle"):
        return [dependency_key]
    if dependency_key is None:
        return []

    keys, offsets = catalog_key_offsets(catalog["m_KeyDataString"])
    if dependency_key not in keys:
        return []
    dependency_offset = offsets[keys.index(dependency_key)]
    bucket_entries = parse_catalog_buckets(catalog["m_BucketDataString"]).get(dependency_offset, [])
    rows = catalog_entry_rows(catalog)
    bundles: list[str] = []
    for entry_index in bucket_entries:
        if not 0 <= entry_index < len(rows):
            continue
        row = rows[entry_index]
        primary_key = row.get("primary_key")
        if (
            row.get("resource_type") == "UnityEngine.ResourceManagement.ResourceProviders.IAssetBundleResource"
            and isinstance(primary_key, str)
            and primary_key.endswith(".bundle")
        ):
            bundles.append(primary_key)
    return bundles


def catalog_asset(catalog: dict[str, Any], primary_key: str, resource_type: str | None = None) -> dict[str, Any]:
    matches = catalog_rows_for_primary(catalog, primary_key)
    if resource_type:
        matches = [row for row in matches if row.get("resource_type") == resource_type]
    if not matches:
        detail = f" with resource type {resource_type}" if resource_type else ""
        raise KeyError(f"catalog primary key not found: {primary_key}{detail}")
    row = matches[0]
    bundles = resolve_dependency_bundles(catalog, row.get("dependency_key"))
    return {**row, "dependency_bundles": bundles, "dependency_bundle": bundles[0] if bundles else None}


def config_bundle_for(catalog: dict[str, Any], table_name: str) -> str:
    asset = catalog_asset(catalog, f"config data binary/{table_name}", "UnityEngine.TextAsset")
    bundle = asset.get("dependency_bundle")
    if not isinstance(bundle, str):
        raise ValueError(f"cannot resolve config bundle for {table_name}")
    return bundle


def read_app_data() -> dict[str, list[str]]:
    text = Path("app.js").read_text(encoding="utf-8")
    animals_block = re.search(r"animals:\s*\{.*?items:\s*\[(.*?)\]\s*\}\s*,\s*achievements:", text, re.S)
    achievements_block = re.search(r"achievements:\s*\{.*?items:\s*\[(.*?)\]\s*\}\s*\}\s*;", text, re.S)
    return {
        "animals": re.findall(r"name:\s*'([^']+)'", animals_block.group(1) if animals_block else ""),
        "achievements": re.findall(r"name:\s*'([^']+)'", achievements_block.group(1) if achievements_block else ""),
    }


def safe_filename(value: str) -> str:
    value = value.replace("\\", "_").replace("/", "_")
    return re.sub(r'[<>:"|?*\x00-\x1f]', "_", value)


def build_catalog_manifest(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    keys = parse_catalog_keys(catalog["m_KeyDataString"])
    entries = parse_catalog_entries(catalog["m_EntryDataString"])
    internal_ids = catalog["m_InternalIds"]
    provider_ids = catalog["m_ProviderIds"]
    resource_types = [item["m_ClassName"] for item in catalog["m_resourceTypes"]]

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for entry_index, entry in enumerate(entries):
        internal_index, provider_index, dependency_index, _, data_index, primary_index, type_index = entry
        primary_key = keys[primary_index] if 0 <= primary_index < len(keys) else None
        if not isinstance(primary_key, str):
            continue

        group_name = None
        for name, config in TARGET_GROUPS.items():
            if primary_key.startswith(config["prefix"]):
                group_name = name
                break
        if group_name is None:
            continue

        resource_type = resource_types[type_index] if 0 <= type_index < len(resource_types) else str(type_index)
        if resource_type not in {"UnityEngine.Sprite", "UnityEngine.Texture2D"}:
            continue

        internal_id = internal_ids[internal_index] if 0 <= internal_index < len(internal_ids) else str(internal_index)
        dependency_key = keys[dependency_index] if 0 <= dependency_index < len(keys) else None
        dependency_bundles = resolve_dependency_bundles(catalog, dependency_key)
        provider_id = provider_ids[provider_index] if 0 <= provider_index < len(provider_ids) else str(provider_index)
        key = (primary_key, internal_id, resource_type)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "group": group_name,
                "entry_index": entry_index,
                "primary_key": primary_key,
                "asset_id": internal_id,
                "dependency_key": dependency_key,
                "dependency_bundle": dependency_bundles[0] if dependency_bundles else None,
                "dependency_bundles": dependency_bundles,
                "provider": provider_id,
                "data_index": data_index,
                "resource_type": resource_type,
            }
        )
    rows.sort(key=lambda row: (row["group"], row["primary_key"], row["resource_type"]))
    return rows


def decrypt_target_bundles(rows: list[dict[str, Any]], catalog: dict[str, Any]) -> None:
    bundles = {
        row["dependency_bundle"]
        for row in rows
        if row["group"] in TARGET_GROUPS and isinstance(row.get("dependency_bundle"), str)
    }
    try:
        bundles.add(config_bundle_for(catalog, "AccountPortrait"))
    except Exception:
        pass
    for bundle in sorted(bundles):
        out_path = DECRYPTED_BUNDLE_DIR / bundle
        if out_path.exists() and out_path.read_bytes().startswith(b"UnityFS"):
            continue
        decrypt_bundles(DEFAULT_GAME_DIR, Path("analysis/decrypted"), CATALOG_PATH, 0, bundle.removesuffix(".bundle"))


def recover_unity_binary_text(text: str) -> bytes:
    out = bytearray()
    for char in text:
        codepoint = ord(char)
        if 0xDC80 <= codepoint <= 0xDCFF:
            out.append(codepoint & 0xFF)
        elif codepoint <= 0xFF:
            out.append(codepoint)
        else:
            out.extend(char.encode("utf-8"))
    return bytes(out)


def load_account_portraits(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    asset = catalog_asset(catalog, ACCOUNT_PORTRAIT_PRIMARY_KEY, "UnityEngine.TextAsset")
    bundle = asset.get("dependency_bundle")
    if not isinstance(bundle, str):
        raise ValueError("cannot resolve AccountPortrait bundle")
    bundle_path = DECRYPTED_BUNDLE_DIR / bundle
    env = UnityPy.load(str(bundle_path))
    text_asset = env.container[asset["asset_id"]].read()
    raw = recover_unity_binary_text(text_asset.m_Script)
    table = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    portraits = {}
    for item_id, row in table.items():
        asset_id = row[1]
        profile_asset = asset_id.removesuffix("_Portrait") + "_Profile"
        portraits[profile_asset] = {
            "item_id": row[0],
            "portrait_asset_id": asset_id,
            "profile_asset_id": profile_asset,
            "sorting_order": row[2],
            "hero_name": row[3],
        }
    return portraits


def export_group_images(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows_by_bundle: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["resource_type"] == "UnityEngine.Sprite":
            rows_by_bundle[row["dependency_bundle"]].append(row)

    exported: dict[str, dict[str, Any]] = {}
    for bundle_name, bundle_rows in sorted(rows_by_bundle.items()):
        if not isinstance(bundle_name, str):
            continue
        bundle_path = DECRYPTED_BUNDLE_DIR / bundle_name
        if not bundle_path.exists():
            continue
        env = UnityPy.load(str(bundle_path))
        containers: dict[str, list[Any]] = defaultdict(list)
        for asset_id, pptr in env.container.items():
            containers[asset_id].append(pptr)

        for row in bundle_rows:
            candidates = containers.get(row["asset_id"], [])
            sprite_ptr = None
            for candidate in candidates:
                if candidate.type.name == "Sprite":
                    sprite_ptr = candidate
                    break
            if sprite_ptr is None:
                continue

            sprite = sprite_ptr.read()
            image = sprite.image
            rel_name = row["primary_key"].split("/", 1)[1]
            out_dir = TARGET_GROUPS[row["group"]]["out"]
            out_path = out_dir / f"{safe_filename(rel_name)}.png"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(out_path)
            exported[row["primary_key"]] = {
                **row,
                "output": str(out_path.as_posix()),
                "width": image.width,
                "height": image.height,
            }
    return exported


def average_hash(path: Path, size: int = 8) -> int:
    with Image.open(path) as image:
        gray = image.convert("L").resize((size, size), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    average = sum(pixels) / len(pixels)
    value = 0
    for index, pixel in enumerate(pixels):
        if pixel >= average:
            value |= 1 << index
    return value


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def match_existing_animal_images(exported: dict[str, dict[str, Any]], account_portraits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    existing = sorted(WEB_ANIMALS_DIR.glob("*.png"))
    by_profile_asset = {
        key.rsplit("/", 1)[-1]: value
        for key, value in exported.items()
        if value["group"] == "portraits"
    }
    candidates = []
    for profile_asset, meta in account_portraits.items():
        resource = by_profile_asset.get(profile_asset)
        if not resource:
            continue
        candidates.append(
            {
                "profile_asset_id": profile_asset,
                "resource": resource,
                "account_portrait": meta,
                "hash": average_hash(Path(resource["output"])),
            }
        )

    matches = []
    for path in existing:
        source_hash = average_hash(path)
        best = sorted(
            (
                {
                    "distance": hamming_distance(source_hash, candidate["hash"]),
                    "profile_asset_id": candidate["profile_asset_id"],
                    "resource": candidate["resource"],
                    "account_portrait": candidate["account_portrait"],
                }
                for candidate in candidates
            ),
            key=lambda item: item["distance"],
        )[:5]
        matches.append(
            {
                "name": path.stem,
                "best": [
                    {
                        "distance": item["distance"],
                        "profile_asset_id": item["profile_asset_id"],
                        "hero_name": item["account_portrait"]["hero_name"],
                        "source": item["resource"]["output"],
                    }
                    for item in best
                ],
            }
        )
    return {"count": len(matches), "matches": matches}


def copy_known_site_assets(exported: dict[str, dict[str, Any]]) -> dict[str, Any]:
    app_data = read_app_data()
    WEB_ANIMALS_DIR.mkdir(parents=True, exist_ok=True)
    WEB_ACHIEVEMENTS_DIR.mkdir(parents=True, exist_ok=True)

    animal_manual_map = {
        "鳄霸": "AU_002609_Crocodile_Original_Profile",
        "培根": "AU_002647_Bacon_Original_Profile",
        "宝伯": "AU_002652_Bob_Original_Profile",
        "山姆": "AU_002653_Sam_Original_Profile",
        "玛奇朵": "AU_002654_Macchiato_Original_Profile",
        "泰哥": "AU_002655_Tiagra_Original_Profile",
        "芭比": "AU_002657_Barbie_Original_Profile",
        "可乐": "AU_002658_Cola_Original_Profile",
        "雪诺": "AU_002659_Snow_Original_Profile",
        "锤子": "AU_002660_Hammer_Original_Profile",
        "尼莫": "AU_002661_Nemo_Original_Profile",
        "奥里": "AU_002662_Otta_Original_Profile",
        "莫斯": "AU_002663_Morse_Original_Profile",
        "利威尔": "AU_002664_Levi_Original_Profile",
        "八公": "AU_002665_Hachi_Original_Profile",
        "福吉": "AU_002666_Fuggy_Original_Profile",
        "加肥": "AU_002667_Garafat_Original_Profile",
        "卡托": "AU_002669_Cato_Original_Profile",
        "图斯卡尔": "AU_002671_Tuskarr_Original_Profile",
        "嘟嘟": "AU_002672_Dodo_Original_Profile",
        "豆豆": "AU_002673_Doudou_Original_Profile",
        "地包天": "AU_002674_Underbite_Original_Profile",
        "瓦特": "AU_002676_Watt_Original_Profile",
        "瓦力": "AU_002677_Valiente_Original_Profile",
        "麦克斯": "AU_002678_Max_Original_Profile",
        "高非": "AU_002679_GuFei_Original_Profile",
        "刺头": "AU_002681_Bristle_Original_Profile",
        "毛毛": "AU_002682_Fluffy_Original_Profile",
        "柯蒂斯": "AU_002683_Curtis_Original_Profile",
        "咕咕": "AU_002686_Gugu_Original_Profile",
        "木木": "AU_002687_Mumu_Original_Profile",
        "优罗莎": "AU_002688_Yurusa_Original_Profile",
        "阿呆": "AU_002689_Otta_Original_Profile",
        "阿瓜": "AU_002690_Duck_Original_Profile",
        "阿宝": "AU_002691_Bao_Original_Profile",
        "暴莉": "AU_002692_Bully_Original_Profile",
        "咩咩": "AU_002693_Meemee_Original_Profile",
        "希子": "AU_002694_Xizi_Original_Profile",
        "奥姆诺姆": "AU_002695_Omnom_Original_Profile",
        "福宝": "AU_003721_Panda_Original_Profile",
        "妙妙": "AU_003722_RedPanda_Original_Profile",
        "纳鲁": "AU_003725_Naru_Original_Profile",
        "苗苗": "AU_003726_Meow_Original_Profile",
        "星期天": "AU_003727_Sunday_Original_Profile",
        "卡洛特": "AU_003728_Carrot_Original_Profile",
        "玛奈奇": "AU_003729_Maneki_Original_Profile",
        "白菜狗": "AU_003730_CabbageDog_Original_Profile",
        "小新": "AU_003731_ShinChan_Original_Profile",
        "丘丘": "AU_003737_Chuchu_Original_Profile",
        "哈士企": "AU_003738_Husky_Penguin_Profile",
        "巴巴拉": "AU_003739_Barbara_Original_Profile",
        "糊涂": "AU_003740_Hoot_Original_Profile",
        "桑尼": "AU_003741_Sunny_Original_Profile",
        "斯帕奇": "AU_003742_Sparky_Original_Profile",
        "罗恩": "AU_003743_Ron_Original_Profile",
        "斯黛拉": "AU_003744_Stella_Original_Profile",
        "坨坨": "AU_003746_Toto_Original_Profile",
        "泰雷斯": "AU_003747_Tyras_Original_Profile",
        "瑞文": "AU_003748_Raven_Original_Profile",
        "2662": "AU_003749_2662_Original_Profile",
        "Vicksy": "AU_003848_Vicksy_Original_Profile",
        "珞珞": "AU_003849_Luoluo_Original_Profile",
    }
    achievement_manual_map = {
        "完美格挡": "UI_Achievements_ACV001",
        "西部点子王": "UI_Achievements_ACV002",
        "我开悟了": "UI_Achievements_ACV003",
        "知识渊博": "UI_Achievements_ACV004",
        "风狗": "UI_Achievements_ACV005",
        "脑子瓦特": "UI_Achievements_ACV006",
        "赛末点": "UI_Achievements_ACV007",
        "我是岛主": "UI_Achievements_ACV008",
        "保持呼吸": "UI_Achievements_ACV009",
        "金爪奖": "UI_Achievements_ACV010",
        "积少成多": "UI_Achievements_ACV011",
        "保龄球馆里的猫": "UI_Achievements_ACV012",
        "不可能的任务": "UI_Achievements_ACV013",
        "头号玩家": "UI_Achievements_ACV014",
        "爷回来了": "UI_Achievements_ACV015",
        "鳄口脱险": "UI_Achievements_ACV016",
        "海獭突击队": "UI_Achievements_ACV017",
        "球类武器": "UI_Achievements_ACV018",
        "野鸭变凤凰": "UI_Achievements_ACV019",
        "全面战争": "UI_Achievements_ACV020",
        "火车进站": "UI_Achievements_ACV021",
        "极度干燥": "UI_Achievements_ACV022",
        "幸存者": "UI_Achievements_ACV023",
        "毛量级冠军": "UI_Achievements_ACV024",
        "十万伏特": "UI_Achievements_ACV025",
        "魂断烂桥": "UI_Achievements_ACV026",
        "G-Man": "UI_Achievements_ACV027",
        "赢了！地球上最强猛兽": "UI_Achievements_ACV028",
        "无敌破坏王": "UI_Achievements_ACV029",
        "笑到最后": "UI_Achievements_ACV030",
        "坚持再坚持": "UI_Achievements_ACV031",
        "等级 100 级": "UI_Achievements_ACV032",
        "虎胆龙威": "UI_Achievements_ACV033",
        "和平精英": "UI_Achievements_ACV034",
        "人猿泰山": "UI_Achievements_ACV035",
        "冰狗": "UI_Achievements_ACV036",
        "梦之队": "UI_Achievements_ACV037",
        "超级碗": "UI_Achievements_ACV038",
        "风平浪静": "UI_Achievements_ACV039",
        "真狗快打": "UI_Achievements_ACV040",
        "风中划水": "UI_Achievements_ACV041",
        "当红炸子鸡": "UI_Achievements_ACV042",
        "盖了帽了": "UI_Achievements_ACV043",
        "兄弟连": "UI_Achievements_ACV044",
        "小菜一碟": "UI_Achievements_ACV045",
        "你不要回来了": "UI_Achievements_ACV046",
        "阿甘快跑": "UI_Achievements_ACV047",
        "描边大师": "UI_Achievements_ACV048",
        "铁人麦克": "UI_Achievements_ACV049",
        "尼莫船长": "UI_Achievements_ACV050",
        "给我个五": "UI_Achievements_ACV051",
        "等级 50 级": "UI_Achievements_ACV052",
        "落水狗": "UI_Achievements_ACV053",
        "速度与柯基": "UI_Achievements_ACV054",
        "有乐同享": "UI_Achievements_ACV055",
        "猫朋狗友": "UI_Achievements_ACV056",
        "新兵营": "UI_Achievements_ACV057",
        "遵命，船长！": "UI_Achievements_ACV058",
        "极品飞狗": "UI_Achievements_ACV059",
        "我有个朋友": "UI_Achievements_ACV060",
        "我做主": "UI_Achievements_ACV061",
        "罗伊·马凯": "UI_Achievements_ACV062",
        "哪儿有风": "UI_Achievements_ACV063",
        "弗地冈人": "UI_Achievements_ACV064",
        "老铁来了": "UI_Achievements_ACV065",
        "快速游戏 10 胜": "UI_Achievements_ACV066",
        "打卡上班": "UI_Achievements_ACV067",
        "头像达人": "UI_Achievements_ACV068",
        "时尚时尚最时尚": "UI_Achievements_ACV069",
        "动物解锁：20": "UI_Achievements_ACV070",
        "谁干的": "UI_Achievements_ACV071",
        "皮肤解锁：20": "UI_Achievements_ACV072",
        "体育精神": "UI_Achievements_ACV073",
        "安全第一": "UI_Achievements_ACV074",
        "亚瑟的梦": "UI_Achievements_ACV075",
        "稳如老狗": "UI_Achievements_ACV076",
        "杰克与萝丝": "UI_Achievements_ACV077",
        "热狗": "UI_Achievements_ACV078",
        "冲浪狗": "UI_Achievements_ACV079",
        "牛啊": "UI_Achievements_ACV080",
        "小试牛刀": "UI_Achievements_ACV081",
        "欢迎来到派对": "UI_Achievements_ACV082",
        "白金动物": "UI_Achievements_ACV083",
        "打遍天下": "UI_Achievements_ACV084",
        "寒冰屏障": "UI_Achievements_ACV085",
        "天降正义": "UI_Achievements_ACV086",
        "窜天猴": "UI_Achievements_ACV087",
        "安全降落": "UI_Achievements_ACV088",
        "不像帕特·罗奇那样": "UI_Achievements_ACV089",
        "荒野求生": "UI_Achievements_ACV090",
        "威利·旺卡": "UI_Achievements_ACV091",
        "打工狗": "UI_Achievements_ACV092",
        "生物燃料": "UI_Achievements_ACV093",
        "钻石商人": "UI_Achievements_ACV094",
        "淘金客": "UI_Achievements_ACV095",
        "带我去月球": "UI_Achievements_ACV096",
        "飞狗环游记": "UI_Achievements_ACV097",
        "矿车狂热": "UI_Achievements_ACV098",
        "赚快钱": "UI_Achievements_ACV099",
        "拆弹部队": "UI_Achievements_ACV100",
        "猩空联盟会员": "UI_Achievements_ACV101",
        "666": "UI_Achievements_ACV102",
        "科怀·伦纳德": "UI_Achievements_ACV103",
        "帽子戏法": "UI_Achievements_ACV104",
        "身体健全": "UI_Achievements_ACV105",
        "干杯，宝贝们！": "UI_Achievements_ACV106",
        "威尔逊": "UI_Achievements_ACV107",
        "秋名山猛兽": "UI_Achievements_ACV108",
    }

    by_leaf = {key.rsplit("/", 1)[-1]: value for key, value in exported.items()}
    copied_animals = []
    missing_animals = []
    for name in app_data["animals"]:
        asset = animal_manual_map.get(name)
        source = by_leaf.get(asset) if asset else None
        if not source:
            missing_animals.append({"name": name, "expected_asset": asset})
            continue
        shutil.copyfile(source["output"], WEB_ANIMALS_DIR / f"{name}.png")
        copied_animals.append({"name": name, "asset": asset, "source": source["output"]})

    copied_achievements = []
    missing_achievements = []
    for name in app_data["achievements"]:
        asset = achievement_manual_map.get(name)
        source = by_leaf.get(asset) if asset else None
        if not source:
            missing_achievements.append({"name": name, "expected_asset": asset})
            continue
        target = WEB_ACHIEVEMENTS_DIR / f"{name}.jpg"
        source_path = Path(source["output"])
        with Image.open(source_path) as image:
            image.convert("RGB").save(target, quality=92)
        copied_achievements.append({"name": name, "asset": asset, "source": source["output"]})

    return {
        "animals": {
            "site_count": len(app_data["animals"]),
            "copied_count": len(copied_animals),
            "missing_count": len(missing_animals),
            "copied": copied_animals,
            "missing": missing_animals,
        },
        "achievements": {
            "site_count": len(app_data["achievements"]),
            "copied_count": len(copied_achievements),
            "missing_count": len(missing_achievements),
            "copied": copied_achievements,
            "missing": missing_achievements,
        },
    }


def build_resources_manifest() -> dict[str, Any]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    rows = build_catalog_manifest(catalog)
    decrypt_target_bundles(rows, catalog)
    exported = export_group_images(rows)
    account_portraits = load_account_portraits(catalog)
    site_report = copy_known_site_assets(exported)
    animal_image_matches = match_existing_animal_images(exported, account_portraits)

    return {
        "catalog": str(CATALOG_PATH.as_posix()),
        "groups": {
            name: {
                "prefix": config["prefix"],
                "bundles": sorted(
                    {
                        row["dependency_bundle"]
                        for row in rows
                        if row["group"] == name and isinstance(row.get("dependency_bundle"), str)
                    }
                ),
                "catalog_sprite_count": sum(
                    1
                    for row in rows
                    if row["group"] == name and row["resource_type"] == "UnityEngine.Sprite"
                ),
                "exported_count": sum(1 for row in exported.values() if row["group"] == name),
                "out": str(config["out"].as_posix()),
            }
            for name, config in TARGET_GROUPS.items()
        },
        "account_portraits": sorted(account_portraits.values(), key=lambda row: row["sorting_order"]),
        "animal_image_matches": animal_image_matches,
        "site_report": site_report,
        "resources": sorted(exported.values(), key=lambda row: row["primary_key"]),
    }


def main() -> int:
    manifest = build_resources_manifest()
    out_path = EXTRACTED_DIR / "resources_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["groups"], ensure_ascii=False, indent=2))
    print(json.dumps(manifest["site_report"], ensure_ascii=False, indent=2))
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
