# Party Animals 资源同步工作流

这份文档面向一个“没有上下文记忆”的 AI：从当前游戏安装中更新站点资源，并在游戏版本变化后根据运行证据排查和适配。

保留中文版是有意的。本项目的路径、站点文案和主要验收语义都是中文；命令、代码标识符和原始错误保持英文即可。不要因为文档是中文而自行翻译游戏 id、资源 key 或日志。

## 目标与原则

站点最终使用这些由游戏资源生成的文件：

- `data/animals.generated.js`
- `data/achievements.generated.js`
- `images/animals/H*.png`
- `images/achievements/ACV*.png`

动物 id、成就 id、地图 id、图片 id、特征 id 应尽量与当前游戏资源一致。

执行时遵守这些原则：

1. 以当前运行资源为准，不手抄旧站点内容，也不把旧中文文件名当主键。
2. 先证明 catalog、配置表和 bundle 属于同一游戏版本，再修改解析逻辑。
3. 完整更新用于刷新游戏来源和 bundle 缓存；`--skip-decrypt` 只用于当前版本缓存上的快速重建。
4. 缺图保护只负责避免破坏站点，不代表同步成功。交付时 `images_missing` 仍应为 `0`。
5. 遇到新场景或同名文案时，核对成就条件与实际场景，不接受“脚本跑通但映射错误”。

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

这些是缓存或临时分析产物，不应提交：

- `analysis/decrypted/`
- `analysis/extracted/`
- `analysis/il2cppdump_out*/`
- `analysis/.tmp_*/`
- `analysis/__pycache__/`
- `analysis/party_animals_asset_scan.json`
- 临时下载的 Il2CppDumper、反汇编输出和测试 bundle

原始游戏文件只读。原始、解密和导出文件必须分别保留在游戏目录、`analysis/decrypted/` 和 `analysis/extracted/`。

## 依赖

要求 Python 3.11+，以及：

- `UnityPy`
- `Pillow`
- `msgpack`
- `pycryptodome`

缺什么就安装什么：

```powershell
python -m pip install UnityPy Pillow msgpack pycryptodome
```

Il2CppDumper、Capstone 等只在 HEO 参数变化时用于诊断，不是日常同步依赖。临时下载后应在交付前删除。

## 更新前检查

### 1. 确认游戏更新已经完成

不要在 Steam 正在下载、校验或替换文件时同步，也不要在同步期间启动新的游戏更新。至少检查：

```powershell
Get-Item "F:\SteamLibrary\steamapps\common\Party Animals\GameAssembly.dll"
Get-Item "F:\SteamLibrary\steamapps\common\Party Animals\PartyAnimals_Data\il2cpp_data\Metadata\global-metadata.dat"
Get-Item "F:\SteamLibrary\steamapps\common\Party Animals\PartyAnimals_Data\StreamingAssets\aa\catalog.json"
```

记录大小和修改时间，短暂等待后再次检查。只要这些文件仍在变化，就停止分析并等待更新完成。

游戏更新过程中可能出现“新 catalog / 新配置表 + 旧 bundle”的混合状态。典型表现是只有一个新动物 `image: null`，或同一条目在连续运行间 id 发生变化。这时不要手工补图，也不要立即修改资源 key；先让游戏更新完成，再跑完整更新。

### 2. 记录工作树基线

```powershell
git status --short --branch
```

保留用户已有变更。同步结束后只解释本次生成和适配产生的差异。

### 3. 先检查脚本语法

```powershell
python -X utf8 -m py_compile analysis\extract_party_animals_web_assets.py analysis\build_party_animals_web_data.py analysis\export_party_animals_resource_index.py analysis\build_party_animals_achievement_map_index.py analysis\sync_site_animals.py analysis\sync_site_achievements.py analysis\update_from_game.py analysis\decrypt_party_animals.py analysis\scan_party_animals_assets.py
```

## 从零完整更新

