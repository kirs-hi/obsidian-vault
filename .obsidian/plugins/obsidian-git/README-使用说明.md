# Obsidian Git 使用说明（已为你预配置）

你当前已安装 obsidian-git，且我已经写入推荐配置到：
`.obsidian/plugins/obsidian-git/data.json`

## 这份配置做了什么

- 每 10 分钟自动 commit（`autoSaveInterval=10`）
- 每 10 分钟自动 push（`autoPushInterval=10`）
- 每 10 分钟自动 pull（`autoPullInterval=10`）
- 启动 Obsidian 时自动 pull（`autoPullOnBoot=true`）
- push 前先 pull（`pullBeforePush=true`）
- 冲突策略使用 merge（`syncMethod=merge`）
- 不再弹“没有变化”的提示（`disablePopupsForNoChanges=true`）

## 重要前提（你现在缺这一步）

当前 `/Users/szx/Documents/red` 目录还不是 Git 仓库（没有 `.git`）。
如果不先初始化 Git，插件不会真正同步。

在终端执行下面命令（把 URL 换成你的仓库）：

```bash
cd /Users/szx/Documents/red
git init
git branch -M main
git remote add origin https://github.com/<你的用户名>/<你的仓库>.git

# 可选：避免同步本机界面状态
echo '.DS_Store
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache/
.trash/' > .gitignore

git add .
git commit -m "init obsidian vault"
git push -u origin main
```

## 日常使用方法

日常编辑时你基本不用管，插件会自动同步。你也可以手动触发：

- 打开命令面板（`Cmd/Ctrl + P`）
- 输入 `Obsidian Git: Create backup`
- 或执行 `Obsidian Git: Pull` / `Obsidian Git: Push`

## 冲突处理建议

如果你多设备同时改同一篇笔记，可能出现冲突：

1. 先执行 Pull
2. 按提示打开冲突文件
3. 保留你想要的版本后保存
4. 再执行 Create backup / Push
