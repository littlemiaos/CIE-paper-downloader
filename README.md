# astrbot_plugin_cie_papers

AstrBot 插件：下载 Cambridge International (CIE/CAIE) 历年真题、答案、分数线、考官报告等 PDF。

默认数据源：[XtremePapers](https://papers.xtremepape.rs)，也支持自定义 API（目录结构相同的镜像）。

## 兼容版本

- 针对 **AstrBot v4.27.4** 编写，声明版本范围 `>=4.5,<5`，可直接加载。

## 安装方法

### 方式一：直接放入插件目录（推荐）

把整个 `astrbot_plugin_cie_papers` 文件夹复制到：

```
AstrBot/data/plugins/astrbot_plugin_cie_papers/
```

然后在 WebUI「插件」页刷新并启用。

### 方式二：WebUI 上传

1. 将本插件打包为 zip（`astrbot_plugin_cie_papers.zip`，压缩包内直接包含 `metadata.yaml`、`main.py` 等）。
2. WebUI → 插件 → 安装插件 → 上传 zip。
3. 若无法识别，请改用方式一。

## 依赖

- `aiohttp`（AstrBot 一般已内置）
- `PyMuPDF`（仅「图片」输出形式需要；如未安装，图片模式会自动退回文字/链接）

## 插件配置（WebUI 插件页可调）

| 配置项 | 可选值 / 说明 | 默认 |
| --- | --- | --- |
| 输出形式 | `pdf` 发送 PDF 文件 · `image` 转成图片(第1页预览) · `text` 仅发文字与链接 | `pdf` |
| 下载失败即停止 | 开启后某张卷失败立即停止后续下载 | 开 |
| 下载超时（秒） | 单个请求超时时间 | `60` |
| 下载源 | `xtremepapers` 默认源 · `custom` 自定义 | `xtremepapers` |
| 自定义 API 地址 | 留空用默认源；填写后需与默认源目录结构一致 | 空 |

> 修改配置后建议在插件页「重载插件」使配置生效。

## 使用方法

### 分步查找（推荐，无需记参数）

| 命令 | 说明 |
| --- | --- |
| `/cie list` | 查看所有科目与代码 |
| `/cie list igcse`（或 `alevel` / `olevel`） | 查看某个等级的科目 |
| `/cie list <代码>` | 查看该科目**可用卷号**与考季范围，如 `/cie list 0580` |
| `/cie list <代码> <考季>` | 查看某考季的具体文件，如 `/cie list 0580 s20` |

每步都会给出下一步提示，照着提示输入即可。

### 直接下载（熟练后）

```
/cie get 0580 s20 21        # IGCSE 数学 2020 年 5/6 月 Paper 21（试卷+答案）
/cie get 0580 s20 21 qp     # 仅试卷
/cie get 9709 w19 32 ms     # 仅答案
/cie get 0580 s 20 qp 21    # 分开写法
```

- **考季**：`s` = 5/6 月，`m` = 3 月，`w` = 10/11 月
- **类型**：`qp` 试卷，`ms` 答案，`gt` 分数线，`er` 考官报告，`all` 试卷+答案（默认）

## 常用科目代码

| 代码 | 科目 | 等级 |
| --- | --- | --- |
| 0580 | 数学 | IGCSE |
| 0620 | 化学 | IGCSE |
| 0625 | 物理 | IGCSE |
| 0610 | 生物 | IGCSE |
| 0455 | 经济 | IGCSE |
| 0478 | 计算机科学 | IGCSE |
| 9709 | 数学 | AS & A Level |
| 9701 | 化学 | AS & A Level |
| 9702 | 物理 | AS & A Level |
| 9700 | 生物 | AS & A Level |

完整列表用 `/cie list` 查询。

## 目录结构

```
astrbot_plugin_cie_papers/
├── main.py                  # 入口：命令注册与路由（精简）
├── _conf_schema.json        # 插件配置项定义
├── metadata.yaml
├── requirements.txt
└── cie_papers/              # 核心逻辑包
    ├── config.py            # 配置默认值 + 常量 + 科目兜底
    ├── http.py              # 异步 HTTP 客户端
    ├── resolver.py          # 科目解析 + 缓存
    ├── downloader.py        # PDF 下载器
    ├── output.py            # 输出形式（pdf/image/text）
    └── sources/
        ├── base.py          # 数据源抽象
        └── directory.py     # 目录型源（默认源与自定义 API 通用）
```

## 工作原理

1. 通过数据源的目录接口获取「科目代码 → 等级/目录名」映射并缓存 1 小时。
2. 根据代码、考季、年份、类型、卷号拼接直链 URL。
3. 按配置的输出形式处理：下载 PDF / 转图片 / 仅发链接。
4. 下载到系统临时目录，发送给用户（文件 + 直链双保险），超过 24 小时自动清理。

## 免责声明

- 本插件仅提供对公开托管文件的下载链接，不存储、不重新分发受版权保护的内容。
- 历年真题版权归 Cambridge Assessment International Education 所有，请仅用于个人学习用途。
- 默认数据源（XtremePapers）由第三方维护，如站点结构变化可能导致个别功能失效，此时可用 `/cie list` 重新核对。
