# 猛兽派对助手

一个给《猛兽派对》（Party Animals）做的静态查询站点。

它包含两个页面：

- 动物特征分类
- 成就地图分类

全部在浏览器端完成，没有后端依赖。站点资源来自游戏数据同步生成，支持离线使用。

## 功能

- 动物页支持多选特征筛选
- 成就页支持单选地图筛选
- 动物显示中文名、本体图片和特征
- 成就显示图标、名称和条件
- 使用本地离线字体 `fonts/NotoSansSC-VF.ttf`

## 资源来源

站点运行时直接读取这些生成文件：

- `data/animals.generated.js`
- `data/achievements.generated.js`
- `images/animals/`
- `images/achievements/`

`images/assets/` 提供站点图标和截图。

## 文件结构

```text
/
├── index.html
├── achievements.html
├── animals.css
├── app.js
├── data/
├── fonts/
├── images/
└── README.md
```

## 本地使用

直接打开 `index.html` 或 `achievements.html` 即可。

## 说明

- 这是一个纯前端站点
- 页面逻辑统一由 `app.js` 驱动
- 资源更新后，站点数据会重新生成并覆盖现有文件

