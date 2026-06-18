# Party Animals 资源同步工作流

这份文档给一个“没有上下文记忆”的 AI 用：从零开始更新站点资源，并在游戏更新后自己排查、适配。

## 目标

站点最终使用这些由游戏资源生成的文件：

- `data/animals.generated.js`
- `data/achievements.generated.js`
- `images/animals/H*.png`
- `images/achievements/ACV*.png`

动物 id、成就 id、地图 id、图片 id、特征 id 都应尽量跟游戏资源一致。不要手抄旧站点内容，也不要把旧中文文件名当主键。

## 关键路径

- 仓库根目录：`E:\Desktop\partyanimals`
- 默认游戏目录：`F:\SteamLibrary\steamapps\common\Party Animals`
- 一键入口：`analysis/update_from_game.py`
- 解密入口：`analysis/decrypt_party_animals.py`
- catalog / bundle 工具：`analysis/extract_party_animals_web_assets.py`
- 动物资源索引：`analysis/export_party_animals_resource_index.py`
- 成就与地图索引：`analysis/build_party_animals_achievement_map_index.py`
- 动物站点同步：`analysis/sync_site_animals.py`
- 成就站点同步：`analysis/sync_site_achievements.py`

这些目录是缓存，不应提交：

- `analysis/decrypted/`
- `analysis/extracted/`
- `analysis/il2cppdump_out*/`
- `analysis/__pycache__/`

## 依赖

Python 3.11+，以及：

- `UnityPy`
- `Pillow`
- `msgpack`
- `pycryptodome`

缺什么就装什么：

```powershell
python -m pip install UnityPy Pillow msgpack pycryptodome
```

## 从零完整更新

在仓库根目录运行：

```powershell
python -X utf8 analysis\update_from_game.py --game-dir "F:\SteamLibrary\steamapps\common\Party Animals"
```

这个入口现在会按顺序做：

1. `decrypt`
2. `extract_resources`
3. `extract_animals`
4. `sync_site`
5. `sync_achievements`

其中 `extract_resources` 先生成 `analysis/extracted/resources_manifest.json`，这是后续动物和成就图标提取的基础。

## 不重新解密的快速重建

如果 `analysis/decrypted/` 已经存在，只改了解析或同步脚本，可以运行：

```powershell
python -X utf8 analysis\update_from_game.py --skip-decrypt
```

这会重新生成：

- `analysis/extracted/resources_manifest.json`
- `analysis/extracted/resource_index/party_animals_resources.json`
- `analysis/extracted/resource_index/animals_core.json`
- `analysis/extracted/achievement_map_index.json`
- `analysis/extracted/achievement_map_index_core.json`
- `data/animals.generated.js`
- `data/achievements.generated.js`
- `images/animals/*.png`
- `images/achievements/*.png`

## 基础验证

先检查脚本语法：

```powershell
python -X utf8 -m py_compile analysis\extract_party_animals_web_assets.py analysis\build_party_animals_web_data.py analysis\export_party_animals_resource_index.py analysis\build_party_animals_achievement_map_index.py analysis\sync_site_animals.py analysis\sync_site_achievements.py analysis\update_from_game.py analysis\decrypt_party_animals.py analysis\scan_party_animals_assets.py
```

检查成就站点数据没有泄露调试字段：

```powershell
python -X utf8 -c "from pathlib import Path; t=Path('data/achievements.generated.js').read_text(encoding='utf-8'); print({k:t.count(k) for k in ['sceneId','mapNameEn','sceneName','sceneMatch']})"
```

期望都是 `0`。

检查动物图片路径是否使用游戏 id：

```powershell
python -X utf8 -c "from pathlib import Path; t=Path('data/animals.generated.js').read_text(encoding='utf-8'); print(t.count('images/animals/H'))"
```

输出数量应等于同步报告里的动物数量。

## 同步链路原理

`analysis/update_from_game.py` 是总入口。

1. `decrypt_hybridclr()` 从游戏目录提取 HybridCLR DLL 到 `analysis/decrypted/RecreateHybridCLR/`。
2. `decrypt_catalogs()` 解密 Addressables catalog 到 `analysis/decrypted/aa/`。
3. `build_resources_manifest()` 先导出资源清单和图标/头像基础资源，写入 `analysis/extracted/resources_manifest.json`。
4. 动物脚本通过 catalog 定位配置表和图片 bundle，生成动物、中文名、本体图片和特征。
5. 成就脚本读取 `Achievement`、`SelectableScene`、`I2LanguagesFull_LoadingMaps`，生成成就、条件、地图筛选。
6. 站点同步脚本增量复制图片，并写入 `data/*.generated.js`。

不要依赖固定 bundle hash。类似 `6211be75...bundle`、`65f88cd7...bundle` 的文件名可能随游戏更新变化。脚本应优先通过 catalog primary key 自动定位资源。

## 故障排查

### catalog 解密失败

先怀疑 `CATALOG_KEY` 变化。流程：

1. 运行 `analysis/scan_party_animals_assets.py`。
2. 检查 `LoadContentCatalogAsync`、`AAInitializer`、`CryptoManager`、`AESStreamProcessor` 相关字符串。
3. 只有证明 key 变了，才改 `analysis/decrypt_party_animals.py`。

### HotUpdate 文件解密失败

先怀疑 `HOT_UPDATE_KEY` 变化。排查方式同上。

### bundle 解密失败或 UnityPy 不能加载

常见原因：

- `HEO_HASH_METADATA_OFFSET` 变化
- bundle transform 逻辑变化
- catalog 依赖指向了新 bundle 分组

优先确认 `analysis/decrypted/aa/catalog.json` 是当前版本，然后只解一个确定存在的 bundle 看是否还是 `UnityFS`。

### 配置表找不到

如果 `Achievement`、`Hero`、`Occupation`、`Item`、`SelectableScene` 读取失败，先枚举相似 key，再改 `text_asset_bytes()` 的 key 构造方式或 resource type 筛选。

### 中文本地化找不到

如果中文名缺失，先枚举 `I2LanguagesFull_*` key，再更新 `LOCALIZATION_PRIMARY_KEYS` 或语言索引逻辑。

### 成就图标被清空

这通常说明资源清单没先生成，或者图标源全缺失。

现在的保护逻辑是：如果成就图标全部缺失，脚本会直接报错，不再继续删站点图标。

## 交付前检查清单

1. 所有同步脚本 `py_compile` 通过。
2. `python -X utf8 analysis\update_from_game.py --skip-decrypt` 可以跑通。
3. 完整同步可以跑通。
4. `analysis/extracted/resources_manifest.json` 存在。
5. `data/achievements.generated.js` 不包含 `sceneId`、`mapNameEn`、`sceneName`、`sceneMatch`。
6. 动物图片路径是 `images/animals/H*.png`。
7. 成就图片路径是 `images/achievements/ACV*.png`。
8. `git status` 里没有意外的缓存目录或临时日志。
