<template>
  <div class="knowledge-page fade-rise">
    <header class="page-head">
      <div class="head-copy">
        <p class="page-kicker">THE ARCHIVE</p>
        <h1 class="page-title">资料室</h1>
        <p class="page-subtitle">
          把设定、参考与灵感收进同一个资料库。写作时，AI 会从你亲手整理的资料里找答案。
        </p>
      </div>
      <el-button type="primary" :icon="Plus" class="head-action" @click="showCreateDialog = true">
        新建资料库
      </el-button>
    </header>

    <section class="archive-summary">
      <div class="summary-item">
        <span class="summary-value">{{ String(list.length).padStart(2, '0') }}</span>
        <span class="summary-label">资料库</span>
      </div>
      <span class="summary-divider" />
      <div class="summary-item">
        <span class="summary-value">{{ String(totalDocs).padStart(2, '0') }}</span>
        <span class="summary-label">已收录文档</span>
      </div>
      <span class="summary-divider" />
      <p class="summary-note">
        <span class="note-dot" /> 支持 TXT / Markdown / PDF / Word 等格式
      </p>
    </section>

    <div v-if="loading" class="kb-grid">
      <div v-for="i in 3" :key="i" class="kb-card skeleton-card">
        <div class="skeleton-line short" />
        <div class="skeleton-mark" />
        <div class="skeleton-line" />
        <div class="skeleton-line tiny" />
      </div>
    </div>

    <section v-else-if="!list.length" class="empty-state">
      <span class="empty-index">01</span>
      <div class="empty-mark">
        <el-icon :size="28"><FolderOpened /></el-icon>
      </div>
      <h2>资料室还是空的</h2>
      <p>建一个资料库，把世界观、人物小传和参考文章放进去，再让 AI 陪你写。</p>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
        建立第一个资料库
      </el-button>
    </section>

    <section v-else class="kb-grid">
      <article
        v-for="(kb, index) in list"
        :key="kb.id"
        class="kb-card hover-lift"
        @click="goDetail(kb)"
      >
        <div class="card-top">
          <span class="card-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <span class="card-date">{{ formatDate(kb.created_at) }}</span>
        </div>

        <div class="folder-mark">
          <el-icon :size="24"><FolderOpened /></el-icon>
        </div>

        <h2 class="kb-name" :title="kb.name">{{ kb.name }}</h2>
        <p class="kb-desc" :title="kb.description || '暂无描述'">
          {{ kb.description || '还没有写描述。' }}
        </p>

        <div class="card-meta">
          <span><el-icon><Document /></el-icon> {{ kb.document_count }} 份文档</span>
          <span class="meta-rule" />
          <span>资料库 #{{ String(kb.id).padStart(2, '0') }}</span>
        </div>

        <div class="card-actions">
          <button type="button" class="text-action" @click.stop="goChat(kb)">
            <el-icon><ChatDotRound /></el-icon>
            去对话
            <el-icon class="action-arrow"><Right /></el-icon>
          </button>
          <button
            type="button"
            class="text-action danger"
            aria-label="删除资料库"
            @click.stop="onDelete(kb)"
          >
            <el-icon><Delete /></el-icon>
          </button>
        </div>
      </article>
    </section>

    <el-dialog v-model="showCreateDialog" title="新建资料库" width="520px">
      <p class="dialog-lead">给这个资料库一个清晰的名字。之后上传的文档、问答历史都会归档在这里。</p>
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="例如：雾港世界观 / 角色参考 / 写作技法" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="简单描述这个资料库的用途（选填）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate">创建资料库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, FolderOpened, Document, Delete, ChatDotRound, Right,
} from '@element-plus/icons-vue'
import { listKnowledge, createKnowledge, deleteKnowledge } from '../api/knowledge'

const router = useRouter()

const loading = ref(false)
const list = ref([])

const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref()
const createForm = ref({ name: '', description: '' })
const createRules = {
  name: [{ required: true, message: '请输入资料库名称', trigger: 'blur' }],
}

const totalDocs = computed(() => list.value.reduce((sum, kb) => sum + (kb.document_count || 0), 0))

async function fetchList() {
  loading.value = true
  try {
    list.value = await listKnowledge()
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  if (!createFormRef.value) return
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    creating.value = true
    try {
      await createKnowledge(createForm.value)
      ElMessage.success('创建成功')
      showCreateDialog.value = false
      createForm.value = { name: '', description: '' }
      fetchList()
    } finally {
      creating.value = false
    }
  })
}

