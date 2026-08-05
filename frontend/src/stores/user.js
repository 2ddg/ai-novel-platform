import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, register as registerApi, getMe } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  // 登录
  async function login(form) {
    const res = await loginApi(form)
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    userInfo.value = res.user
    return res
  }

  // 注册
  async function register(form) {
    return await registerApi(form)
  }

  // 拉取当前用户信息
  async function fetchUser() {
    if (!token.value) return null
    try {
      const res = await getMe()
      userInfo.value = res
      return res
    } catch {
      logout()
      return null
    }
  }

  // 登出
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  return { token, userInfo, login, register, fetchUser, logout }
})
