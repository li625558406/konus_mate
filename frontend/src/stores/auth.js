import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getCurrentUser } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('access_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.is_superuser || false)

  /**
   * 用户登录
   */
  const login = async (credentials) => {
    loading.value = true
    error.value = null
    try {
      const response = await loginApi(credentials)
      const { access_token, user: userData } = response.data

      // 保存到 localStorage
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))

      // 更新状态
      token.value = access_token
      user.value = userData

      return userData
    } catch (err) {
      error.value = err.response?.data?.detail || '登录失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户注册
   */
  const register = async (userData) => {
    loading.value = true
    error.value = null
    try {
      const response = await registerApi(userData)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '注册失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 登出
   */
  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    token.value = ''
    user.value = null
  }

  /**
   * 获取当前用户信息
   */
  const fetchCurrentUser = async () => {
    if (!token.value) return

    loading.value = true
    try {
      const response = await getCurrentUser()
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(response.data))
      return response.data
    } catch (err) {
      logout()
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    token,
    user,
    loading,
    error,
    // Computed
    isAuthenticated,
    isAdmin,
    // Actions
    login,
    register,
    logout,
    fetchCurrentUser,
  }
})
