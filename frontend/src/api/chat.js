import api from './index'

/**
 * 发送聊天消息（支持多轮对话上下文）
 * @param {Object} data - 聊天请求
 * @param {Array} data.messages - 对话上下文列表 [{role, content}, ...]
 * @param {string} data.system_instruction - 系统提示词内容（可选）
 * @param {number} data.system_instruction_id - 系统提示词ID（可选）
 * @param {number} data.temperature - 温度参数（可选）
 * @param {number} data.max_tokens - 最大token数（可选）
 */
export const sendMessage = (data) => {
  return api.post('/chat', data)
}
