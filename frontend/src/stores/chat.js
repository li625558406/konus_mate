import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { sendMessage } from '@/api/chat'

const MESSAGES_STORAGE_KEY = 'chat_messages'

// 前端消息截取配置
//const TRIGGER_MESSAGE_COUNT = 60    // 触发截取的消息总数
//const KEEP_MESSAGE_COUNT = 10        // 截取后保留的最新消息数

const TRIGGER_MESSAGE_COUNT = 10    // 触发截取的消息总数
const KEEP_MESSAGE_COUNT = 5        // 截取后保留的最新消息数

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref([])
  const sending = ref(false)
  const error = ref(null)

  // 从localStorage恢复消息历史
  const loadMessagesFromStorage = () => {
    try {
      const stored = localStorage.getItem(MESSAGES_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        messages.value = parsed
      }
    } catch (err) {
      console.error('Failed to load messages from storage:', err)
      messages.value = []
    }
  }

  // 保存消息到localStorage
  const saveMessagesToStorage = () => {
    try {
      localStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(messages.value))
    } catch (err) {
      console.error('Failed to save messages to storage:', err)
    }
  }

  // 初始化时加载消息
  loadMessagesFromStorage()

  // 监听messages变化，自动保存
  watch(() => messages.value, () => {
    saveMessagesToStorage()
  }, { deep: true })

  /**
   * 发送消息（支持上下文）
   * 前端消息管理：
   * - 当消息长度等于 60 时，删除前 50 条，保留最新 10 条
   * - 后端会在第 50 次对话时触发 AI 清洗并保存记忆
   */
  const send = async (messageContent, options = {}) => {
    sending.value = true
    error.value = null

    try {
      // 添加用户消息到上下文列表
      messages.value.push({
        role: 'user',
        content: messageContent,
      })

      // 当消息长度达到阈值时，删除旧消息，保留最新的N条
      if (messages.value.length === TRIGGER_MESSAGE_COUNT) {
        messages.value = messages.value.slice(-KEEP_MESSAGE_COUNT)
        console.log(`消息数量达到${TRIGGER_MESSAGE_COUNT}，已删除前${TRIGGER_MESSAGE_COUNT - KEEP_MESSAGE_COUNT}条，保留最新${KEEP_MESSAGE_COUNT}条`)
      }

      // 构建完整的对话上下文列表（发送完整的消息历史给后端）
      const messagesContext = messages.value.map(msg => ({
        role: msg.role,
        content: msg.content,
      }))

      // 发送请求（后端会从messages数组长度判断对话次数）
      const response = await sendMessage({
        messages: messagesContext,  // 完整的对话历史
        system_instruction_id: options.systemInstructionId,
        temperature: options.temperature,
        max_tokens: options.maxTokens,
      })

      // 添加助手回复到上下文列表
      messages.value.push({
        role: 'assistant',
        content: response.data.message,
      })

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '发送消息失败'
      throw err
    } finally {
      sending.value = false
    }
  }

  /**
   * 清除当前消息
   */
  const clearMessages = () => {
    messages.value = []
    localStorage.removeItem(MESSAGES_STORAGE_KEY)
  }

  // 计算属性：消息总数（用于判断是否接近50次）
  const messageCount = computed(() => messages.value.length)

  // 计算属性：是否需要警告（接近50条）
  const shouldWarnAboutCount = computed(() => {
    const count = messages.value.length
    return count >= 45 && count < 50
  })

  // 计算属性：对话轮次
  const conversationRound = computed(() => {
    const count = messages.value.length
    return Math.floor(count / 50) * 50
  })

  return {
    // State
    messages,
    sending,
    error,
    // Computed
    messageCount,
    shouldWarnAboutCount,
    conversationRound,
    // Actions
    send,
    clearMessages,
  }
})
