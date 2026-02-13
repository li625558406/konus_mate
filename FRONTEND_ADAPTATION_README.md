# 前端适配说明

## 已完成的修改

### 1. Chat Store 更新 (`frontend/src/stores/chat.js`)

**新增功能：**
- ✅ 消息历史持久化到 localStorage
- ✅ 自动保存/恢复对话历史
- ✅ 新增计算属性：`messageCount`、`shouldWarnAboutCount`、`conversationRound`
- ✅ 自动触发记忆保存（后端判断）

**关键代码：**
```javascript
// 从localStorage恢复消息历史
const loadMessagesFromStorage = () => {
  const stored = localStorage.getItem('chat_messages')
  if (stored) {
    messages.value = JSON.parse(stored)
  }
}

// 监听messages变化，自动保存
watch(() => messages.value, () => {
  saveMessagesToStorage()
}, { deep: true })

// 后端会从messages数组长度判断对话次数
const response = await sendMessage({
  messages: messagesContext,  // 完整的对话历史
  system_instruction_id: options.systemInstructionId,
  temperature: options.temperature,
  max_tokens: options.maxTokens,
})
```

### 2. 记忆管理 API (`frontend/src/api/memory.js`)

**新增接口：**
```javascript
// 获取用户记忆列表
getMemories({ system_instruction_id: 1 })

// 删除指定记忆
deleteMemory(memoryId)

// 清理旧记忆
clearOldMemories({ system_instruction_id: 1, months: 3 })
```

### 3. 记忆管理 Store (`frontend/src/stores/memory.js`)

**功能：**
- ✅ 加载记忆列表
- ✅ 删除指定记忆
- ✅ 清理旧记忆
- ✅ 格式化关键点和时间

### 4. Chat.vue 界面更新

**新增UI组件：**

1. **对话统计卡片**
   - 显示消息总数
   - 接近50条时显示警告
   - 显示已完成对话清洗轮次

2. **记忆管理面板**
   - 显示最近5条记忆
   - 删除指定记忆
   - 一键清理3个月前的旧记忆
   - 刷新记忆列表

## 使用方式

### 对话流程

1. **发送消息**
   ```javascript
   await chatStore.send("你好", {
     systemInstructionId: 1
   })
   ```

   后端自动处理：
   - 从 `messages.length` 判断对话次数
   - 第50次触发AI清洗并保存记忆
   - 超过50次只保留后10条消息
   - 使用RAG检索相关记忆

2. **查看统计**
   ```javascript
   console.log(chatStore.messageCount)      // 消息总数
   console.log(chatStore.shouldWarnAboutCount)  // 是否需要警告
   console.log(chatStore.conversationRound)     // 当前对话轮次
   ```

3. **管理记忆**
   ```javascript
   // 加载记忆列表
   await memoryStore.loadMemories(systemInstructionId)

   // 删除记忆
   await memoryStore.removeMemory(memoryId)

   // 清理旧记忆
   await memoryStore.clearOld(systemInstructionId, 3)
   ```

## 后端逻辑说明

### 对话次数判断
后端从 `messages` 数组长度判断：
- `messages.length === 50` → 触发第1次清洗
- `messages.length === 100` → 触发第2次清洗
- `messages.length > 50` → 只保留后10条消息

### 记忆保存时机
每50次对话自动触发：
1. AI分析对话内容
2. 提取关键信息（个人信息、喜好等）
3. 保存到 `conversation_memories` 表
4. 生成向量嵌入用于RAG检索

### RAG检索
每次聊天时自动：
1. 检索相关记忆（向量相似度搜索）
2. 将记忆追加到 `prompt` 参数（不是 system_instruction）
3. AI根据记忆提供个性化回复

## 前端关键点

### 1. 维护完整消息历史
```javascript
// ✅ 正确：发送完整历史
const messagesContext = messages.value.map(msg => ({
  role: msg.role,
  content: msg.content,
}))
await sendMessage({ messages: messagesContext })

// ❌ 错误：只发送最后一条
await sendMessage({
  messages: [{ role: 'user', content: lastMessage }]
})
```

### 2. localStorage 持久化
- 自动保存：监听 `messages` 变化
- 自动恢复：页面刷新后恢复历史
- 清空对话：同时清除 localStorage

### 3. 切换系统指令时切换记忆
记忆按 `system_instruction_id` 分组存储，切换助手时显示对应的记忆。

## UI 显示

### 对话统计
```
┌─────────────────┐
│ 对话统计        │
│ 消息总数：47   │
│ ⚠️ 接近50条消息 │
└─────────────────┘
```

### 记忆管理
```
┌─────────────────┐
│ 记忆管理    [刷新]│
│                 │
│ • 用户介绍了自己的│ [×]
│   姓名和兴趣爱好│  2天前  │
│                 │
│ • 用户询问了编程 │ [×]
│   学习建议      │  1周前  │
│                 │
│ [清理3个月前的记忆]│
└─────────────────┘
```

## 注意事项

1. **前端不需要判断50次**
   - 后端从 `messages.length` 自动判断
   - 前端只需维护完整的消息数组

2. **messages 自动裁剪**
   - 后端会自动只保留后10条
   - 前端可以继续维护完整历史（用于localStorage）
   - 下次发送时后端会自动处理

3. **记忆自动加载**
   - 切换系统指令时自动加载对应记忆
   - 可以手动点击"刷新"按钮更新

4. **向量模型首次加载**
   - sentence-transformers 首次使用需要下载模型（~200MB）
   - 如果未安装，自动回退到关键词匹配

## 测试建议

1. **测试对话次数**
   - 发送50条消息，观察统计提示
   - 第51条时观察后端是否只保留后10条

2. **测试记忆保存**
   - 提供个人信息："我叫张三，喜欢编程"
   - 查看记忆列表是否出现

3. **测试RAG检索**
   - 第60条时询问："我的名字是什么？"
   - AI应该能从记忆中回答

4. **测试记忆管理**
   - 删除指定记忆
   - 清理旧记忆
   - 切换系统指令查看不同记忆
