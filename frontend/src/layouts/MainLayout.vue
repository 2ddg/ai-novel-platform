<template>
  <div class="app-shell" :class="{ 'is-collapsed': isCollapse }">
    <div class="mobile-scrim" :class="{ show: mobileOpen }" @click="closeMobile" />

    <aside class="sidebar" :class="{ 'is-open': mobileOpen }">
      <router-link to="/novel" class="brand" @click="closeMobile">
        <span class="brand-mark">✳</span>
        <span class="brand-copy">
          <span class="brand-name">AI 小说创作</span>
          <span class="brand-sub">WRITING STUDIO</span>
        </span>
      </router-link>

      <div class="sidebar-label">工作台</div>

      <nav class="nav-list">
        <router-link
          v-for="(item, index) in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: activeMenu === item.path }"
          @click="closeMobile"
        >
          <span class="nav-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-copy">
            <span class="nav-name">{{ item.label }}</span>
            <span class="nav-desc">{{ item.desc }}</span>
          </span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </router-link>
      </nav>

      <div class="sidebar-note">
        <div class="note-rule" />
        <p class="note-kicker">今日写作</p>
        <p class="note-text">先写坏，再写好。初稿不需要完美。</p>
        <div class="note-status">
          <span class="status-dot" />
          <span>AI 创作引擎在线</span>
        </div>
      </div>
    </aside>

    <section class="workspace">
      <header class="topbar">
        <div class="topbar-left">
          <button class="icon-button" type="button" aria-label="切换导航" @click="toggleSidebar">
            <el-icon :size="18"><Fold v-if="!isCollapse || mobileOpen" /><Expand v-else /></el-icon>
          </button>
          <div class="topbar-title">
            <span class="topbar-kicker">Writing Studio</span>
            <span class="topbar-page">{{ currentTitle }}</span>
          </div>
        </div>

        <div class="topbar-right">
          <router-link to="/novel" class="quick-link">
            <el-icon><EditPen /></el-icon>
            <span>我的作品</span>
          </router-link>
          <span class="topbar-divider" />
          <el-dropdown trigger="click" @command="onCommand">
            <button class="user-button" type="button">
              <span class="user-avatar">{{ userInitial }}</span>
              <span class="user-copy">
                <span class="user-name">{{ userStore.userInfo?.username || '写作者' }}</span>
                <span class="user-role">作者账号</span>
              </span>
              <el-icon class="user-arrow"><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="main-content">
        <router-view />
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  Folder, ChatDotRound, EditPen, Fold, Expand, ArrowDown, SwitchButton,
} from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const navItems = [
  { path: '/knowledge', label: '资料室', desc: '知识库与参考文档', icon: Folder },
  { path: '/chat', label: '问答台', desc: '和你的资料对话', icon: ChatDotRound },
  { path: '/novel', label: '创作室', desc: '小说、章节与角色', icon: EditPen },
]

const isCollapse = ref(false)
const mobileOpen = ref(false)
const isMobile = ref(false)

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/knowledge')) return '/knowledge'
  if (path.startsWith('/chat')) return '/chat'
  if (path.startsWith('/novel')) return '/novel'
  return path
})

const currentTitle = computed(() => route.meta.title || 'AI 小说创作平台')
const userInitial = computed(() => (userStore.userInfo?.username || 'W').charAt(0).toUpperCase())

function syncViewport() {
  isMobile.value = window.innerWidth <= 900
  if (!isMobile.value) mobileOpen.value = false
}

function toggleSidebar() {
  if (isMobile.value) {
    mobileOpen.value = !mobileOpen.value
  } else {
    isCollapse.value = !isCollapse.value
  }
}

function closeMobile() {
  mobileOpen.value = false
}

async function onCommand(cmd) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning',
    }).then(() => {
      userStore.logout()
      router.push('/login')
    }).catch(() => {})
  }
}

watch(() => route.fullPath, closeMobile)

onMounted(() => {
  syncViewport()
  window.addEventListener('resize', syncViewport)
})

