<template>
  <div class="h-screen bg-neutral-50 flex overflow-hidden">
    <!-- Sidebar -->
    <aside class="sidebar w-80 flex flex-col h-full">
      <!-- Logo Area -->
      <div class="p-6 border-b border-neutral-200">
        <h1 class="text-2xl font-display font-bold text-gradient">Konus Mate</h1>
        <p class="text-neutral-500 text-sm font-body">AI Assistant</p>
      </div>

      <!-- User Info -->
      <div class="p-4 border-b border-neutral-200">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-500 flex items-center justify-center font-display font-bold text-lg text-white">
            {{ authStore.user?.username?.[0]?.toUpperCase() || '?' }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-body font-semibold text-neutral-800 truncate">{{ authStore.user?.full_name || authStore.user?.username }}</p>
            <p class="text-neutral-400 text-sm truncate">{{ authStore.user?.email }}</p>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex-1 overflow-y-auto p-4">
        <!-- Conversation Stats -->
        <div class="mb-4 p-3 bg-neutral-100 rounded-lg">
          <h3 class="text-neutral-600 font-body font-semibold text-sm mb-2">对话统计</h3>
          <div class="space-y-1 text-sm">
            <div class="flex justify-between">
              <span class="text-neutral-500">消息总数：</span>
              <span class="font-semibold text-neutral-800">{{ chatStore.messageCount }}</span>
            </div>
            <div v-if="chatStore.shouldWarnAboutCount" class="mt-2 p-2 bg-yellow-100 border border-yellow-300 rounded text-yellow-800 text-xs">
              ⚠️ 接近50条消息，系统将自动保存关键记忆
            </div>
            <div v-if="chatStore.conversationRound > 0" class="mt-2 p-2 bg-green-100 border border-green-300 rounded text-green-800 text-xs">
              ✅ 已完成 {{ chatStore.conversationRound }} 次对话清洗
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between mb-4">
          <h2 class="text-neutral-600 font-body font-semibold text-base">对话</h2>
          <button
            @click="handleNewChat"
            class="p-2 rounded-lg bg-neutral-100 hover:bg-neutral-200 transition-colors text-primary-600"
            title="清空对话"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        <!-- System Instruction Selector -->
        <div class="mb-4">
          <label class="block text-neutral-600 font-body font-semibold text-sm mb-2">
            AI 助手类型
          </label>
          <select
            v-model="systemInstructionStore.selectedInstructionId"
            class="w-full px-3 py-2 rounded-lg border border-neutral-300 bg-white text-neutral-800 font-body text-sm focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            :disabled="systemInstructionStore.loading"
          >
            <option v-if="systemInstructionStore.loading" value="" disabled>
              加载中...
            </option>
            <option v-else-if="!systemInstructionStore.hasInstructions" value="" disabled>
              暂无可用的助手类型
            </option>
            <option
              v-for="instruction in systemInstructionStore.instructions"
              :key="instruction.id"
              :value="instruction.id"
            >
              {{ instruction.name }}
            </option>
          </select>
          <p
            v-if="systemInstructionStore.selectedInstruction"
            class="mt-2 text-neutral-500 text-xs"
          >
            {{ systemInstructionStore.selectedInstruction.description }}
          </p>
        </div>

        <!-- Memory Management -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-neutral-600 font-body font-semibold text-base">记忆管理</h2>
            <button
              @click="handleLoadMemories"
              class="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              刷新
            </button>
          </div>

          <!-- Memory List -->
          <div v-if="memoryStore.loading" class="text-center py-4 text-neutral-500 text-sm">
            加载中...
          </div>
          <div v-else-if="memoryStore.memories.length === 0" class="text-center py-4 text-neutral-500 text-sm">
            暂无保存的记忆
          </div>
          <div v-else class="space-y-2 max-h-60 overflow-y-auto">
            <div
              v-for="memory in memoryStore.memories.slice(0, 5)"
              :key="memory.id"
              class="p-3 bg-neutral-100 rounded-lg text-sm"
            >
              <div class="flex justify-between items-start mb-1">
                <span class="font-semibold text-neutral-800 flex-1">{{ memory.summary }}</span>
                <button
                  @click="handleDeleteMemory(memory.id)"
                  class="text-red-600 hover:text-red-700 ml-2"
                  title="删除"
                >
                  ×
                </button>
              </div>
              <div class="text-neutral-500 text-xs">
                {{ memoryStore.formatDate(memory.created_at) }}
              </div>
            </div>
          </div>

          <!-- Clear Old Memories Button -->
          <button
            @click="handleClearOldMemories"
            class="w-full mt-2 py-2 rounded-lg border border-neutral-300 text-neutral-600 hover:bg-neutral-50 hover:border-neutral-400 transition-all font-body font-medium text-sm"
          >
            清理3个月前的记忆
          </button>
        </div>
      </div>

      <!-- Logout Button -->
      <div class="p-4 border-t border-neutral-200">
        <button
          @click="handleLogout"
          class="w-full py-3 rounded-xl border border-neutral-300 text-neutral-600 hover:bg-neutral-50 hover:border-neutral-400 transition-all font-body font-medium"
        >
          退出登录
        </button>
      </div>
    </aside>

    <!-- Main Chat Area -->
    <main class="flex-1 flex flex-col bg-white h-full overflow-hidden">
      <!-- Chat Header -->
      <header class="flex-shrink-0 p-6 border-b border-neutral-200">
        <h2 class="text-xl font-display font-semibold text-neutral-800">
          新对话
        </h2>
        <p class="text-neutral-400 text-sm font-body mt-1">
          {{ chatStore.messages.length }} 条消息
        </p>
      </header>

      <!-- Messages Area -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Welcome Message -->
        <div v-if="chatStore.messages.length === 0" class="flex items-center justify-center h-full">
          <div class="text-center">
            <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary-400 to-primary-500 flex items-center justify-center">
              <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 class="text-2xl font-display font-bold text-gradient mb-2">开始新的对话</h3>
            <p class="text-neutral-500 font-body text-base">向我提问任何问题，我很乐意帮助您！</p>
          </div>
        </div>

        <!-- Messages List -->
        <div v-else class="space-y-6">
          <div
            v-for="(message, index) in chatStore.messages"
            :key="index"
            class="flex gap-4 animate-fade-in"
            :class="{ 'flex-row-reverse': message.role === 'user' }"
          >
            <!-- Avatar -->
            <div
              class="w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center font-display font-bold text-sm"
              :class="message.role === 'user' ? 'bg-gradient-to-br from-primary-400 to-primary-500 text-white' : 'bg-gradient-to-br from-accent-400 to-accent-500 text-white'"
            >
              {{ message.role === 'user' ? 'U' : 'AI' }}
            </div>

            <!-- Message Content -->
            <div
              class="max-w-2xl p-4 rounded-2xl"
              :class="message.role === 'user' ? 'bubble-user' : 'bubble-assistant'"
            >
              <p class="text-neutral-800 font-body text-base leading-relaxed whitespace-pre-wrap">{{ message.content }}</p>
            </div>
          </div>
        </div>

        <!-- Loading Indicator -->
        <div v-if="chatStore.sending" class="flex gap-4">
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-accent-400 to-accent-500 flex items-center justify-center font-display font-bold text-white text-sm">
            AI
          </div>
          <div class="bubble-assistant">
            <div class="flex gap-2">
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-6 border-t border-neutral-200 bg-white">
        <!-- Error Message -->
        <div v-if="chatStore.error" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          {{ chatStore.error }}
          <button @click="chatStore.error = null" class="ml-2 text-red-700 hover:text-red-900 text-lg">×</button>
        </div>

        <!-- Message Input -->
        <form @submit.prevent="handleSend" class="flex gap-4">
          <input
            v-model="messageInput"
            type="text"
            class="input-field flex-1"
            placeholder="输入您的消息..."
            :disabled="chatStore.sending"
            @keydown.enter.prevent
          />
          <button
            type="submit"
            class="btn-primary px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            :disabled="chatStore.sending || !messageInput.trim()"
          >
            <span v-if="!chatStore.sending">发送</span>
            <div v-else class="spinner" style="width: 20px; height: 20px;"></div>
            <svg v-if="!chatStore.sending" class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-9-9 2 2z" />
            </svg>
          </button>
        </form>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useSystemInstructionStore } from '@/stores/system_instruction'
