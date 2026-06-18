from __future__ import annotations

import base64
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


GAME_ROOT = Path(r"F:\SteamLibrary\steamapps\common\Party Animals")
DATA_ROOT = GAME_ROOT / "PartyAnimals_Data"
STREAMING_ASSETS = DATA_ROOT / "StreamingAssets"
AA_DIR = STREAMING_ASSETS / "aa"
BUNDLE_DIR = AA_DIR / "StandaloneWindows64"
HYBRIDCLR_DIR = STREAMING_ASSETS / "RecreateHybridCLR"
SINGLE_MAPS_DIR = STREAMING_ASSETS / "SingleMaps"
METADATA_PATH = DATA_ROOT / "il2cpp_data" / "Metadata" / "global-metadata.dat"
OUT_DIR = Path(__file__).resolve().parent


INTERESTING_METADATA_TERMS = [
    b"AAInitializer",
    b"ClearEncryptedBundleCache",
    b"LoadContentCatalogAsync",
    b"AddressableHotUpdateFileList",
    b"HotUpdateFileList",
    b"RemoteBundleHostingUrl",
    b"LocalBundleCacheDirectory",
    b"EncryptedAssetBundleProvider",
    b"AESStreamProcessor",
    b"AssetBundleHelper",
    b"CryptoManager",
    b"Achievement",
    b"PlayerAvatar",
    b"LanguageData",
    b"BaseLocalize",
]


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def printable_head(data: bytes, length: int = 64) -> str:
    return "".join(chr(c) if 32 <= c < 127 else "." for c in data[:length])


def maybe_base64_decode(data: bytes) -> dict[str, Any]:
    stripped = data.strip()
    try:
        decoded = base64.b64decode(stripped, validate=True)
    except Exception as exc:
        return {"is_base64": False, "error": str(exc)}

    return {
        "is_base64": True,
        "decoded_size": len(decoded),
        "decoded_head_hex": decoded[:32].hex(),
        "decoded_head_ascii": printable_head(decoded),
        "decoded_entropy_64k": round(entropy(decoded[:65536]), 4),
        "decoded_json_like": decoded[:1] in (b"{", b"["),
    }


def repeat_block_stats(data: bytes, block_size: int = 16, limit: int = 1024 * 1024) -> dict[str, Any]:
    sample = data[:limit]
    sample = sample[: len(sample) // block_size * block_size]
    blocks = [sample[i : i + block_size] for i in range(0, len(sample), block_size)]
    counts = Counter(blocks)
    repeated_extra = sum(count - 1 for count in counts.values() if count > 1)
    top = [
        {"block_hex": block.hex(), "count": count}
        for block, count in counts.most_common(5)
        if count > 1
    ]
    return {
        "block_size": block_size,
        "sample_blocks": len(blocks),
        "repeated_extra": repeated_extra,
        "top_repeated_blocks": top,
    }


def describe_file(path: Path, include_base64: bool = True, include_repeats: bool = False) -> dict[str, Any]:
    data = path.read_bytes()
    info: dict[str, Any] = {
        "path": str(path),
        "size": len(data),
        "head_hex": data[:32].hex(),
        "head_ascii": printable_head(data),
        "entropy_64k": round(entropy(data[:65536]), 4),
    }
    if include_base64:
        info["base64"] = maybe_base64_decode(data)
    if include_repeats:
        repeat_data = data
        decoded = info.get("base64", {})
        if decoded.get("is_base64"):
            repeat_data = base64.b64decode(data.strip())
        info["repeat_blocks_16"] = repeat_block_stats(repeat_data, 16)
    return info


def scan_catalogs() -> dict[str, Any]:
    catalog_paths = [
        AA_DIR / "catalog.json",
        BUNDLE_DIR / "catalog_219610.json",
    ]
    catalog_paths.extend(sorted(SINGLE_MAPS_DIR.glob("*/*/catalog_*.json"))[:5])
    return {
        str(path): describe_file(path, include_base64=True, include_repeats=True)
        for path in catalog_paths
        if path.exists()
    }


def scan_hotupdate_files() -> dict[str, Any]:
    paths = [
        HYBRIDCLR_DIR / "version.bytes",
        HYBRIDCLR_DIR / "AotDlls" / "AotDllFileList.bytes",
        HYBRIDCLR_DIR / "HotUpdateDlls" / "HotUpdateFileList.bytes",
        HYBRIDCLR_DIR / "HotUpdateDlls" / "PartyAnimals.Ui.dll.bytes",
        HYBRIDCLR_DIR / "AotDlls" / "Recreate.PartyAnimals.dll.bytes",
    ]
    paths.extend(sorted(SINGLE_MAPS_DIR.glob("*/*/AddressableHotUpdateFileList.bytes"))[:5])
    return {
        str(path): describe_file(path, include_base64=True, include_repeats=True)
        for path in paths
        if path.exists()
    }


def scan_bundle_headers() -> dict[str, Any]:
    bundle_paths = sorted(BUNDLE_DIR.glob("*.bundle"))
    sample_paths = bundle_paths[:20]
    headers = [describe_file(path, include_base64=False, include_repeats=False) for path in sample_paths]
    return {
        "bundle_count": len(bundle_paths),
        "sample": headers,
    }


def scan_single_maps() -> list[dict[str, Any]]:
    maps = []
    for map_dir in sorted(SINGLE_MAPS_DIR.iterdir()) if SINGLE_MAPS_DIR.exists() else []:
        if not map_dir.is_dir():
            continue
        standalone = map_dir / "StandaloneWindows64"
        maps.append(
            {
                "name": map_dir.name,
                "has_catalog": any(standalone.glob("catalog_*.json")),
                "has_file_list": (standalone / "AddressableHotUpdateFileList.bytes").exists(),
                "has_version": (standalone / "version.bytes").exists(),
            }
        )
    return maps


def scan_metadata_strings() -> list[dict[str, Any]]:
    if not METADATA_PATH.exists():
        return []
    data = METADATA_PATH.read_bytes()
    hits = []
    seen = set()
    for term in INTERESTING_METADATA_TERMS:
        for match in re.finditer(re.escape(term), data, flags=re.IGNORECASE):
            start = max(0, match.start() - 500)
            end = min(len(data), match.end() + 900)
            strings = re.findall(rb"[ -~]{4,}", data[start:end])
            context = " | ".join(s.decode("utf-8", errors="replace") for s in strings[:45])
            key = (term.lower(), context)
            if key not in seen:
                seen.add(key)
                hits.append({"term": term.decode(), "offset": match.start(), "context": context})
            break
    return hits


def main() -> None:
    result = {
        "game_root": str(GAME_ROOT),
        "catalogs": scan_catalogs(),
        "hotupdate_files": scan_hotupdate_files(),
        "bundles": scan_bundle_headers(),
        "single_maps": scan_single_maps(),
        "metadata_hits": scan_metadata_strings(),
        "notes": [
            "catalog.json/catalog_*.json and hot-update file lists are base64 text whose decoded payload is high-entropy data, not plain Addressables JSON.",
            "UnityFS bundle headers are present, but sample data has high entropy and UnityPy fails on decompression, consistent with encrypted or custom-wrapped bundles.",
            "IL2CPP metadata references AAInitializer, ClearEncryptedBundleCache, AESStreamProcessor, EncryptedAssetBundleProvider, AssetBundleHelper, and CryptoManager.",
        ],
    }

    out_path = OUT_DIR / "party_animals_asset_scan.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
