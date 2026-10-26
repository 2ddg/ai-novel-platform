<template>
  <AuthShell
    kicker="BEGIN YOUR MANUSCRIPT"
    :heading="'写下第一章，\n故事才开始。'"
    :lead="'创建你的作者账号。\n知识库问答、角色档案、章节审计与伏笔追踪，从第一行字起就陪着你。'"
    quote="每一个世界，都从一行字开始。"
    panel-index="02 / 02"
  >
    <div class="auth-header">
      <p class="auth-kicker">NEW AUTHOR</p>
      <h2>创建账号</h2>
      <p>注册后即可使用知识库问答与 AI 写作。</p>
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
        <label for="register-username">用户名</label>
        <el-form-item prop="username">
          <el-input
            id="register-username"
            v-model="form.username"
            placeholder="至少 3 个字符"
            :prefix-icon="User"
            autocomplete="username"
          />
        </el-form-item>
      </div>

      <div class="field">
        <label for="register-email">邮箱</label>
        <el-form-item prop="email">
          <el-input
            id="register-email"
            v-model="form.email"
            placeholder="用于找回账号"
            :prefix-icon="Message"
            autocomplete="email"
          />
        </el-form-item>
      </div>

      <div class="field-grid">
        <div class="field">
          <label for="register-password">密码</label>
          <el-form-item prop="password">
            <el-input
              id="register-password"
              v-model="form.password"
              type="password"
              placeholder="至少 6 位"
              :prefix-icon="Lock"
              show-password
              autocomplete="new-password"
            />
          </el-form-item>
        </div>

        <div class="field">
          <label for="register-confirm">确认密码</label>
          <el-form-item prop="confirmPassword">
            <el-input
              id="register-confirm"
              v-model="form.confirmPassword"
              type="password"
              placeholder="再次输入"
              :prefix-icon="Lock"
              show-password
              autocomplete="new-password"
              @keyup.enter="onSubmit"
            />
          </el-form-item>
        </div>
      </div>

      <el-button
        type="primary"
        class="submit-btn"
        :loading="loading"
        @click="onSubmit"
      >
        <span>创建作者账号</span>
        <el-icon><Right /></el-icon>
      </el-button>
    </el-form>

    <div class="auth-footer">
      <span>已有账号？</span>
      <router-link to="/login">返回登录</router-link>
    </div>
  </AuthShell>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Message, Right, User } from '@element-plus/icons-vue'
import AuthShell from '../components/AuthShell.vue'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度 3-20 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.register({
        username: form.username,
        email: form.email,
        password: form.password,
      })
      ElMessage.success('注册成功，请登录')
      router.push('/login')
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
  margin-bottom: 28px;
}

.auth-kicker {
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--color-primary);
  margin-bottom: 12px;
}

.auth-header h2 {
  font-family: var(--font-serif);
  font-size: 36px;
  font-weight: 400;
  line-height: 1.08;
  letter-spacing: -0.8px;
  color: var(--color-ink);
  margin-bottom: 9px;
}

.auth-header p:last-child {
  font-size: 13px;
  color: var(--color-muted);
}

.field {
  margin-bottom: 2px;
}

.field label {
  display: block;
  margin-bottom: 7px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.8px;
  color: var(--color-muted);
}

.field :deep(.el-form-item) {
  margin-bottom: 14px;
}

.field-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.auth-form :deep(.el-input__wrapper) {
  min-height: 46px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.56);
  padding: 0 13px;
}

.auth-form :deep(.el-input__prefix) {
  color: var(--color-muted-soft);
}

.submit-btn {
  width: 100%;
  height: 50px;
  margin-top: 8px;
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
  margin-top: 24px;
  font-size: 12.5px;
  color: var(--color-muted);
}

.auth-footer a {
  color: var(--color-primary);
  font-weight: 600;
  border-bottom: 1px solid rgba(204, 120, 92, 0.28);
}

.auth-footer a:hover {
  border-color: var(--color-primary);
}

@media (max-width: 520px) {
  .field-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
