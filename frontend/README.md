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

赛博朋克/未来科技风格
- 深色背景 + 霓虹渐变效果
- 玻璃态卡片设计
- 粒子动画背景
- 独特的科技感字体 (Orbitron + Rajdhani)

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
│   ├── api/           # API 接口封装
│   ├── stores/        # Pinia 状态管理
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

## 测试账号

后端初始化后可使用以下账号测试：

1. admin / Test123456 (管理员)
2. testuser / Test123456 (普通用户)

## API 配置

默认代理配置指向 `http://localhost:8000`

可在 `vite.config.js` 中修改代理目标。
