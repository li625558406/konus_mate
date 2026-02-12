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

      <!-- Sessions List -->
      <div class="flex-1 overflow-y-auto p-4">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-neutral-600 font-body font-semibold text-base">会话历史</h2>
          <button
            @click="handleNewChat"
            class="p-2 rounded-lg bg-neutral-100 hover:bg-neutral-200 transition-colors text-primary-600"
            title="新建会话"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        <div v-if="chatStore.loading" class="flex items-center justify-center py-8">
          <div class="spinner"></div>
        </div>

        <div v-else-if="chatStore.hasSessions" class="space-y-2">
          <div
            v-for="session in chatStore.sessions"
            :key="session.id"
            @click="handleSelectSession(session.id)"
            class="p-3 rounded-xl cursor-pointer transition-all duration-300 hover:bg-neutral-50"
            :class="{ 'bg-primary-50 border border-primary-200': chatStore.currentSession?.id === session.id }"
          >
            <p class="text-neutral-700 font-body text-sm truncate mb-1">{{ session.title }}</p>
            <p class="text-neutral-400 text-xs">{{ formatDate(session.updated_at) }}</p>
          </div>
        </div>

        <div v-else class="text-center py-8 text-neutral-400">
          <p class="font-body">暂无会话记录</p>
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
          {{ chatStore.currentSession?.title || '新对话' }}
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
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-9-2 9-2 9 2z" />
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

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const messageInput = ref('')
const messagesContainer = ref(null)

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`

  return date.toLocaleDateString('zh-CN')
}

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
    await chatStore.send(content)
    await scrollToBottom()
  } catch (error) {
    console.error('Send message failed:', error)
  }
}

// 新建会话
const handleNewChat = () => {
  chatStore.createNewSession()
}

// 选择会话
const handleSelectSession = async (sessionId) => {
  try {
    await chatStore.loadMessages(sessionId)
    await scrollToBottom()
  } catch (error) {
    console.error('Load session failed:', error)
  }
}

// 退出登录
const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    authStore.logout()
    router.push('/login')
  }
}

// 初始化加载会话列表
onMounted(async () => {
  try {
    await chatStore.loadSessions()
  } catch (error) {
    console.error('Load sessions failed:', error)
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
