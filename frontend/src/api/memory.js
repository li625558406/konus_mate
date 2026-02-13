import api from './index'

/**
 * 获取用户记忆列表
 * @param {Object} params - 查询参数
 * @param {number} params.system_instruction_id - 系统提示词ID（可选）
 * @returns {Promise} 记忆列表
 */
export const getMemories = (params = {}) => {
  return api.get('/memory/list', { params })
}

/**
 * 删除指定记忆
 * @param {number} memoryId - 记忆ID
 * @returns {Promise} 删除结果
 */
export const deleteMemory = (memoryId) => {
  return api.delete(`/memory/${memoryId}`)
}

/**
 * 清理旧记忆
 * @param {Object} params - 查询参数
 * @param {number} params.system_instruction_id - 系统提示词ID（可选）
 * @param {number} params.months - 清理几个月前的记忆（默认3）
 * @returns {Promise} 清理结果
 */
export const clearOldMemories = (params = {}) => {
  return api.post('/memory/clear-old', null, { params })
}
