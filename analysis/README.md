# Party Animals 资源一键更新工具

这组脚本用于从本地《猛兽派对》游戏目录重新提取站点所需资源，并生成静态站点使用的数据与图片。

## 生成内容

运行成功后会更新：

- `data/animals.generated.js`
- `data/achievements.generated.js`
- `images/animals/H*.png`
- `images/achievements/ACV*.png`

中间产物会写入 `analysis/decrypted/` 和 `analysis/extracted/`。这些目录可重建，不应提交。

## 环境依赖

需要 Python 3.11+。

```powershell
python -m pip install UnityPy Pillow msgpack pycryptodome
```

## 一键完整同步

在仓库根目录运行：

```powershell
python -X utf8 analysis\update_from_game.py --game-dir "F:\SteamLibrary\steamapps\common\Party Animals"
```

脚本会依次执行：

1. 解密 HybridCLR 与 Addressables catalog
2. 导出资源清单和图标基础资源
3. 提取动物中文名、本体图片、特征
4. 提取成就中文名、达成条件、地图筛选和图标
5. 写入站点 generated 数据并同步图片

成功输出是 JSON 报告。当前版本的正常数量大致为：

- 动物：69
- 动物特征：11
- 成就：116
- 地图筛选：24

## 快速重建

如果已经存在 `analysis/decrypted/`，只修改了解析或同步脚本，可以跳过解密：

```powershell
python -X utf8 analysis\update_from_game.py --skip-decrypt --game-dir "F:\SteamLibrary\steamapps\common\Party Animals"
```

## 验证

语法检查：

```powershell
python -X utf8 -m py_compile analysis\extract_party_animals_web_assets.py analysis\build_party_animals_web_data.py analysis\export_party_animals_resource_index.py analysis\build_party_animals_achievement_map_index.py analysis\sync_site_animals.py analysis\sync_site_achievements.py analysis\update_from_game.py analysis\decrypt_party_animals.py analysis\scan_party_animals_assets.py
```

检查成就页面 payload 没有带内部调试字段：

```powershell
python -X utf8 -c "from pathlib import Path; t=Path('data/achievements.generated.js').read_text(encoding='utf-8'); print({k:t.count(k) for k in ['sceneId','mapNameEn','sceneName','sceneMatch']})"
```

期望结果：

```text
{'sceneId': 0, 'mapNameEn': 0, 'sceneName': 0, 'sceneMatch': 0}
```

检查图片引用数量：

```powershell
python -X utf8 -c "from pathlib import Path; print(Path('data/animals.generated.js').read_text(encoding='utf-8').count('images/animals/H')); print(Path('data/achievements.generated.js').read_text(encoding='utf-8').count('images/achievements/ACV'))"
```

## 文件说明

- `update_from_game.py`：一键入口
- `decrypt_party_animals.py`：解密 HybridCLR、catalog 和 bundle
- `extract_party_animals_web_assets.py`：解析 catalog，导出资源清单、头像、成就图标、技能图标
- `export_party_animals_resource_index.py`：生成动物资源索引
- `build_party_animals_achievement_map_index.py`：生成成就与地图索引
- `sync_site_animals.py`：同步动物 generated 数据和图片
- `sync_site_achievements.py`：同步成就 generated 数据和图片
- `scan_party_animals_assets.py`：游戏更新后用于排查结构变化
- `RESOURCE_SYNC_WORKFLOW.md`：更详细的维护与故障排查工作流

## 提交范围

可以提交：

- `analysis/*.py`
- `analysis/README.md`
- `analysis/RESOURCE_SYNC_WORKFLOW.md`
- 由同步生成并确认正确的 `data/`、`images/`、`fonts/` 站点资源

不要提交：

- `analysis/decrypted/`
- `analysis/extracted/`
- `analysis/il2cppdump_out*/`
- `analysis/__pycache__/`
- 扫描日志、dump 输出、临时 JSON