onBeforeUnmount(() => window.removeEventListener('resize', syncViewport))
</script>

<style scoped>
.app-shell {
  --sidebar-width: 272px;
  min-height: 100vh;
  height: 100vh;
  display: flex;
  background: transparent;
  overflow: hidden;
}

.app-shell.is-collapsed {
  --sidebar-width: 88px;
}

.sidebar {
  width: var(--sidebar-width);
  flex: 0 0 var(--sidebar-width);
  min-height: 100vh;
  background:
    radial-gradient(ellipse at 0% 0%, rgba(204, 120, 92, 0.16), transparent 40%),
    var(--color-surface-dark);
  border-right: 1px solid rgba(250, 249, 245, 0.06);
  display: flex;
  flex-direction: column;
  padding: 22px 18px 18px;
  transition: width 280ms var(--ease-out), flex-basis 280ms var(--ease-out),
    transform 280ms var(--ease-out);
  position: relative;
  z-index: 40;
  overflow: hidden;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 8px 24px;
  color: var(--color-on-dark);
  white-space: nowrap;
}

.brand-mark {
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-on-dark);
  font-size: 24px;
  line-height: 1;
  box-shadow: 0 6px 22px rgba(204, 120, 92, 0.35);
}

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.brand-name {
  font-family: var(--font-serif);
  font-size: 17px;
  letter-spacing: -0.3px;
  line-height: 1.1;
}

.brand-sub {
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--color-on-dark-soft);
}

.sidebar-label {
  padding: 0 10px 10px;
  font-size: 10px;
  letter-spacing: 2px;
  color: #77736b;
  white-space: nowrap;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 54px;
  padding: 10px 10px;
  border-radius: 10px;
  color: var(--color-on-dark-soft);
  position: relative;
  transition: background var(--dur-fast) var(--ease-soft), color var(--dur-fast) var(--ease-soft);
  white-space: nowrap;
}

.nav-item:hover {
  background: rgba(250, 249, 245, 0.055);
  color: var(--color-on-dark);
}

.nav-item.active {
  background: rgba(250, 249, 245, 0.09);
  color: var(--color-on-dark);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 15px;
  bottom: 15px;
  width: 2px;
  background: var(--color-primary);
  border-radius: 2px;
}

.nav-index {
  font-family: var(--font-mono);
  font-size: 9px;
  color: #6d6961;
  width: 16px;
  flex: 0 0 16px;
  letter-spacing: 0.4px;
}

.nav-icon {
  font-size: 18px;
  flex: 0 0 18px;
  color: inherit;
}

.nav-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.nav-name {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.3;
}

.nav-desc {
  font-size: 10.5px;
  color: #77736b;
  line-height: 1.3;
}

.nav-item.active .nav-desc {
  color: var(--color-on-dark-soft);
}

.nav-badge {
  margin-left: auto;
  min-width: 20px;
  padding: 2px 6px;
  border-radius: 999px;
  background: var(--color-primary);
  color: #fff;
  font-size: 10px;
  text-align: center;
}

.sidebar-note {
  margin-top: auto;
  padding: 14px 10px 2px;
  min-width: 212px;
}

.note-rule {
  height: 1px;
  background: rgba(250, 249, 245, 0.09);
  margin-bottom: 16px;
}

.note-kicker {
  font-size: 10px;
  letter-spacing: 1.6px;
  color: #77736b;
  margin-bottom: 7px;
}

.note-text {
  font-family: var(--font-serif);
  font-size: 14px;
  line-height: 1.55;
  color: var(--color-on-dark);
  margin-bottom: 14px;
}

.note-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10.5px;
  color: var(--color-on-dark-soft);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent-teal);
  box-shadow: 0 0 10px var(--color-accent-teal);
}

.is-collapsed .brand-copy,
.is-collapsed .sidebar-label,
.is-collapsed .nav-copy,
.is-collapsed .nav-index,
.is-collapsed .nav-badge,
.is-collapsed .sidebar-note {
  display: none;
}

