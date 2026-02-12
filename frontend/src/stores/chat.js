import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sendMessage, getSessions, getSessionMessages } from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  // State
  const sessions = ref([])
  const currentSession = ref(null)
  const messages = ref([])
  const loading = ref(false)
  const sending = ref(false)
  const error = ref(null)

  // Computed
  const hasSessions = computed(() => sessions.value.length > 0)

  /**
   * 发送消息
   */
  const send = async (messageContent, options = {}) => {
    sending.value = true
    error.value = null
    try {
      const response = await sendMessage({
        message: messageContent,
        session_id: currentSession.value?.id || undefined,
        system_instruction_id: options.systemInstructionId,
        prompt_id: options.promptId,
        temperature: options.temperature,
        max_tokens: options.maxTokens,
      })

      const { session_id, message } = response.data

      // 如果是新会话，设置为当前会话
      if (!currentSession.value || currentSession.value.id !== session_id) {
        currentSession.value = { id: session_id }
      }

      // 添加消息到列表
      messages.value.push({
        role: 'user',
        content: messageContent,
      })
      messages.value.push({
        role: 'assistant',
        content: message.content,
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
   * 加载会话列表
   */
  const loadSessions = async (userId = 'default_user') => {
    loading.value = true
    error.value = null
    try {
      const response = await getSessions(userId)
      sessions.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '加载会话列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载会话消息
   */
  const loadMessages = async (sessionId) => {
    loading.value = true
    error.value = null
    try {
      const response = await getSessionMessages(sessionId)
      messages.value = response.data
      currentSession.value = { id: sessionId }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '加载消息失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建新会话
   */
  const createNewSession = () => {
    currentSession.value = null
    messages.value = []
    error.value = null
  }

  /**
   * 清除当前消息
   */
  const clearMessages = () => {
    messages.value = []
  }

  return {
    // State
    sessions,
    currentSession,
    messages,
    loading,
    sending,
    error,
    // Computed
    hasSessions,
    // Actions
    send,
    loadSessions,
    loadMessages,
    createNewSession,
    clearMessages,
  }
})
