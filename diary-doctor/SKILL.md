---
name: diary-doctor
description: |
  前后端代码健康检查：扫描类型不一致、死代码、未处理错误、内存泄漏等问题。
  触发词：代码检查、health check、diary doctor、代码健康
allowed-tools: [Bash, Read, AskUserQuestion]
---

# diary-doctor

扫描 dear-diary 前后端项目的代码健康问题。

## 使用

```bash
# 检查前端
python ~/dev/dear-diary-skills/diary-doctor/scripts/diary_doctor.py \
  --project ~/dev/dear-diary --type frontend

# 检查后端
python ~/dev/dear-diary-skills/diary-doctor/scripts/diary_doctor.py \
  --project ~/dev/dear-diary-server --type backend

# 同时检查前后端
python ~/dev/dear-diary-skills/diary-doctor/scripts/diary_doctor.py \
  --frontend ~/dev/dear-diary --backend ~/dev/dear-diary-server
```

## 检查项

| 类别 | 检查内容 |
|------|----------|
| 类型安全 | model/types 字段不一致、前后端类型不匹配 |
| 死代码 | 未使用的 export、空文件、未导入的组件 |
| 错误处理 | 空 catch、未 await 的 Promise、fire-and-forget |
| 内存泄漏 | 未清理的 setTimeout/setInterval、未卸载的监听器 |
| 导入 | 未使用的 import、缺失的依赖 |

## 输出

JSON 报告，按严重程度分级（critical / warning / info），包含文件路径和行号。
