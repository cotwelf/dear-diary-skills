---
name: taro-page
description: |
  Taro 页面脚手架生成器，一键创建页面目录 + 自动注册路由。
  触发词：新页面、taro page、生成页面、页面脚手架
allowed-tools: [Bash, Read, Edit]
---

# taro-page

生成 Taro 页面脚手架（index.tsx + index.scss + index.config.ts）并自动注册到 app.config.ts。

## 使用

```bash
python ~/dev/dear-diary-skills/taro-page/scripts/gen_page.py \
  --name settings --title 设置 --project ~/dev/dear-diary
```

## 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--name` | 是 | 页面目录名（英文，如 settings） |
| `--title` | 是 | 导航栏标题（如 设置） |
| `--project` | 否 | 项目根目录，默认当前目录 |

## 生成内容

1. `src/pages/{name}/index.tsx` — React 函数组件
2. `src/pages/{name}/index.scss` — 漫画风格基础样式
3. `src/pages/{name}/index.config.ts` — definePageConfig
4. 自动追加路由到 `src/app.config.ts`
