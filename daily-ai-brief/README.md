# Daily AI Brief

每天自动抓取可靠 AI 论文/文章，筛选 3-5 篇，生成简洁、可追溯的中文研究简报，并可选地创建飞书文档和发送飞书消息。

## 当前版本能做什么

- 从 arXiv 抓取 `cs.AI`、`cs.LG`、`cs.CL`、`cs.CV` 的最新论文。
- 从 Hugging Face Daily Papers 抓取社区热门论文入口。
- 从 Semantic Scholar 搜索补充候选论文和元信息。
- 从新闻媒体、官方博客 RSS 补充非论文类文章。
- 按关键词、来源可靠性、时间新鲜度、引用量信号做初筛。
- 为入选内容生成 Markdown 简报，并可导出 HTML / Word。
- 保留原始链接、PDF 链接、来源类型、摘要证据。
- 每篇生成基于本篇文章内容的 Mermaid 行文逻辑图。
- 预留飞书 API：配置好开放平台应用后，可自动创建在线文档并发送消息。

## 快速运行

第一次运行前安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

```bash
cd work/daily_ai_brief
python3 -m src.main --config config.example.json
```

报告会生成在 `reports/` 目录。

如果要让本机每天稳定定时运行，使用：

```bash
scripts/run_daily_brief.sh
```

本机 `launchd` 定时安装说明见 `docs/LOCAL_AUTOMATION.md`。

如果想把最新 Markdown 报告导出为 HTML / Word：

```bash
python3 scripts/export_outputs.py
```

导出的文件会生成在 `outputs/` 目录。

## 推荐仓库结构

- `src/`：核心程序。
- `scripts/`：辅助脚本，例如导出 HTML / Word。
- `docs/`：项目规划、仓库整理、后续接入说明。
- `config.example.json`：可公开的配置模板。
- `.env.example`：账号和密钥的填写模板。

`data/`、`reports/`、`outputs/` 都是每天运行时产生的内容，默认不上传 GitHub。

## 飞书自动交付

复制 `.env.example` 为 `.env`，补齐飞书开放平台信息：

```bash
cp .env.example .env
```

需要的能力：

- 创建云文档：飞书开放平台 Drive / Docs 权限。
- 写入文档内容：新版文档 `docx` 相关权限。
- 发送消息：`im:message:send_as_bot` 或等价机器人消息权限。

如果没有配置飞书凭证，脚本会只生成本地报告，不会失败退出。

## 推荐自动化节奏

每天上午 9 点运行一次。第一版建议每天只推 5 篇，宁缺毋滥。

## 质量原则

- 所有总结只基于原文标题、摘要、PDF、官方页面或 API 元信息。
- 预印本必须标注为预印本。
- 产品发散必须标注依据；没有依据时写“暂不判断”。
- 每篇必须保留原始链接和 PDF/资料链接。
