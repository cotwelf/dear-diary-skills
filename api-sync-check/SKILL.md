---
name: api-sync-check
description: |
  前后端接口一致性校验：对比后端路由定义和前端 service 调用，检测不匹配。
  触发词：接口检查、api check、sync check、接口一致性
allowed-tools: [Bash, Read, AskUserQuestion]
---

# api-sync-check

对比 dear-diary 前后端的 API 定义，检测接口不匹配。

## 使用

```bash
python ~/dev/dear-diary-skills/api-sync-check/scripts/api_sync_check.py \
  --frontend ~/dev/dear-diary \
  --backend ~/dev/dear-diary-server
```

## 检查项

| 类别 | 检查内容 |
|------|----------|
| 路由覆盖 | 后端定义了但前端未调用的接口 |
| 幽灵调用 | 前端调用了但后端不存在的接口 |
| 方法不匹配 | GET/POST/PUT/DELETE 方法不一致 |
| 字段一致性 | 前端 transform 的字段与后端 model 对比 |

## 输出

表格形式展示匹配结果，标注不一致项。支持 `--json` 输出 JSON 格式。
