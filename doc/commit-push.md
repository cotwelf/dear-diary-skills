---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git push:*), Bash(cat package.json:*), Read
description: 提交本次所有改动并推送到远程仓库
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Remote repository (from package.json): !`node -e "const p=JSON.parse(require('fs').readFileSync('package.json','utf8')); console.log(p.repository?.url || p.repository || 'not set')"`

## Your task

提交当前项目的所有改动并推送到远程仓库。步骤：

1. `git add -A` 暂存所有改动
2. 根据 diff 内容生成中文 commit message，简洁描述改动要点
3. `git commit` 提交
4. 从 package.json 的 repository.url 获取远程地址，确认 origin 已设置（未设置则 `git remote add origin <url>`）
5. `git push origin <当前分支>`（如果远程没有该分支则加 `-u`）

要求：
- commit message 用中文，一行主题 + 空行 + 要点列表（如有多项改动）
- 一次性完成所有操作，不要发送多余文字