在仓库根目录运行：

```powershell
python -X utf8 analysis\update_from_game.py --game-dir "F:\SteamLibrary\steamapps\common\Party Animals"
```

入口按顺序执行：

1. `decrypt`
2. `extract_resources`
3. `extract_animals`
4. `sync_site`
5. `sync_achievements`

当前完整更新会为本次进程实际用到的 bundle 强制刷新一次，即使缓存文件已经以 `UnityFS` 开头。这是必要行为：Party Animals 可能在文件名不变的情况下替换 bundle 内容。仅检查签名会误用同名旧缓存。

`extract_resources` 必须先生成 `analysis/extracted/resources_manifest.json`，它是后续动物头像和成就图标提取的基础。

完整更新成功时，报告至少应满足：

- 每个资源组的 `exported_count == catalog_sprite_count`
- `animals_with_image == animals`
- 动物和成就的 `images_missing == 0`
- 没有意外删除仍被引用的图片

如果游戏文件在运行中发生过变化，即使某次完整更新成功，也应在文件稳定后重新执行一次完整更新。

## 不重新解密的快速重建

只有在以下条件同时成立时使用：

- 已经对当前游戏版本成功执行过一次完整更新；
- `analysis/decrypted/` 属于当前 catalog；
- 只修改了解析、匹配或站点同步脚本。

命令：

```powershell
python -X utf8 analysis\update_from_game.py --skip-decrypt
```

它会复用 bundle 缓存并重新生成：

- `analysis/extracted/resources_manifest.json`
- `analysis/extracted/resource_index/party_animals_resources.json`
- `analysis/extracted/resource_index/animals_core.json`
- `analysis/extracted/achievement_map_index.json`
- `analysis/extracted/achievement_map_index_core.json`
- `data/animals.generated.js`
- `data/achievements.generated.js`
- `images/animals/*.png`
- `images/achievements/*.png`

如果 `--skip-decrypt` 成功、完整更新失败，不要把快速重建当成交付依据；这通常表示旧缓存仍可读，而当前游戏资源的解密参数已经变化。

## 同步链路原理

`analysis/update_from_game.py` 是总入口。

1. `decrypt_hybridclr()` 从游戏目录提取 HybridCLR DLL 到 `analysis/decrypted/RecreateHybridCLR/`。
2. `decrypt_catalogs()` 解密 Addressables catalog 到 `analysis/decrypted/aa/`。
3. `build_resources_manifest()` 通过当前 catalog 定位并刷新资源组 bundle，导出基础图标和头像。
4. 动物脚本读取 `Hero`、`Occupation`、`Variant`、`Item`、`ItemTag` 与本地化表，通过 catalog primary key 定位默认头像。
5. 成就脚本读取 `Achievement`、`SelectableScene`、`I2LanguagesFull_LoadingMaps`，生成条件、地图与筛选。
6. 站点同步脚本增量复制图片、清理未引用图片，并写入 `data/*.generated.js`。

不要依赖固定 bundle hash。类似 `6211be75...bundle`、`65f88cd7...bundle` 的名称可能变化，也可能名称不变但内容已更新。资源定位必须优先使用当前 catalog 的 primary key 和依赖关系。

动物图片为空时，同步脚本会记录 `images_missing` 并输出 `image: null`，不会再因 `Path / None` 崩溃。但交付前仍必须追查为什么缺图。

## 成就与地图匹配规则

场景匹配证据的优先级是：

1. 明确的 `ACTION_SCENE_ALIASES`
2. 明确的 `DERIVED_ACTION_SCENES`
3. 中英文条件中提取的地图提示

明确的 action id 必须优先于模糊文案。2026-07-16 更新加入了卡丁车场景 `Cast-a-Way / 荒岛环线`，它会与教程关卡条件里的 `Cast Away / 荒岛` 发生英文归一化碰撞。如果先按英文提示匹配，`ACV102` 会被错误绑定到 `AKDD_Island`。正确结果仍是教程场景 `AE_001991_TutorialNewPt3_Original / 荒岛`。

