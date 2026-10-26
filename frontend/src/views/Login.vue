<template>
  <AuthShell
    kicker="A ROOM FOR STORIES"
    :heading="'把灵感，\n写成一部小说。'"
    :lead="'资料、角色、大纲、章节与伏笔，都在同一张写作台上。\n你负责想象，AI 负责陪你把它写完。'"
    quote="初稿不必漂亮，它只需要存在。"
    panel-index="01 / 02"
  >
    <div class="auth-header">
      <p class="auth-kicker">WELCOME BACK</p>
      <h2>欢迎回来</h2>
      <p>登录后继续你的故事。</p>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      size="large"
      class="auth-form"
      @submit.prevent="onSubmit"
    >
      <div class="field">
        <label for="login-username">用户名</label>
        <el-form-item prop="username">
          <el-input
            id="login-username"
            v-model="form.username"
            placeholder="你的作者名"
            :prefix-icon="User"
            autocomplete="username"
          />
        </el-form-item>
      </div>

      <div class="field">
        <label for="login-password">密码</label>
        <el-form-item prop="password">
          <el-input
            id="login-password"
            v-model="form.password"
            type="password"
            placeholder="输入密码"
            :prefix-icon="Lock"
            show-password
            autocomplete="current-password"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
      </div>

      <el-button
        type="primary"
        class="submit-btn"
        :loading="loading"
        @click="onSubmit"
      >
        <span>进入写作台</span>
        <el-icon><Right /></el-icon>
      </el-button>
    </el-form>

    <div class="auth-footer">
      <span>还没有账号？</span>
      <router-link to="/register">创建作者账号</router-link>
    </div>
  </AuthShell>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Right, User } from '@element-plus/icons-vue'
import AuthShell from '../components/AuthShell.vue'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(form)
      ElMessage.success('登录成功')
      const redirect = route.query.redirect || '/'
      router.push(redirect)
    } catch {
      // 错误已在拦截器统一提示
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.auth-header {
  margin-bottom: 34px;
}

.auth-kicker {
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--color-primary);
  margin-bottom: 14px;
}

.auth-header h2 {
  font-family: var(--font-serif);
  font-size: 38px;
  font-weight: 400;
  line-height: 1.08;
  letter-spacing: -0.8px;
  color: var(--color-ink);
  margin-bottom: 10px;
}

.auth-header p:last-child {
  font-size: 13.5px;
  color: var(--color-muted);
}

.field {
  margin-bottom: 4px;
}

.field label {
  display: block;
  margin-bottom: 8px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.8px;
  color: var(--color-muted);
}

.field :deep(.el-form-item) {
  margin-bottom: 18px;
}

.auth-form :deep(.el-input__wrapper) {
  min-height: 48px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.56);
  padding: 0 14px;
}

.auth-form :deep(.el-input__prefix) {
  color: var(--color-muted-soft);
}

.submit-btn {
  width: 100%;
  height: 50px;
  margin-top: 10px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  letter-spacing: 0.3px;
  box-shadow: 0 10px 24px rgba(204, 120, 92, 0.22);
}

.auth-footer {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 28px;
  font-size: 12.5px;
  color: var(--color-muted);
}

.auth-footer a {
  color: var(--color-primary);
  font-weight: 600;
  border-bottom: 1px solid rgba(204, 120, 92, 0.28);
  transition: border-color var(--dur-fast);
}

.auth-footer a:hover {
  border-color: var(--color-primary);
}
</style>
