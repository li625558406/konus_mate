# Konus Mate Frontend

企业级 AI 助手前端应用 - Vue 3 + Vite + Tailwind CSS

## 技术栈

- **Vue 3** - Composition API
- **Vite** - 极速开发服务器
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **Tailwind CSS** - 原子化 CSS 框架

## 设计风格

**简约清新、高级、浅色主题**

- **配色**: 金棕色 + 橄榄绿 + 纯白/浅灰背景
- **字体**: Playfair Display (优雅衬线) + Inter (简洁无衬线)
- **视觉**: 柔和阴影、细腻边框、微妙点状背景
- **动画**: 淡入淡出、轻微缩放、平滑过渡

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/          # API 接口封装
│   ├── stores/       # Pinia 状态管理
│   ├── router/        # Vue Router 配置
│   ├── views/         # 页面组件
│   ├── App.vue        # 根组件
│   └── main.js       # 应用入口
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

## 页面

- `/login` - 登录页
- `/register` - 注册页
- `/chat` - 聊天界面（需要登录）

## 功能特性

### ✅ 上下文对话支持
- **自动加载会话历史**（最近 15 条消息）
- **实现真正的多轮对话能力**
- **智能截断**避免 token 超限（保留最近 15 条）
- **历史消息格式转换**适配 litellm API

### ✅ 聊天功能
- 实时发送消息
- 打字机效果（AI 回复时）
- 消息自动滚动到底部
- 新建会话
- 会话历史管理
- 退出登录

### ✅ 用户体验
- 加载状态指示器
- 错误提示
- 输入验证（注册页）
- 响应式设计
- 优雅的过渡动画

## 测试账号

后端初始化后可使用以下账号测试：

1. `admin / Test123456` - 管理员账户
2. `testuser / Test123456` - 普通用户

## API 配置

默认代理配置指向 `http://localhost:8000`

可在 `vite.config.js` 中修改代理目标。
