<template>
  <div class="min-h-screen flex items-center justify-center bg-neutral-50 relative">
    <!-- Subtle Background Decorations -->
    <div class="absolute top-20 left-20 w-64 h-64 rounded-full bg-primary-100/40 blur-3xl"></div>
    <div class="absolute bottom-20 right-20 w-80 h-80 rounded-full bg-accent-100/30 blur-3xl"></div>

    <!-- Login Card -->
    <div class="card p-10 md:p-14 w-full max-w-md mx-4 relative z-10 animate-scale-in">
      <!-- Logo -->
      <div class="text-center mb-10">
        <h1 class="text-4xl font-display font-bold text-gradient mb-3">Konus Mate</h1>
        <p class="text-neutral-500 font-body text-lg">智能 AI 助手</p>
      </div>

      <!-- Error Message -->
      <div v-if="authStore.error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-center">
        {{ authStore.error }}
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-6">
        <!-- Username/Email -->
        <div>
          <label class="block text-neutral-600 font-body font-medium mb-2 ml-1">用户名或邮箱</label>
          <input
            v-model="formData.username"
            type="text"
            class="input-field"
            placeholder="请输入用户名或邮箱"
            required
            :disabled="authStore.loading"
          />
        </div>

        <!-- Password -->
        <div>
          <label class="block text-neutral-600 font-body font-medium mb-2 ml-1">密码</label>
          <input
            v-model="formData.password"
            type="password"
            class="input-field"
            placeholder="请输入密码"
            required
            :disabled="authStore.loading"
          />
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          class="btn-primary w-full py-4 text-base disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
          :disabled="authStore.loading"
        >
          <span v-if="!authStore.loading">登录</span>
          <div v-else class="spinner"></div>
        </button>
      </form>

      <!-- Register Link -->
      <div class="mt-8 text-center">
        <p class="text-neutral-500 font-body text-base">
          还没有账号？
          <router-link to="/register" class="text-primary-600 hover:text-primary-700 transition-colors font-semibold ml-1">
            立即注册
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = reactive({
  username: '',
  password: '',
})

const handleLogin = async () => {
  try {
    await authStore.login(formData)
    router.push('/chat')
  } catch (error) {
    console.error('Login failed:', error)
  }
}
</script>