.is-collapsed .brand,
.is-collapsed .nav-item {
  justify-content: center;
  padding-left: 0;
  padding-right: 0;
}

.is-collapsed .brand {
  padding-bottom: 22px;
}

.is-collapsed .nav-item.active::before {
  display: none;
}

.workspace {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.topbar {
  height: 72px;
  flex: 0 0 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  background: rgba(250, 249, 245, 0.82);
  border-bottom: 1px solid var(--color-hairline-soft);
  backdrop-filter: blur(14px);
  position: relative;
  z-index: 20;
}

.topbar-left,
.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.icon-button {
  width: 38px;
  height: 38px;
  border: 1px solid transparent;
  border-radius: 50%;
  background: transparent;
  color: var(--color-muted);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background var(--dur-fast), color var(--dur-fast), border-color var(--dur-fast);
}

.icon-button:hover {
  background: var(--color-surface-soft);
  border-color: var(--color-hairline);
  color: var(--color-ink);
}

.topbar-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.2;
}

.topbar-kicker {
  font-size: 9px;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  color: var(--color-muted-soft);
}

.topbar-page {
  font-family: var(--font-serif);
  font-size: 18px;
  letter-spacing: -0.2px;
  color: var(--color-ink);
}

.quick-link {
  display: flex;
  align-items: center;
  gap: 7px;
  height: 36px;
  padding: 0 14px;
  border: 1px solid var(--color-hairline);
  border-radius: 999px;
  color: var(--color-body);
  font-size: 12.5px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.44);
  transition: border-color var(--dur-fast), color var(--dur-fast), background var(--dur-fast);
}

.quick-link:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: #fff;
}

.topbar-divider {
  width: 1px;
  height: 22px;
  background: var(--color-hairline);
}

.user-button {
  display: flex;
  align-items: center;
  gap: 9px;
  border: 0;
  background: transparent;
  cursor: pointer;
  padding: 4px;
  border-radius: 999px;
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-serif);
  font-size: 15px;
  border: 2px solid var(--color-canvas);
  box-shadow: 0 2px 8px rgba(204, 120, 92, 0.22);
}

.user-copy {
  display: flex;
  flex-direction: column;
  gap: 1px;
  text-align: left;
}

.user-name {
  font-size: 12.5px;
  font-weight: 500;
  color: var(--color-ink);
  line-height: 1.25;
}

.user-role {
  font-size: 9.5px;
  color: var(--color-muted-soft);
  letter-spacing: 0.5px;
}

.user-arrow {
  color: var(--color-muted-soft);
  font-size: 10px;
}

.main-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 30px 34px 48px;
  scroll-behavior: smooth;
}

.mobile-scrim {
  display: none;
}

@media (max-width: 1100px) {
  .main-content {
    padding: 26px 24px 40px;
  }

  .user-copy {
    display: none;
  }
}

@media (max-width: 900px) {
  .app-shell {
    --sidebar-width: 276px;
  }

  .app-shell.is-collapsed {
    --sidebar-width: 276px;
  }

  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    transform: translateX(-104%);
    box-shadow: 24px 0 70px rgba(20, 20, 19, 0.26);
  }

  .sidebar.is-open {
    transform: translateX(0);
  }

  .mobile-scrim {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(24, 23, 21, 0.42);
    backdrop-filter: blur(3px);
    opacity: 0;
    pointer-events: none;
    transition: opacity 240ms;
    z-index: 35;
  }

  .mobile-scrim.show {
    opacity: 1;
    pointer-events: auto;
  }

  .topbar {
    height: 64px;
    flex-basis: 64px;
    padding: 0 16px;
  }

  .topbar-page {
    font-size: 16px;
  }

  .topbar-kicker,
  .topbar-divider,
  .quick-link {
    display: none;
  }

  .main-content {
    padding: 18px 16px 36px;
  }
}

@media (max-width: 520px) {
  .user-avatar {
    width: 30px;
    height: 30px;
    font-size: 13px;
  }
}
</style>
