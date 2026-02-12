import api from './index'

/**
 * 发送聊天消息
 * @param {Object} data - 聊天请求 { message, session_id?, system_instruction_id?, prompt_id?, temperature?, max_tokens? }
 */
export const sendMessage = (data) => {
  return api.post('/chat', data)
}

/**
 * 获取会话列表
 * @param {string} userId - 用户ID
 * @param {number} limit - 限制数量
 */
export const getSessions = (userId = 'default_user', limit = 50) => {
  return api.get('/chat/sessions', {
    params: { user_id: userId, limit }
  })
}

/**
 * 获取会话详情
 * @param {string} sessionId - 会话ID
 */
export const getSession = (sessionId) => {
  return api.get(`/chat/sessions/${sessionId}`)
}

/**
 * 获取会话消息列表
 * @param {string} sessionId - 会话ID
 */
export const getSessionMessages = (sessionId) => {
  return api.get(`/chat/sessions/${sessionId}/messages`)
}
