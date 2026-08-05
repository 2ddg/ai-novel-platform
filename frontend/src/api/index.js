import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',          // 走 vite 代理到后端 8001
  timeout: 60000,
})

// 请求拦截器：自动带 JWT Token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一处理 401 和错误
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const { response } = error
    if (response) {
      if (response.status === 401) {
        // token 失效或未登录
        localStorage.removeItem('token')
        ElMessage.error('登录已过期，请重新登录')
        router.push('/login')
      } else {
        const msg = response.data?.detail || response.data?.message || `请求失败 (${response.status})`
        ElMessage.error(msg)
      }
    } else {
      ElMessage.error('网络异常，请检查服务是否启动')
    }
    return Promise.reject(error)
  }
)

export default request
