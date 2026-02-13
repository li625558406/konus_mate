import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMemories, deleteMemory, clearOldMemories } from '@/api/memory'

export const useMemoryStore = defineStore('memory', () => {
  // State
  const memories = ref([])
  const loading = ref(false)
  const error = ref(null)

  /**
   * 加载记忆列表
   */
  const loadMemories = async (systemInstructionId = null) => {
    loading.value = true
    error.value = null

    try {
      const params = systemInstructionId
        ? { system_instruction_id: systemInstructionId }
        : {}

      const response = await getMemories(params)
      memories.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '加载记忆失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除指定记忆
   */
  const removeMemory = async (memoryId) => {
    try {
      await deleteMemory(memoryId)
      // 从列表中移除
      memories.value = memories.value.filter(m => m.id !== memoryId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || '删除记忆失败'
      throw err
    }
  }

  /**
   * 清理旧记忆
   */
  const clearOld = async (systemInstructionId = null, months = 3) => {
    try {
      const params = { months }
      if (systemInstructionId) {
        params.system_instruction_id = systemInstructionId
      }

      const response = await clearOldMemories(params)

      // 重新加载列表
      await loadMemories(systemInstructionId)

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '清理记忆失败'
      throw err
    }
  }

  /**
   * 格式化关键点
   */
  const formatKeyPoints = (keyPointsStr) => {
    if (!keyPointsStr) return []
    try {
      return JSON.parse(keyPointsStr)
    } catch {
      return []
    }
  }

  /**
   * 格式化时间
   */
  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) return '今天'
    if (days === 1) return '昨天'
    if (days < 7) return `${days}天前`
    if (days < 30) return `${Math.floor(days / 7)}周前`
    if (days < 365) return `${Math.floor(days / 30)}个月前`
    return `${Math.floor(days / 365)}年前`
  }

  // 计算属性：记忆总数
  const memoryCount = computed(() => memories.value.length)

  // 计算属性：按类型分组的记忆
  const memoriesByType = computed(() => {
    const grouped = {
      active: [],
      passive: []
    }
    memories.value.forEach(memory => {
      if (memory.memory_type === 'active') {
        grouped.active.push(memory)
      } else if (memory.memory_type === 'passive') {
        grouped.passive.push(memory)
      }
    })
    return grouped
  })

  return {
    // State
    memories,
    loading,
    error,
    // Computed
    memoryCount,
    memoriesByType,
    // Actions
    loadMemories,
    removeMemory,
    clearOld,
    // Helpers
    formatKeyPoints,
    formatDate,
  }
})
