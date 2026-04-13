---
name: ai-prompt-lab
description: |
  Prompt 版本管理 + A/B 测试 + LLM-as-judge 自动评分。
  管理 dear-diary-server 中 aiService.ts 的 prompt 迭代。
  触发词：prompt 测试、prompt 版本、A/B 测试、prompt lab
allowed-tools: [Bash, Read, AskUserQuestion]
---

# ai-prompt-lab

管理 AI 日记回复的 prompt 版本，支持 A/B 对比测试和 LLM 自动评分。

## 使用

```bash
# 列出所有 prompt 版本
python ~/dev/dear-diary-skills/ai-prompt-lab/scripts/prompt_lab.py list

# 保存一个 prompt 版本（从文件读取）
python ~/dev/dear-diary-skills/ai-prompt-lab/scripts/prompt_lab.py save \
  --name v2-empathy --file prompt.txt --type reply

# 用同一输入对比两个版本的输出
python ~/dev/dear-diary-skills/ai-prompt-lab/scripts/prompt_lab.py test \
  --v1 v1-default --v2 v2-empathy --input "今天和朋友吵架了，心情很差"

# LLM-as-judge 自动评分对比
python ~/dev/dear-diary-skills/ai-prompt-lab/scripts/prompt_lab.py judge \
  --v1 v1-default --v2 v2-empathy --input "今天和朋友吵架了"
```

## Prompt 类型

| 类型 | 说明 | 对应 aiService.ts |
|------|------|-------------------|
| `reply` | 日记回复 prompt | analyzeDiarySentiment |
| `summary` | 摘要 prompt | analyzeDiarySentiment (summary) |
| `extract` | 人物/关键词提取 prompt | extractPeopleAndKeywords |

## 评分维度（judge 命令）

| 维度 | 说明 | 分值 |
|------|------|------|
| 自然度 | 像朋友聊天，不像 AI | 1-5 |
| 共情度 | 理解情绪，不说空话 | 1-5 |
| 具体性 | 回应具体细节，不泛泛而谈 | 1-5 |
| 长度合规 | 100-200 字 | 1-5 |

## 存储

`~/.dear-diary-skills/prompt-lab/versions/` 下按名称存储 prompt 文本文件。
