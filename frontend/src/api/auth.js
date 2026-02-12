import api from './index'

/**
 * 用户注册
 * @param {Object} data - 注册数据 { username, email, password, full_name, phone }
 */
export const register = (data) => {
  return api.post('/auth/register', data)
}

/**
 * 用户登录
 * @param {Object} data - 登录数据 { username, password }
 */
export const login = (data) => {
  return api.post('/auth/login', data)
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = () => {
  return api.get('/auth/me')
}
