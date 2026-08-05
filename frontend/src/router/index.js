import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/knowledge',
    children: [
      {
        path: 'knowledge',
        name: 'KnowledgeList',
        component: () => import('../views/KnowledgeList.vue'),
        meta: { title: '知识库管理' },
      },
      {
        path: 'knowledge/:id',
        name: 'KnowledgeDetail',
        component: () => import('../views/KnowledgeDetail.vue'),
        meta: { title: '知识库详情' },
      },
      {
        path: 'chat/:id?',
        name: 'Chat',
        component: () => import('../views/Chat.vue'),
        meta: { title: '智能问答' },
      },
      {
        path: 'novel',
        name: 'NovelList',
        component: () => import('../views/NovelList.vue'),
        meta: { title: '小说创作' },
      },
      {
        path: 'novel/:id',
        name: 'NovelDetail',
        component: () => import('../views/NovelDetail.vue'),
        meta: { title: '小说详情' },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫：未登录跳登录页
router.beforeEach(async (to) => {
  const userStore = useUserStore()
  if (to.meta.public) {
    // 已登录用户访问登录页，跳首页
    if (userStore.token && to.name === 'Login') {
      return { path: '/' }
    }
    return true
  }
  // 需要登录的页面
  if (!userStore.token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  // 首次进入拉一下用户信息
  if (!userStore.userInfo) {
    await userStore.fetchUser()
  }
  return true
})

export default router
