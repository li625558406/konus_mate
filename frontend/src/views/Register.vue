<template>
  <div class="min-h-screen flex items-center justify-center bg-neutral-50 relative py-8">
    <!-- Subtle Background Decorations -->
    <div class="absolute top-10 right-10 w-64 h-64 rounded-full bg-accent-100/40 blur-3xl"></div>
    <div class="absolute bottom-10 left-10 w-80 h-80 rounded-full bg-primary-100/30 blur-3xl"></div>

    <!-- Register Card -->
    <div class="card p-10 md:p-12 w-full max-w-lg mx-4 relative z-10 animate-scale-in">
      <!-- Logo -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-display font-bold text-gradient mb-2">创建账户</h1>
        <p class="text-neutral-500 font-body text-base">加入 Konus Mate，开启 AI 之旅</p>
      </div>

      <!-- Error Message -->
      <div v-if="authStore.error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-center">
        {{ authStore.error }}
      </div>

      <!-- Validation Errors -->
      <div v-if="validationErrors.length > 0" class="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-700">
        <ul class="text-sm space-y-1">
          <li v-for="(error, i) in validationErrors" :key="i">• {{ error }}</li>
        </ul>
      </div>

      <!-- Register Form -->
      <form @submit.prevent="handleRegister" class="space-y-5">
        <!-- Username -->
        <div>
          <label class="block text-neutral-600 font-body font-medium mb-2 ml-1">用户名 *</label>
          <input
            v-model="formData.username"
            type="text"
            class="input-field"
            placeholder="3-50位字母、数字、下划线或连字符"
            required
            minlength="3"
            maxlength="50"
            :disabled="authStore.loading"
          />
        </div>

        <!-- Email -->
        <div>
          <label class="block text-neutral-600 font-body font-medium mb-2 ml-1">邮箱 *</label>
          <input
            v-model="formData.email"
            type="email"
            class="input-field"
            placeholder="your@email.com"
            required
            :disabled="authStore.loading"
          />
        </div>

        <!-- Password -->
        <div>
          <label class="block text-neutral-600 font-body font-medium mb-2 ml-1">密码 *</label>
          <input
            v-model="formData.password"
            type="password"
            class="input-field"
            placeholder="至少6位，包含大小写字母和数字"
            required
            minlength="6"
            :disabled="authStore.loading"
          />
        </div>

        <!-- Full Name -->
        <div>
          <label class="block text-neutral-600 font-body font-medium mb-2 ml-1">姓名</label>
          <input
            v-model="formData.full_name"
            type="text"
            class="input-field"
            placeholder="您的真实姓名（可选）"
            maxlength="100"
            :disabled="authStore.loading"
          />
        </div>

        <!-- Phone -->
        <div>
          <label class="block text-neutral-600 font-body font-medium mb-2 ml-1">手机号</label>
          <input
            v-model="formData.phone"
            type="tel"
            class="input-field"
            placeholder="手机号码（可选）"
            maxlength="20"
            :disabled="authStore.loading"
          />
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          class="btn-primary w-full py-4 text-base disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
          :disabled="authStore.loading"
        >
          <span v-if="!authStore.loading">注册</span>
          <div v-else class="spinner"></div>
        </button>
      </form>

      <!-- Login Link -->
      <div class="mt-6 text-center">
        <p class="text-neutral-500 font-body text-base">
          已有账号？
          <router-link to="/login" class="text-primary-600 hover:text-primary-700 transition-colors font-semibold ml-1">
            立即登录
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = reactive({
  username: '',
  email: '',
  password: '',
  full_name: '',
  phone: '',
})

const validationErrors = computed(() => {
  const errors = []

  // Username validation
  if (formData.username && formData.username.length < 3) {
    errors.push('用户名至少需要3个字符')
  }
  if (formData.username && !/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
    errors.push('用户名只能包含字母、数字、下划线和连字符')
  }

  // Password validation
  if (formData.password) {
    if (formData.password.length < 6) {
      errors.push('密码至少需要6个字符')
    }
    if (!/[A-Z]/.test(formData.password)) {
      errors.push('密码必须包含至少一个大写字母')
    }
    if (!/[a-z]/.test(formData.password)) {
      errors.push('密码必须包含至少一个小写字母')
    }
    if (!/[0-9]/.test(formData.password)) {
      errors.push('密码必须包含至少一个数字')
    }
  }

  return errors
})

const handleRegister = async () => {
  if (validationErrors.value.length > 0) {
    return
  }

  try {
    await authStore.register(formData)
    alert('注册成功！请登录')
    router.push('/login')
  } catch (error) {
    console.error('Registration failed:', error)
  }
}
</script>
