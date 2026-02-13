import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSystemInstructions, getDefaultSystemInstruction } from '@/api/system_instruction'

export const useSystemInstructionStore = defineStore('systemInstruction', () => {
  // State
  const instructions = ref([])
  const selectedInstructionId = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const hasInstructions = computed(() => instructions.value.length > 0)
  const selectedInstruction = computed(() => {
    return instructions.value.find(i => i.id === selectedInstructionId.value)
  })

  /**
   * 加载系统提示词列表
   */
  const loadInstructions = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await getSystemInstructions(true)
      instructions.value = response.data

      // 如果有选中的ID，确认它仍然存在
      if (selectedInstructionId.value) {
        const exists = instructions.value.some(i => i.id === selectedInstructionId.value)
        if (!exists) {
          selectedInstructionId.value = null
        }
      }

      // 如果没有选中项，设置默认的
      if (!selectedInstructionId.value && instructions.value.length > 0) {
        const defaultInstruction = instructions.value.find(i => i.is_default)
        if (defaultInstruction) {
          selectedInstructionId.value = defaultInstruction.id
        } else {
          selectedInstructionId.value = instructions.value[0].id
        }
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '加载系统提示词失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 选择系统提示词
   */
  const selectInstruction = (instructionId) => {
    selectedInstructionId.value = instructionId
  }

  /**
   * 清除选择
   */
  const clearSelection = () => {
    selectedInstructionId.value = null
  }

  return {
    // State
    instructions,
    selectedInstructionId,
    selectedInstruction,
    loading,
    error,
    // Computed
    hasInstructions,
    // Actions
    loadInstructions,
    selectInstruction,
    clearSelection,
  }
})
