# 对话记忆管理功能说明

## 功能概述

本次更新为 `/api/v1/chat` 接口添加了完整的对话记忆管理功能，包括：

1. **对话次数判断** - 直接从接口请求的 `messages` 数组长度判断
2. **AI清洗对话** - 每50次对话触发AI清洗，保留关键记忆
3. **RAG向量检索** - 使用 sentence-transformers 进行向量相似度搜索
4. **对话轮转** - 超过50次后保留后10条消息，避免token消耗过大
5. **记忆管理API** - 提供获取、删除、清理记忆的接口

## 数据表结构

### conversation_memories 表

存储清洗后的对话记忆，用于RAG检索。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键ID |
| user_id | Integer | 用户ID（外键） |
| system_instruction_id | Integer | 系统提示词ID（外键） |
| memory_type | String(20) | 记忆类型：active(主动记忆)/passive(被动记忆) |
| original_content | Text | 原始对话内容片段 |
| summary | Text | AI清洗后的记忆摘要 |
| key_points | Text | 关键点列表（JSON格式） |
| embedding | String(2000) | 向量嵌入（JSON数组字符串） |
| conversation_round | Integer | 对话轮次（50, 100, 150...） |
| importance_score | Integer | 重要性评分 1-10 |
| is_deleted | Boolean | 是否软删除 |
| deleted_at | DateTime | 删除时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 索引设计

- `ix_user_system_created` - (user_id, system_instruction_id, created_at)
- `ix_user_system_deleted` - (user_id, system_instruction_id, is_deleted)

## 核心逻辑流程

```
用户发送聊天请求
    ↓
从 messages 数组长度判断对话次数
    ↓
[如果达到50次] → 触发异步清洗 → AI分析并保存重要记忆
    ↓
[如果超过50次] → 只保留后10条消息 → 调用AI聊天
    ↓
RAG检索历史记忆 → 追加到系统提示词
    ↓
返回AI响应
    ↓
[异步] 软删除3个月前的旧记忆
```

## API接口说明

### 1. 聊天接口 (已更新)

**POST** `/api/v1/chat`

请求示例：
```json
{
  "messages": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    {"role": "user", "content": "我叫张三，喜欢编程"}
  ],
  "system_instruction_id": 1,
  "temperature": 0.7,
  "max_tokens": 1000
}
```

后端处理逻辑：
1. 从 `messages` 数组长度判断当前是第几次对话
2. 第50、100、150...次触发AI清洗并保存记忆
3. 第51次起只保留后10条消息
4. 使用向量相似度搜索检索相关记忆
5. **将检索到的记忆追加到prompt参数**（而非system_instruction）

### 2. 获取记忆列表

**GET** `/api/v1/memory/list?system_instruction_id=1`

响应示例：
```json
[
  {
    "id": 1,
    "summary": "用户介绍了自己的基本信息",
    "key_points": "[\"姓名：张三\", \"爱好：编程\"]",
    "memory_type": "active",
    "importance_score": 7,
    "created_at": "2025-01-15T10:30:00"
  }
]
```

### 3. 删除指定记忆

**DELETE** `/api/v1/memory/{memory_id}`

响应示例：
```json
{
  "message": "记忆已删除",
  "id": 1
}
```

### 4. 清理旧记忆

**POST** `/api/v1/memory/clear-old?months=3&system_instruction_id=1`

响应示例：
```json
{
  "message": "已清理 5 条旧记忆",
  "count": 5
}
```

## 前端适配建议

### 对话上下文管理

前端需要维护完整的对话历史 `messages` 数组：

```javascript
// 示例：前端维护对话历史
let messages = [];

async function sendMessage(userMessage) {
  // 添加用户消息
  messages.push({ role: "user", content: userMessage });

  // 调用聊天接口
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      messages: messages,  // 发送完整的对话历史
      system_instruction_id: 1
    })
  });

  const data = await response.json();

  // 添加AI回复
  messages.push({ role: "assistant", content: data.message });

  // 后端会自动判断是否超过50条并清洗
  // 前端不需要额外处理
}
```

### 记忆查看功能

```javascript
// 获取用户的所有记忆
async function getMemories() {
  const response = await fetch('/api/v1/memory/list', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const memories = await response.json();
  return memories;
}

// 清理旧记忆
async function clearOldMemories(months = 3) {
  const response = await fetch(`/api/v1/memory/clear-old?months=${months}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
}
```

## 依赖安装

向量相似度搜索需要 sentence-transformers：

```bash
pip install sentence-transformers numpy
```

如果未安装，系统会自动回退到简化的关键词匹配算法。

## 配置说明

常量配置位于 `app/services/chat_service.py`：

```python
CONVERSATION_BATCH_SIZE = 50  # 每50次对话触发清洗
CONVERSATION_KEEP_SIZE = 10    # 超过50次后保留后10条
```

可根据实际需求调整。

## AI清洗逻辑

AI会根据以下标准判断是否保存记忆：

1. **主动记忆（active）**：用户主动提到的个人信息、喜好、重要事件、情感状态等
2. **被动记忆（passive）**：用户明确要求AI记住的信息
3. **重要性评分**：1-10分，10分为最重要
4. **should_remember**：只有true的记忆才会被保存

清洗示例：

对话：
```
用户：我叫张三，喜欢编程和打篮球
AI：很高兴认识你张三！...
```

清洗后保存：
```json
{
  "summary": "用户介绍了自己的姓名和兴趣爱好",
  "key_points": ["姓名：张三", "爱好：编程", "爱好：打篮球"],
  "importance_score": 7,
  "should_remember": true,
  "memory_type": "active"
}
```

## 向量相似度搜索

RAG检索使用以下算法：

1. 使用 sentence-transformers 将文本编码为向量
2. 计算查询文本与记忆摘要的余弦相似度
3. 综合考虑相似度（70%）和重要性评分（30%）
4. 返回Top 5相关记忆

示例：

查询："我的爱好是什么？"

检索结果（按相似度排序）：
1. "用户介绍了自己的姓名和兴趣爱好" - 相似度0.85
2. "用户询问了编程学习建议" - 相似度0.62
3. "用户聊起了最近的篮球比赛" - 相似度0.58

## 注意事项

1. **对话次数计算**：后端从 `messages` 数组长度判断，前端需要发送完整历史
2. **软删除机制**：删除的记忆不会立即从数据库移除，只是标记为删除
3. **异步处理**：清洗和删除操作在后台异步执行，不影响聊天响应速度
4. **向量模型**：首次使用时会下载 sentence-transformers 模型（约200MB）

## 数据库初始化

运行初始化脚本创建新表：

```bash
python scripts/init_db.py
```

## 测试建议

1. 发送50条消息，观察日志中是否触发"对话清洗"
2. 发送51条消息，观察后端是否只保留后10条
3. 查询记忆列表，确认AI是否正确保存了关键信息
4. 测试向量相似度搜索是否返回相关记忆