每次出现新场景时，都应检查：

- `condition` 中的地图名称是否与 `mapName` 一致；
- 教程、剧情或特殊模式是否被同名的新可选场景劫持；
- action alias 是否比本地化文本提供了更强的场景证据；
- `git diff -- data/achievements.generated.js` 是否出现无理由的批量 feature 索引漂移。

不要为单条冲突直接手写成就 id 覆盖；优先修复通用匹配优先级。

## 基础验证

### 1. 检查站点字段和图片数量

```powershell
python -X utf8 -c "from pathlib import Path; ach=Path('data/achievements.generated.js').read_text(encoding='utf-8'); ani=Path('data/animals.generated.js').read_text(encoding='utf-8'); print({'debug_fields': {k:ach.count(k) for k in ['sceneId','mapNameEn','sceneName','sceneMatch']}, 'animal_refs': ani.count('images/animals/H'), 'animal_png': len(list(Path('images/animals').glob('H*.png'))), 'achievement_png': len(list(Path('images/achievements').glob('ACV*.png'))), 'manifest': Path('analysis/extracted/resources_manifest.json').exists()})"
```

期望：

- 四个调试字段都是 `0`；
- `animal_refs == animal_png ==` 同步报告中的动物数；
- `achievement_png ==` 同步报告中的成就数；
- `manifest` 为 `True`。

### 2. 检查生成差异

```powershell
git diff --check
git diff -- data\animals.generated.js data\achievements.generated.js
git status --short
```

重点核对新增/删除条目、id、图片路径、地图名称和 feature 索引。不要只看文件数量。

### 3. 验证快速重建幂等

完整更新成功后再运行一次：

```powershell
python -X utf8 analysis\update_from_game.py --skip-decrypt
```

第二次报告应以 `images_unchanged` 为主，不应继续新增、删除或修改同一批资源。

## 故障排查

### catalog 解密失败

先怀疑 `CATALOG_KEY` 变化：

1. 运行 `analysis/scan_party_animals_assets.py`。
2. 检查 `LoadContentCatalogAsync`、`AAInitializer`、`CryptoManager`、`AESStreamProcessor` 相关字符串。
3. 只有证明 key 变化后，才修改 `analysis/decrypt_party_animals.py`。

### HotUpdate 文件解密失败

先怀疑 `HOT_UPDATE_KEY` 变化，排查顺序与 catalog 相同。不要因为一个 bundle 失败就改 AES key。

### 同名旧 bundle 被缓存

典型证据：

- catalog 中能找到新 primary key；
- 游戏目录中的 bundle 大小或修改时间比 `analysis/decrypted/` 中的同名文件更新；
- 缓存有合法 `UnityFS` 头，但容器里没有新 asset id。

先对 traceback 指向的单个 bundle 比较源文件和缓存，再运行完整更新。当前完整更新的强制刷新逻辑就是为此设计；不要退回到“只要有 UnityFS 头就复用”。

### bundle 有 `UnityFS` 头但 UnityPy 报 LZ4 解压失败

常见原因：

- `HEO_HASH_METADATA_OFFSET` 已变化；
- catalog、`GameAssembly.dll`、`global-metadata.dat` 不属于同一版本；
- `HeoStream.Cipher()` 算法发生变化。

排查顺序：

