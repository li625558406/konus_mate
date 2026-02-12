# Konus Mate - AI Backend Application

企业级 AI 后端应用，基于 FastAPI + LiteLLM + PostgreSQL 构建。

## 技术栈

- **Web 框架**: FastAPI 0.115.0
- **LLM 集成**: LiteLLM 1.81.6 (智谱 AI)
- **数据库**: PostgreSQL + SQLAlchemy 2.0 (异步)
- **数据验证**: Pydantic 2.9
- **未来扩展**: LangChain, LangGraph

## 项目结构

```
konus-mate/
├── app/
│   ├── api/              # API 路由
│   │   ├── dependencies.py
│   │   └── routes/
│   ├── core/             # 核心配置
│   │   └── config.py
│   ├── db/               # 数据库连接
│   │   └── session.py
│   ├── models/           # 数据库模型
│   │   ├── chat.py
│   │   ├── system_instruction.py
│   │   └── prompt.py
│   ├── schemas/          # Pydantic Schema
│   ├── services/         # 业务逻辑服务
│   │   ├── litellm_service.py
│   │   ├── chat_service.py
│   │   ├── system_instruction_service.py
│   │   └── prompt_service.py
│   └── main.py           # 应用入口
├── scripts/
│   └── init_db.py        # 数据库初始化脚本
├── .env.example          # 环境变量示例
└── requirements.txt      # 依赖列表
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
ZHIPU_API_KEY=your-zhipu-api-key-here
DB_HOST=89.208.242.21
DB_PORT=15432
DB_NAME=mate_db
DB_USER=konus
DB_PASSWORD=LGligang
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 启动服务

```bash
python -m app.main
```

或使用 uvicorn：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 聊天接口
- `POST /api/v1/chat` - 发送聊天消息
- `GET /api/v1/chat/sessions` - 获取会话列表
- `GET /api/v1/chat/sessions/{session_id}` - 获取会话详情
- `GET /api/v1/chat/sessions/{session_id}/messages` - 获取会话消息

### 系统提示词
- `GET /api/v1/system-instructions` - 获取列表
- `POST /api/v1/system-instructions` - 创建
- `GET /api/v1/system-instructions/default` - 获取默认
- `PUT /api/v1/system-instructions/{id}` - 更新
- `DELETE /api/v1/system-instructions/{id}` - 删除

### Prompts
- `GET /api/v1/prompts` - 获取列表
- `POST /api/v1/prompts` - 创建
- `GET /api/v1/prompts/default` - 获取默认
- `PUT /api/v1/prompts/{id}` - 更新
- `DELETE /api/v1/prompts/{id}` - 删除

## 数据库表

### chat_sessions
聊天会话表，存储用户对话会话

### chat_messages
聊天消息表，存储单条消息内容

### system_instructions
系统提示词表，存储 AI 的系统级指令

### prompts
Prompt 表，存储对话提示词模板

## 默认测试数据

初始化后自动插入：

- **System Instructions** (3条): 通用助手(默认), 编程专家, 创意写作助手
- **Prompts** (5条): 默认对话(默认), 简洁专业, 详细解释, 代码审查, 头脑风暴

## License

MIT
