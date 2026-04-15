# dear-diary-skills

[Dear Diary](https://github.com/cotwelf/dear-diary) 项目的 Claude Code Skills 合集，围绕 AI 工程和前端提效。

## 架构

```
dear-diary-skills/
├── ai-prompt-lab/     Prompt 版本管理 + A/B 测试 + LLM-as-judge 评分
├── ai-eval/           AI 输出质量批量评估（人物提取/关键词/回复）
├── diary-doctor/      前后端代码健康检查（类型一致性/死代码/内存泄漏）
├── api-sync-check/    前后端接口一致性校验（路由覆盖/字段匹配）
└── taro-page/         Taro 页面脚手架一键生成
```

## Skills

### ai-prompt-lab

管理 `aiService.ts` 中的 prompt 迭代。保存不同版本的 prompt，用同一输入对比输出，用 LLM-as-judge 自动评分。

```bash
# 保存 prompt 版本
prompt_lab.py save --name v2-empathy --file prompt.txt --type reply

# A/B 对比
prompt_lab.py test --v1 v1-default --v2 v2-empathy --input "今天心情不好"

# LLM 自动评分
prompt_lab.py judge --v1 v1-default --v2 v2-empathy --input "今天心情不好"
```

评分维度：自然度、共情度、具体性、长度合规（各 1-5 分）。

### ai-eval

批量测试 AI 分析管线的准确率。支持从现有日记采样或用 LLM 合成测试用例。

```bash
# 生成测试用例
ai_eval.py gen-cases --count 10 --synthetic

# 批量评估
ai_eval.py run --cases cases.json

# 查看报告
ai_eval.py report
```

输出指标：人物提取 F1、关键词 F1、长度合规率、平均耗时、失败率。

### diary-doctor

扫描前后端代码的健康问题：类型不一致、死代码、空 catch、未清理定时器等。

```bash
# 同时检查前后端
diary_doctor.py --frontend ~/dev/dear-diary --backend ~/dev/dear-diary-server

# 单独检查
diary_doctor.py --project ~/dev/dear-diary-server --type backend
```

### api-sync-check

对比后端路由定义和前端 service 调用，检测接口不匹配、幽灵调用、字段缺失。

```bash
api_sync_check.py --frontend ~/dev/dear-diary --backend ~/dev/dear-diary-server
```

### taro-page

一键生成 Taro 页面（index.tsx + index.scss + index.config.ts）并自动注册路由。

```bash
gen_page.py --name settings --title 设置 --project ~/dev/dear-diary
```

## 依赖

- Python 3.10+
- [Ollama](https://ollama.ai)（ai-prompt-lab 和 ai-eval 需要）
- `ollama pull deepseek-r1:8b`

## 安装

```bash
./install.sh
```