async function onDelete(kb) {
  try {
    await ElMessageBox.confirm(
      `确定要删除资料库「${kb.name}」吗？该资料库的所有文档和对话历史将一并删除。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', confirmButtonClass: 'el-button--danger' }
    )
    await deleteKnowledge(kb.id)
    ElMessage.success('已删除')
    fetchList()
  } catch {
    // 用户取消或删除失败
  }
}

function goDetail(kb) {
  router.push({ path: `/knowledge/${kb.id}`, query: { name: kb.name } })
}

function goChat(kb) {
  router.push({ path: `/chat/${kb.id}` })
}

function formatDate(str) {
  if (!str) return ''
  const d = new Date(str)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`
}

onMounted(fetchList)
</script>

<style scoped>
.knowledge-page {
  max-width: 1360px;
  margin: 0 auto;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 28px;
  margin-bottom: 34px;
}

.head-copy {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.head-action {
  height: 42px;
  padding: 0 20px;
  flex: 0 0 auto;
}

.archive-summary {
  display: flex;
  align-items: center;
  gap: 26px;
  padding: 18px 24px;
  margin-bottom: 28px;
  border-top: 1px solid var(--color-hairline);
  border-bottom: 1px solid var(--color-hairline);
}

.summary-item {
  display: flex;
  align-items: baseline;
  gap: 9px;
}

.summary-value {
  font-family: var(--font-serif);
  font-size: 28px;
  line-height: 1;
  color: var(--color-ink);
  letter-spacing: -0.6px;
}

.summary-label {
  font-size: 10.5px;
  letter-spacing: 1.2px;
  color: var(--color-muted);
}

.summary-divider {
  width: 1px;
  height: 28px;
  background: var(--color-hairline);
}

.summary-note {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--color-muted);
}

.note-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-accent-teal);
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.kb-card {
  position: relative;
  min-height: 286px;
  display: flex;
  flex-direction: column;
  padding: 22px 24px 18px;
  border: 1px solid var(--color-hairline);
  border-radius: 16px;
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.84), rgba(245, 240, 232, 0.55));
  cursor: pointer;
  overflow: hidden;
}

.kb-card::after {
  content: '';
  position: absolute;
  left: 24px;
  right: 24px;
  bottom: 60px;
  height: 1px;
  background: var(--color-hairline-soft);
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--color-muted-soft);
}

.card-index {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 1px;
}

.card-date {
  font-size: 10px;
  letter-spacing: 0.6px;
}

.folder-mark {
  width: 46px;
  height: 46px;
  margin: 24px 0 18px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  transition: transform var(--dur-base) var(--ease-out), background var(--dur-base);
}

.kb-card:hover .folder-mark {
  transform: translateY(-3px) rotate(-4deg);
  background: rgba(204, 120, 92, 0.18);
}

.kb-name {
  font-family: var(--font-serif);
  font-size: 23px;
  font-weight: 400;
  line-height: 1.24;
  letter-spacing: -0.4px;
  color: var(--color-ink);
  margin-bottom: 9px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-desc {
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--color-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: auto;
  min-height: 42px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 16px 0 12px;
  font-size: 10.5px;
  color: var(--color-muted-soft);
}

.card-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.meta-rule {
  width: 14px;
  height: 1px;
  background: var(--color-hairline);
}

.card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 2px;
}

.text-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: transparent;
  padding: 4px 0;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.2px;
  color: var(--color-primary);
  cursor: pointer;
}

.text-action:hover {
  color: var(--color-primary-active);
}

.text-action.danger {
  color: var(--color-muted-soft);
  font-weight: 400;
}

.text-action.danger:hover {
  color: var(--color-error);
}

.action-arrow {
  font-size: 10px;
  transition: transform var(--dur-fast);
}

.text-action:hover .action-arrow {
  transform: translateX(3px);
}

.empty-state {
  position: relative;
  min-height: 390px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
  border: 1px dashed var(--color-hairline);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.38);
  overflow: hidden;
}

.empty-index {
  position: absolute;
  right: 34px;
  top: 8px;
  font-family: var(--font-serif);
  font-size: 150px;
  line-height: 1;
  color: rgba(204, 120, 92, 0.08);
  letter-spacing: -8px;
}

.empty-mark {
  width: 62px;
  height: 62px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--color-surface-soft);
  color: var(--color-primary);
  margin-bottom: 20px;
}

.empty-state h2 {
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 400;
  letter-spacing: -0.5px;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.empty-state p {
  max-width: 420px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-muted);
  margin-bottom: 22px;
}

.dialog-lead {
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--color-muted);
  margin: -6px 0 20px;
}

.skeleton-card {
  cursor: default;
  gap: 14px;
}

.skeleton-card::after {
  display: none;
}

.skeleton-line,
.skeleton-mark {
  background: linear-gradient(90deg, #f0ebe2, #f8f4ec, #f0ebe2);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}

.skeleton-line {
  height: 12px;
  width: 76%;
}

.skeleton-line.short {
  height: 10px;
  width: 30%;
}

.skeleton-line.tiny {
  width: 52%;
}

.skeleton-mark {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  margin: 12px 0;
}

@keyframes shimmer {
  to {
    background-position: -200% 0;
  }
}

@media (max-width: 1100px) {
  .kb-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .page-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 18px;
  }

  .archive-summary {
    flex-wrap: wrap;
    gap: 16px;
  }

  .summary-note {
    width: 100%;
    margin-left: 0;
  }

  .kb-grid {
    grid-template-columns: 1fr;
  }

  .kb-card {
    min-height: 264px;
  }
}
</style>
