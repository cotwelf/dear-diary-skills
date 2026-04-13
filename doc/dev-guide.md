# Dear Diary — 开发者指南

## 项目结构总览

Dear Diary 是一个 AI 日记应用，分为两个独立项目：

| 项目 | 路径 | 技术栈 | 说明 |
|------|------|--------|------|
| dear-diary | `../dear-diary` | Taro 4 + React 18 + TypeScript | 小程序前端 |
| dear-diary-server | `../dear-diary-server` | Koa2 + TypeScript | 后端 API |

两个项目各自有 `CLAUDE.md` 文件，供 AI 编码工具快速理解项目上下文。

---

## 本地开发

### 启动后端

```bash
cd ../dear-diary-server
npm install
npm run dev          # 默认 http://localhost:3000
```

需要 AI 功能时，确保 [Ollama](https://ollama.ai) 已启动并拉取了模型：

```bash
ollama pull llama3.1:8b         # AI 对话
ollama pull nomic-embed-text    # 向量嵌入
```

Ollama 不可用时自动降级为模拟数据，不影响基础功能。

### 启动前端

```bash
cd ../dear-diary
npm install
npm run dev:weapp    # 微信小程序
# 或
npm run dev:h5       # H5 浏览器
```

---

## 如何新增功能

### 场景 1：新增一个日记字段（如"地点"）

需要改动的文件（按顺序）：

**后端：**
1. `dear-diary-server/src/models/Diary.ts` — 在 `DiaryData` 和 `Diary` 类中添加字段
2. `dear-diary-server/src/types/index.ts` — 更新类型定义
3. `dear-diary-server/src/controllers/diaryController.ts` — 在 create/update 中处理新字段

**前端：**
4. `dear-diary/src/services/diary.ts` — 在 `BackendDiary`、`FrontendDiary`、`transformDiary` 中添加字段
5. `dear-diary/src/pages/detail/index.tsx` — 添加 UI 控件和状态

### 场景 2：新增一个 API 接口

**后端：**
1. `dear-diary-server/src/routes/diaryRoutes.ts`（或 `aiRoutes.ts`）— 添加路由
2. `dear-diary-server/src/controllers/` — 添加控制器方法
3. `dear-diary-server/src/services/` — 添加业务逻辑

**前端：**
4. `dear-diary/src/services/diary.ts` — 添加 API 调用方法
5. 在对应页面中调用

### 场景 3：新增一个页面

**前端：**
1. `dear-diary/src/pages/` 下新建目录，包含 `index.tsx`、`index.scss`、`index.config.ts`
2. `dear-diary/src/app.config.ts` — 在 `pages` 数组中注册路由
3. 在需要跳转的地方使用 `Taro.navigateTo({ url: '/pages/xxx/index' })`

### 场景 4：新增 AI 能力

**后端：**
1. `dear-diary-server/src/services/aiService.ts` — 添加方法，编写 prompt
2. 注意处理 `this.useMockData` 降级逻辑
3. 如需暴露接口，按场景 2 添加路由

---

## 如何告知 AI 编码工具

当你使用 Claude Code、Codex 等 AI 工具时，可以这样描述需求：

### 模板

```
在 [前端/后端/前后端] 项目中，[做什么]。

涉及文件：
- [文件路径]: [改什么]

参考现有实现：[类似功能的文件或方法名]
```

### 示例

```
在前后端项目中，给日记添加"地点"字段。

后端涉及文件：
- models/Diary.ts: 添加 location 字段
- controllers/diaryController.ts: create/update 处理 location
- types/index.ts: DiaryData 加 location

前端涉及文件：
- services/diary.ts: BackendDiary/FrontendDiary 加 location，transformDiary 映射
- pages/detail/index.tsx: 添加地点输入框，参考天气选择器的实现

参考现有实现：weather 字段的前后端处理方式
```

### 小贴士

- 告诉 AI 工具先读 `CLAUDE.md`，它会快速理解项目结构
- 指明"参考现有实现"可以让 AI 保持代码风格一致
- 前后端联动的需求，明确说"前后端都要改"，避免只改一端

---

## 关键约定

| 约定 | 说明 |
|------|------|
| 心情值 | number 0-10，前后端统一 |
| 天气 | 英文字符串传输（sunny/cloudy/...），前端转 emoji |
| 导航回首页 | 统一用 `Taro.redirectTo`，不用 `navigateBack` |
| 跨页通信 | 用 `Taro.eventCenter` |
| AI 分析 | 异步执行，不阻塞接口响应 |
| 数据存储 | JSON 文件，无数据库 |
| 样式单位 | rpx，375px 设计稿 |
| 设计风格 | 漫画风：厚边框 + 偏移阴影 + 暖色渐变背景 |
