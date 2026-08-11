from __future__ import annotations

import argparse
import base64
import json
import re
import struct
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


DEFAULT_GAME_DIR = Path(r"F:\SteamLibrary\steamapps\common\Party Animals")
HOT_UPDATE_KEY = b"X2v8pL0qWm9sYt3B"
CATALOG_KEY = b"4X8HH3QBGVS7O8X2"
HEO_HASH_METADATA_OFFSET = 0x17AB658


def aes_ecb_decrypt(data: bytes, key: bytes) -> bytes:
    plain = AES.new(key, AES.MODE_ECB).decrypt(data)
    return unpad(plain, AES.block_size)


def maybe_base64_decode(data: bytes) -> bytes:
    stripped = b"".join(data.split())
    if not stripped:
        return data
    if len(stripped) % 4:
        return data
    if not re.fullmatch(rb"[A-Za-z0-9+/=]+", stripped):
        return data
    try:
        return base64.b64decode(stripped, validate=True)
    except Exception:
        return data


def decrypt_hot_update_file(src: Path) -> bytes:
    raw = src.read_bytes()
    return aes_ecb_decrypt(maybe_base64_decode(raw), HOT_UPDATE_KEY)


def decrypt_catalog_file(src: Path) -> dict:
    ciphertext = base64.b64decode(src.read_text(encoding="utf-8").strip(), validate=True)
    plain = aes_ecb_decrypt(ciphertext, CATALOG_KEY)
    return json.loads(plain.decode("utf-8"))


def load_heo_hash(game_dir: Path) -> list[int]:
    metadata = game_dir / "PartyAnimals_Data" / "il2cpp_data" / "Metadata" / "global-metadata.dat"
    data = metadata.read_bytes()
    return list(struct.unpack_from("<128i", data, HEO_HASH_METADATA_OFFSET))


def heo_params(bundle_id: str, heo_hash: list[int]) -> tuple[str, int, int]:
    name = re.split(r"[\\/]", bundle_id)[-1]
    stem = name.rsplit(".", 1)[0] if "." in name else name
    key = 0x7C
    total = 0
    for value in stem.encode("ascii"):
        key ^= value
        total += value
    return stem, key, heo_hash[total % len(heo_hash)]


def heo_decrypt_bytes(data: bytes, key: int, reserved_pos: int, stream_pos: int = 0) -> bytes:
    out = bytearray(data)
    for index in range(len(out)):
        pos = stream_pos + index
        if pos < reserved_pos:
            continue
        out[index] ^= (((pos >> 3) + 1) & 0xFF) ^ key
    return bytes(out)


def iter_catalog_bundle_ids(catalog: dict) -> list[str]:
    ids = catalog.get("m_InternalIds") or []
    return [
        value
        for value in ids
        if isinstance(value, str) and value.lower().endswith(".bundle")
    ]


