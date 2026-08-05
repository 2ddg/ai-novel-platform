import request from './index'

// 注册
export const register = (data) => request.post('/auth/register', data)

// 登录
export const login = (data) => request.post('/auth/login', data)

// 获取当前用户信息
export const getMe = () => request.get('/auth/me')
