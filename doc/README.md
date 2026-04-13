# Dear Diary 📔

一个有温度的 AI 日记应用 —— 写日记，交笔友。

## 这是什么

Dear Diary 是一款小程序日记应用。你写下今天的故事，AI 笔友会像朋友一样给你回信。它不是冷冰冰的情感分析工具，而是一个懂你、记得你、会成长的日记伙伴。

## 亮点

### 🎨 漫画风 UI
手绘感的界面设计，厚边框、偏移阴影、暖色调渐变，让记录日常变成一件有趣的事。日记列表以弹幕形式呈现，每条日记像一颗飘过的星星。

### 🤖 AI 笔友
不是简单的"今天心情不错"式回复。AI 笔友会：
- 记住你之前写过什么（aiMemory 机制）
- 根据你的写作风格调整回复语气
- 像真正的朋友一样回应你的喜怒哀乐

写完日记点击保存，回复会在后台悄悄生成，下次打开就能看到笔友的来信。

### 🧠 智能理解
自动提取日记中提到的人物和关键词，通过向量嵌入找到相似的历史日记，让 AI 的回复更有上下文、更贴心。

### ⚡ 轻量架构
- 无数据库依赖，JSON 文件存储，开箱即用
- Ollama 本地 AI，数据不出本机，隐私安全
- AI 不可用时自动降级，核心功能不受影响

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Taro 4 + React 18 + TypeScript |
| 后端 | Koa2 + TypeScript |
| AI | Ollama (llama3.1:8b + nomic-embed-text) |
| 存储 | JSON 文件 |
| 平台 | 微信小程序 / H5 |

## 项目结构

```
dev/
├── dear-diary/          # 前端（Taro 小程序）
├── dear-diary-server/   # 后端（Koa API）
└── dear-diary-doc/      # 文档（你在这里）
    ├── README.md        # 项目简介（本文件）
    └── dev-guide.md     # 开发者指南
```

每个项目根目录都有 `CLAUDE.md`，供 AI 编码工具快速理解项目。

## 快速开始

```bash
# 启动后端
cd dear-diary-server
npm install && npm run dev

# 启动前端
cd dear-diary
npm install && npm run dev:weapp

# （可选）启动 Ollama AI
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

## 功能一览

- ✏️ 写日记：选心情、选天气、写内容
- 🤖 AI 回复：异步生成，像笔友来信
- 🔍 搜索：关键词搜索历史日记
- ⭐ 标记重要日记
- 🎭 11 种心情状态（0-10）
- 🌤️ 8 种天气选择
- 👥 自动提取人物和关键词
- 📊 向量相似度匹配历史日记

## 开发文档

详见 [开发者指南](dev-guide.md) —— 包含本地开发、新增功能的完整指引，以及如何高效地与 AI 编码工具协作。
