# 本机定时运行方案

这个方案让 macOS 本机负责联网抓取和飞书交付，Codex 自动化负责检查报告和日志。

## 1. 迁移到适合后台任务的目录

如果项目还在 `Documents` 下，先迁移到 `~/Code/daily_ai_brief`，避免 macOS 隐私权限阻止 `launchd` 访问。

```bash
cd /Users/construct/Documents/Codex/2026-06-02/new-chat/work/daily_ai_brief
scripts/move_to_unprotected_dir.sh
```

迁移脚本会保留旧目录作为备份，并让 `launchd` 指向新目录。

## 2. 准备本地配置

```bash
cd ~/Code/daily_ai_brief
cp config.local.example.json config.local.json
cp .env.example .env
```

在 `.env` 中填写飞书凭证和可选的 `SEMANTIC_SCHOLAR_API_KEY`。

如果暂时不发送飞书，把 `config.local.json` 里的两个交付开关改成 `false`。

检查飞书配置是否填完整：

```bash
scripts/check_feishu_config.sh
```

## 3. 手动验证

```bash
scripts/run_daily_brief.sh
```

运行日志会写入 `logs/`，最近一次日志可看：

```bash
tail -n 80 logs/latest.log
```

## 4. 安装 macOS 定时任务

```bash
scripts/install_launchd.sh
```

安装后每天 `09:00` 运行一次，并且会在安装时立即运行一次。

## 5. Codex 自动化建议

把 Codex 自动化改成巡检型：

```text
进入 Daily AI Brief 项目，只检查本机定时任务产物，不直接联网抓取。读取 logs/latest.log 和今天 reports/ 下的最新 Markdown 报告：如果报告成功生成，说明报告路径和入选数量；如果日志显示非零 exit_code、连续空报告、飞书交付失败或当天没有报告，说明失败类型并回到线程提醒用户。不要把 Codex 自身网络失败当成项目失败。
```
