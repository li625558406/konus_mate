import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sendMessage } from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref([])
  const sending = ref(false)
  const error = ref(null)

  /**
   * 发送消息（支持上下文）
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

      // 构建完整的对话上下文列表
      const messagesContext = messages.value.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      // 发送请求
      const response = await sendMessage({
        messages: messagesContext,
        system_instruction: options.systemInstruction,
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
  }

  return {
    // State
    messages,
    sending,
    error,
    // Actions
    send,
    clearMessages,
  }
})