1. 确认游戏更新已完成，重新解密 catalog。
2. 只选择一个确定存在的失败 bundle，用 `--bundle-name` 解密并用 UnityPy 加载。
3. 打印 `heo_params()` 的 `key` 和 `reserved_pos`。如果 128 项数组包含大量 `0`、字符串样的大整数或离谱位置，优先怀疑元数据偏移，而不是 Cipher 算法。
4. 使用当前 `GameAssembly.dll` 和 `global-metadata.dat` 运行 Il2CppDumper，定位 `UnityEngine.ResourceManagement.ResourceProviders.HeoStream`。
5. 检查 `.ctor`、`Cipher` 和 `.cctor`：确认固定 key、逐 8 字节 XOR 逻辑，以及 `.cctor` 通过 `RuntimeHelpers.InitializeArray` 初始化的 128 项 `int[] s_Hash`。
6. 在 `dump.cs` 的 `<PrivateImplementationDetails>` 中找到被该 `.cctor` 引用的 512 字节静态数组，使用它标注的 `Metadata offset` 更新 `HEO_HASH_METADATA_OFFSET`。
7. 先验证单个 bundle 能被 UnityPy 加载，再运行完整更新。

2026-07-16 当前版本的已验证结果：

- `HEO_HASH_METADATA_OFFSET = 0x17A0010`
- `s_Hash` 是 128 个整数，当前恰为 `128..255` 的排列
- `HeoStream` 固定 key 仍为 `0x7C`
- `Cipher` 算法未变化，变化的只是静态数组位置

这些值是版本证据，不是永久常量。下次游戏更新后必须重新验证，不能盲目复用。

### 配置表找不到

如果 `Achievement`、`Hero`、`Occupation`、`Variant`、`Item`、`ItemTag`、`SelectableScene` 读取失败：

1. 确认配置 bundle 已由当前 catalog 定位和刷新。
2. 枚举相似 primary key。
3. 再考虑修改 `text_asset_bytes()` 的 key 构造或 resource type 筛选。

### 中文本地化找不到

先枚举当前 catalog 中的 `I2LanguagesFull_*` key，再更新 `LOCALIZATION_PRIMARY_KEYS` 或语言索引。不要从旧生成文件反向抄中文名。

### 成就图标被清空

这通常说明资源清单没有先生成，或图标源全部缺失。当前保护逻辑会在成就图标全缺失时直接报错，不再继续删除站点图标。

如果只缺少少量图标，也应视为未完成：检查资源组的 catalog/export 数量、对应 primary key 和依赖 bundle。

## 2026-07-16 参考基线

这次成功同步的报告是：

- 动物：70，带图：70，特征：11
- 成就：116，成就图片：116
- 地图筛选：24
- portraits：151 / 151
- portrait_alpha：151 / 151
- achievements：119 / 119
- perks：110 / 110
- 新动物：`H0073@1.16`，米卢 / Milou，图片 `images/animals/H0073@1.16.png`
- 新场景资源包括：荒岛环线、猛兽摇滚乐、天空遗迹
- `AE_005198_FightClub_SummerCabin` 的当前本地化是“夏季小屋”

这些数字只用于发现异常变化，不应写成永久断言。游戏新增或删除内容后，以当前配置表、catalog 和同步报告为准。

## 交付前检查清单

1. 游戏更新已经完成，关键源文件在同步期间保持稳定。
2. 所有同步脚本 `py_compile` 通过。
3. 完整更新可以跑通。
4. 完整更新中各资源组 `exported_count == catalog_sprite_count`。
5. `animals_with_image == animals`，动物和成就 `images_missing == 0`。
6. `python -X utf8 analysis\update_from_game.py --skip-decrypt` 可以跑通且结果幂等。
7. `analysis/extracted/resources_manifest.json` 存在。
8. `data/achievements.generated.js` 不包含 `sceneId`、`mapNameEn`、`sceneName`、`sceneMatch`。
9. 动物图片路径为 `images/animals/H*.png`，引用数、文件数和动物数一致。
10. 成就图片路径为 `images/achievements/ACV*.png`，文件数和成就数一致。
11. 新增场景没有错误劫持旧教程、剧情或特殊模式成就。
12. `git diff --check` 通过，生成数据 diff 已人工核对。
13. `git status` 中没有意外缓存、临时工具、测试 bundle 或日志。
