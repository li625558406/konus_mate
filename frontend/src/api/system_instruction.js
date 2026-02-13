import api from './index'

/**
 * 获取系统提示词列表
 * @param {boolean} isActive - 筛选启用状态
 * @param {number} skip - 跳过数量
 * @param {number} limit - 返回数量
 */
export const getSystemInstructions = (isActive = true, skip = 0, limit = 100) => {
  return api.get('/system-instructions', {
    params: { is_active: isActive, skip, limit }
  })
}

/**
 * 获取默认系统提示词
 */
export const getDefaultSystemInstruction = () => {
  return api.get('/system-instructions/default')
}