import { useMemoryStore } from '@/stores/memory'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()
const systemInstructionStore = useSystemInstructionStore()
const memoryStore = useMemoryStore()

const messageInput = ref('')
const messagesContainer = ref(null)

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 发送消息
const handleSend = async () => {
  if (!messageInput.value.trim() || chatStore.sending) return

  const content = messageInput.value.trim()
  messageInput.value = ''

  try {
    await chatStore.send(content, {
      systemInstructionId: systemInstructionStore.selectedInstructionId
    })
    await scrollToBottom()
  } catch (error) {
    console.error('Send message failed:', error)
  }
}

// 新建对话
const handleNewChat = () => {
  chatStore.clearMessages()
}

// 退出登录
const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    authStore.logout()
    router.push('/login')
  }
}

// 加载记忆列表
const handleLoadMemories = async () => {
  try {
    await memoryStore.loadMemories(systemInstructionStore.selectedInstructionId)
  } catch (error) {
    console.error('Load memories failed:', error)
  }
}

// 删除记忆
const handleDeleteMemory = async (memoryId) => {
  if (!confirm('确定要删除这条记忆吗？')) return

  try {
    await memoryStore.removeMemory(memoryId)
  } catch (error) {
    console.error('Delete memory failed:', error)
  }
}

// 清理旧记忆
const handleClearOldMemories = async () => {
  if (!confirm('确定要清理3个月前的记忆吗？')) return

  try {
    const result = await memoryStore.clearOld(systemInstructionStore.selectedInstructionId)
    alert(result.message || `已清理 ${result.count || 0} 条旧记忆`)
  } catch (error) {
    console.error('Clear old memories failed:', error)
  }
}

// 初始化加载系统提示词
onMounted(async () => {
  try {
    await systemInstructionStore.loadInstructions()
    await handleLoadMemories()
  } catch (error) {
    console.error('Load system instructions failed:', error)
  }
})

// 监听消息变化，自动滚动到底部
watch(() => chatStore.messages.length, () => {
  scrollToBottom()
})
</script>

<style scoped>
/* Custom scrollbar for messages */
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: #d4d4d4 transparent;
}
</style>
