---
name: ai-eval
description: |
  AI 输出质量批量评估工具。测试情感回复、人物提取、关键词提取的准确率。
  触发词：AI 评估、eval、批量测试、准确率、evaluation
allowed-tools: [Bash, Read, AskUserQuestion]
---

# ai-eval

批量评估 dear-diary AI 分析质量（回复、人物提取、关键词提取）。

## 使用

```bash
# 从现有日记生成测试用例
python ~/dev/dear-diary-skills/ai-eval/scripts/ai_eval.py gen-cases \
  --count 5 --source ~/dev/dear-diary-server/storage/diaries.json

# 用 LLM 生成带标注的测试用例
python ~/dev/dear-diary-skills/ai-eval/scripts/ai_eval.py gen-cases \
  --count 10 --synthetic

# 批量运行评估
python ~/dev/dear-diary-skills/ai-eval/scripts/ai_eval.py run \
  --cases ~/.dear-diary-skills/eval/cases.json

# 查看最近一次报告
python ~/dev/dear-diary-skills/ai-eval/scripts/ai_eval.py report
```

## 评估指标

| 任务 | 指标 | 说明 |
|------|------|------|
| 人物提取 | Precision / Recall / F1 | 与标注对比 |
| 关键词提取 | 覆盖率 | 标注关键词被提取的比例 |
| 回复质量 | LLM-as-judge 1-5 分 | 自然度 + 共情度 |
| 整体 | 平均耗时、失败率 | 稳定性指标 |

## 存储

`~/.dear-diary-skills/eval/` 下存测试用例和评估报告。