def write_bytes_if_changed(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return
    path.write_bytes(data)


def write_text_if_changed(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8", newline="\n")


def decrypt_hybridclr(game_dir: Path, out_dir: Path) -> list[dict]:
    streaming = game_dir / "PartyAnimals_Data" / "StreamingAssets"
    roots = [
        streaming / "RecreateHybridCLR" / "HotUpdateDlls",
        streaming / "RecreateHybridCLR" / "AotDlls",
    ]
    results: list[dict] = []
    for root in roots:
        if not root.exists():
            continue
        for src in sorted(root.glob("*.bytes")):
            plain = decrypt_hot_update_file(src)
            rel = src.relative_to(streaming / "RecreateHybridCLR")
            name = src.name
            if name.endswith(".dll.bytes"):
                name = name[:-6]
            else:
                name = name[:-6] + ".txt"
            dst = out_dir / "RecreateHybridCLR" / rel.parent / name
            write_bytes_if_changed(dst, plain)
            results.append(
                {
                    "source": str(src),
                    "output": str(dst),
                    "bytes": len(plain),
                    "head": plain[:16].hex(),
                }
            )
    return results


def summarize_catalog(catalog: dict, source: Path, output: Path) -> dict:
    internal_ids = catalog.get("m_InternalIds") or []
    local_prefix = "{UnityEngine.AddressableAssets.Addressables.RuntimePath}"
    remote_prefix = "{AAInitializer.RemoteBundleHostingUrl}"
    local_bundles = [v for v in internal_ids if isinstance(v, str) and v.startswith(local_prefix)]
    remote_bundles = [v for v in internal_ids if isinstance(v, str) and v.startswith(remote_prefix)]
    return {
        "source": str(source),
        "output": str(output),
        "locator": catalog.get("m_LocatorId"),
        "provider_ids": catalog.get("m_ProviderIds") or [],
        "resource_provider_count": len(catalog.get("m_ResourceProviderData") or []),
        "resource_type_count": len(catalog.get("m_resourceTypes") or []),
        "internal_id_count": len(internal_ids),
        "local_bundle_count": len(local_bundles),
        "remote_bundle_count": len(remote_bundles),
        "sample_internal_ids": internal_ids[:30],
    }


def decrypt_catalogs(game_dir: Path, out_dir: Path) -> list[dict]:
    aa_root = game_dir / "PartyAnimals_Data" / "StreamingAssets" / "aa"
    summaries: list[dict] = []
    for src in sorted(aa_root.rglob("catalog*.json")):
        catalog = decrypt_catalog_file(src)
        rel = src.relative_to(aa_root)
        dst = out_dir / "aa" / rel
        text = json.dumps(catalog, ensure_ascii=False, indent=2)
        write_text_if_changed(dst, text + "\n")
        summary = summarize_catalog(catalog, src, dst)
        summary_path = dst.with_suffix(".summary.json")
        write_text_if_changed(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        summaries.append(summary)
    return summaries


def resolve_bundle_path(game_dir: Path, bundle_id: str) -> Path:
    name = re.split(r"[\\/]", bundle_id)[-1]
    aa_root = game_dir / "PartyAnimals_Data" / "StreamingAssets" / "aa"
    return aa_root / "StandaloneWindows64" / name


def decrypt_bundles(game_dir: Path, out_dir: Path, catalog_path: Path, limit: int, name_pattern: str | None) -> list[dict]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    heo_hash = load_heo_hash(game_dir)
    bundle_ids = iter_catalog_bundle_ids(catalog)
    if name_pattern:
        bundle_ids = [value for value in bundle_ids if name_pattern.lower() in value.lower()]
    if limit > 0:
        bundle_ids = bundle_ids[:limit]

    results: list[dict] = []
    for bundle_id in bundle_ids:
        src = resolve_bundle_path(game_dir, bundle_id)
        if not src.exists():
            results.append({"id": bundle_id, "source": str(src), "missing": True})
            continue
        stem, key, reserved_pos = heo_params(bundle_id, heo_hash)
        raw = src.read_bytes()
        plain = heo_decrypt_bytes(raw, key, reserved_pos)
        dst = out_dir / "aa" / "StandaloneWindows64" / src.name
        write_bytes_if_changed(dst, plain)

        header_size = 0
        if plain.startswith(b"UnityFS"):
            # UnityFS header: signature\0 version u32, unity version\0, generator version\0,
            # then big-endian size fields. Keep this as a light sanity signal only.
            header_size = plain.find(b"\0", plain.find(b"\0", 8) + 1)
        results.append(
            {
                "id": bundle_id,
                "source": str(src),
                "output": str(dst),
                "bytes": len(plain),
                "stem": stem,
                "key": key,
                "reserved_pos": reserved_pos,
                "head": plain[:16].hex(),
                "signature": plain[:7].decode("ascii", errors="replace"),
                "header_probe": header_size,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Decrypt local Party Animals data files.")
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--out-dir", type=Path, default=Path("analysis/decrypted"))
    parser.add_argument("--skip-hybridclr", action="store_true")
    parser.add_argument("--skip-catalog", action="store_true")
    parser.add_argument("--decrypt-bundles", action="store_true")
    parser.add_argument("--bundle-limit", type=int, default=1, help="0 means no limit when --decrypt-bundles is set.")
    parser.add_argument("--bundle-name", help="case-insensitive substring filter for bundle ids.")
    args = parser.parse_args()

    game_dir = args.game_dir
    out_dir = args.out_dir
    report: dict[str, object] = {
        "game_dir": str(game_dir),
        "out_dir": str(out_dir),
        "hot_update_key": HOT_UPDATE_KEY.decode("ascii"),
        "catalog_key": CATALOG_KEY.decode("ascii"),
    }
    if not args.skip_hybridclr:
        report["hybridclr"] = decrypt_hybridclr(game_dir, out_dir)
    if not args.skip_catalog:
        report["catalogs"] = decrypt_catalogs(game_dir, out_dir)
    if args.decrypt_bundles:
        catalog_path = out_dir / "aa" / "catalog.json"
        if not catalog_path.exists():
            catalog = decrypt_catalog_file(game_dir / "PartyAnimals_Data" / "StreamingAssets" / "aa" / "catalog.json")
            write_text_if_changed(catalog_path, json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
        report["bundles"] = decrypt_bundles(game_dir, out_dir, catalog_path, args.bundle_limit, args.bundle_name)

    report_path = out_dir / "decrypt_report.json"
    write_text_if_changed(report_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
