<template>
  <div class="kb-detail fade-rise">
    <button type="button" class="back-link" @click="$router.push('/knowledge')">
      <el-icon><ArrowLeft /></el-icon>
      返回资料室
    </button>

    <header class="detail-head">
      <div class="head-copy">
        <p class="page-kicker">ARCHIVE · {{ String(kbId).padStart(2, '0') }}</p>
        <h1 class="detail-title">{{ kbName }}</h1>
        <p class="detail-sub">
          {{ docs.length }} 份文档 · {{ totalChunks }} 个知识分块 · {{ totalSizeLabel }}
        </p>
      </div>
      <div class="head-actions">
        <el-button :icon="ChatDotRound" @click="$router.push(`/chat/${kbId}`)">
          去对话
        </el-button>
        <el-upload
          :show-file-list="false"
          :before-upload="beforeUpload"
          :http-request="handleUpload"
          multiple
          accept=".txt,.md,.pdf,.doc,.docx,.html,.json,.csv"
        >
          <el-button type="primary" :icon="Upload" :loading="uploading">
            {{ uploading ? '入库中...' : '上传文档' }}
          </el-button>
        </el-upload>
      </div>
    </header>

    <div v-if="uploading" class="upload-panel">
      <div class="upload-copy">
        <span class="upload-state">{{ uploadCopy }}</span>
        <span class="upload-percent">{{ uploadProgress }}%</span>
      </div>
      <el-progress :percentage="uploadProgress" :show-text="false" :stroke-width="4" />
    </div>

    <div class="detail-grid">
      <section class="doc-panel">
        <div class="panel-head">
          <div>
            <span class="panel-kicker">DOCUMENTS</span>
            <h2>文档目录</h2>
          </div>
          <span class="panel-count">{{ String(docs.length).padStart(2, '0') }}</span>
        </div>

        <div v-if="loading" class="doc-skeletons">
          <div v-for="i in 4" :key="i" class="doc-skeleton">
            <span class="skeleton-icon" />
            <div class="skeleton-copy">
              <span class="skeleton-line" />
              <span class="skeleton-line tiny" />
            </div>
          </div>
        </div>

        <div v-else-if="!docs.length" class="doc-empty">
          <div class="empty-icon"><el-icon :size="26"><Document /></el-icon></div>
          <h3>还没有文档入库</h3>
          <p>上传设定集、人物小传、参考文章或写作笔记，AI 问答会优先检索这里的内容。</p>
          <el-upload
            :show-file-list="false"
            :before-upload="beforeUpload"
            :http-request="handleUpload"
            multiple
            accept=".txt,.md,.pdf,.doc,.docx,.html,.json,.csv"
          >
            <el-button type="primary" :icon="Upload">上传第一份文档</el-button>
          </el-upload>
        </div>

        <div v-else class="doc-list">
          <article v-for="(doc, index) in docs" :key="doc.id" class="doc-row">
            <span class="doc-index">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="doc-icon"><el-icon><Document /></el-icon></span>
            <div class="doc-main">
              <h3 class="doc-name" :title="doc.filename">{{ doc.filename }}</h3>
              <div class="doc-meta">
                <span>{{ formatSize(doc.file_size) }}</span>
                <span class="meta-dot" />
                <span>{{ doc.chunk_count }} 个分块</span>
                <span class="meta-dot" />
                <span>{{ formatDate(doc.uploaded_at) }}</span>
              </div>
            </div>
            <el-button
              class="doc-delete"
              type="danger"
              text
              size="small"
              :icon="Delete"
              @click="onDeleteDoc(doc)"
            >
              删除
            </el-button>
          </article>
        </div>
      </section>

      <aside class="detail-aside">
        <div class="aside-card">
          <span class="panel-kicker">HOW IT WORKS</span>
          <h3>一份文档的入库路径</h3>
          <ol class="process-list">
            <li>
              <span>01</span>
              <div>
                <strong>上传</strong>
                <p>支持 TXT、Markdown、PDF、Word 等格式。</p>
              </div>
            </li>
            <li>
              <span>02</span>
              <div>
                <strong>解析与切块</strong>
                <p>长文会被拆成可检索的知识分块。</p>
              </div>
            </li>
            <li>
              <span>03</span>
              <div>
                <strong>向量化</strong>
                <p>生成语义索引，问答时按相关性召回。</p>
              </div>
            </li>
          </ol>
        </div>

        <div class="aside-note">
          <span class="note-mark">✳</span>
          <p>首次上传会加载 Embedding 模型，可能稍慢。后续文档会快很多。</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Upload, Document, Delete, ChatDotRound,
} from '@element-plus/icons-vue'
import { listDocuments, uploadDocument, deleteDocument } from '../api/knowledge'

const route = useRoute()
const kbId = computed(() => parseInt(route.params.id))
const kbName = ref('')
const docs = ref([])
const loading = ref(false)

const uploading = ref(false)
const uploadProgress = ref(0)

const totalChunks = computed(() => docs.value.reduce((sum, doc) => sum + (doc.chunk_count || 0), 0))
const totalSize = computed(() => docs.value.reduce((sum, doc) => sum + (doc.file_size || 0), 0))
const totalSizeLabel = computed(() => formatSize(totalSize.value))

const uploadCopy = computed(() => {
  if (uploadProgress.value < 30) return '正在上传文件'
  if (uploadProgress.value < 70) return '正在解析与切块'
  if (uploadProgress.value < 100) return '正在生成向量索引'
  return '入库完成'
})

async function fetchDocs() {
  loading.value = true
  try {
    docs.value = await listDocuments(kbId.value)
  } finally {
    loading.value = false
  }
}

function beforeUpload(file) {
  const allowed = ['.txt', '.md', '.pdf', '.doc', '.docx', '.html', '.json', '.csv']
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!allowed.includes(ext)) {
    ElMessage.error(`不支持的文件类型：${ext}`)
    return false
  }
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件超过 50MB')
    return false
  }
  return true
}

async function handleUpload(options) {
  uploading.value = true
  uploadProgress.value = 5

  const timer = setInterval(() => {
    if (uploadProgress.value < 90) {
      uploadProgress.value += Math.floor(Math.random() * 8 + 2)
    }
  }, 500)

  try {
    const res = await uploadDocument(kbId.value, options.file)
    uploadProgress.value = 100
    ElMessage.success(`上传成功，共 ${res.chunks_count} 个分块`)
    fetchDocs()
  } catch (e) {
    uploadProgress.value = 0
  } finally {
    clearInterval(timer)
    setTimeout(() => {
      uploading.value = false
      uploadProgress.value = 0
    }, 800)
  }
}

async function onDeleteDoc(doc) {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档「${doc.filename}」吗？该文档的所有向量分块也会一并删除。`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteDocument(kbId.value, doc.id)
    ElMessage.success('已删除')
    fetchDocs()
  } catch {
    // 用户取消或删除失败
  }
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

function formatDate(str) {
  if (!str) return ''
  const d = new Date(str)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => {
  kbName.value = route.query.name || `资料库 #${kbId.value}`
  fetchDocs()
})
</script>

<style scoped>
.kb-detail {
  max-width: 1320px;
  margin: 0 auto;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 22px;
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 11.5px;
  color: var(--color-muted);
  cursor: pointer;
  transition: color var(--dur-fast);
}

.back-link:hover {
  color: var(--color-primary);
}

.detail-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 28px;
  padding-bottom: 30px;
  border-bottom: 1px solid var(--color-hairline);
  margin-bottom: 26px;
}

.head-copy {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.detail-title {
  font-family: var(--font-serif);
  font-size: clamp(34px, 4vw, 50px);
  font-weight: 400;
  line-height: 1.06;
  letter-spacing: -1.2px;
  color: var(--color-ink);
  overflow-wrap: anywhere;
}

.detail-sub {
  font-size: 12px;
  color: var(--color-muted);
  letter-spacing: 0.2px;
}

.head-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
}

.upload-panel {
  padding: 16px 20px;
  margin-bottom: 22px;
  border: 1px solid rgba(204, 120, 92, 0.26);
  border-radius: 12px;
  background: rgba(204, 120, 92, 0.06);
}

.upload-copy {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 11px;
}

.upload-state {
  color: var(--color-primary-active);
  font-weight: 600;
}

.upload-percent {
  font-family: var(--font-mono);
  color: var(--color-muted);
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 286px;
  gap: 26px;
  align-items: start;
}

.doc-panel {
  border: 1px solid var(--color-hairline);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.66);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-hairline-soft);
  background: rgba(245, 240, 232, 0.48);
}

.panel-kicker {
  display: block;
  margin-bottom: 5px;
  font-size: 9px;
  letter-spacing: 1.8px;
  color: var(--color-muted-soft);
}

.panel-head h2 {
  font-family: var(--font-serif);
  font-size: 21px;
  font-weight: 400;
  letter-spacing: -0.3px;
  color: var(--color-ink);
}

.panel-count {
  font-family: var(--font-serif);
  font-size: 32px;
  line-height: 1;
  color: var(--color-primary);
  letter-spacing: -0.8px;
}

.doc-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-hairline-soft);
  transition: background var(--dur-fast);
}

.doc-row:last-child {
  border-bottom: 0;
}

.doc-row:hover {
  background: rgba(245, 240, 232, 0.44);
}

.doc-index {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--color-muted-soft);
  width: 18px;
  flex: 0 0 18px;
}

.doc-icon {
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  display: grid;
  place-items: center;
  border-radius: 9px;
  background: var(--color-surface-soft);
  color: var(--color-primary);
}

.doc-main {
  min-width: 0;
  flex: 1;
}

.doc-name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--color-ink);
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 10.5px;
  color: var(--color-muted-soft);
}

.meta-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--color-hairline);
}

.doc-delete {
  opacity: 0;
  transition: opacity var(--dur-fast);
}

.doc-row:hover .doc-delete {
  opacity: 1;
}

.detail-aside {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.aside-card {
  padding: 22px;
  border: 1px solid var(--color-hairline);
  border-radius: 16px;
  background: var(--color-surface-dark);
  color: var(--color-on-dark);
}

.aside-card .panel-kicker {
  color: var(--color-on-dark-soft);
}

.aside-card h3 {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 400;
  line-height: 1.3;
  letter-spacing: -0.3px;
  color: var(--color-on-dark);
  margin-bottom: 20px;
}

.process-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.process-list li {
  display: flex;
  gap: 12px;
}

.process-list li > span {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--color-primary);
  padding-top: 3px;
}

.process-list strong {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-on-dark);
  margin-bottom: 3px;
}

.process-list p {
  font-size: 10.5px;
  line-height: 1.6;
  color: var(--color-on-dark-soft);
}

.aside-note {
  display: flex;
  gap: 11px;
  padding: 18px;
  border: 1px dashed var(--color-hairline);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.4);
}

.note-mark {
  color: var(--color-primary);
  font-size: 16px;
  line-height: 1.3;
}

.aside-note p {
  font-size: 10.5px;
  line-height: 1.7;
  color: var(--color-muted);
}

.doc-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 58px 28px 64px;
  text-align: center;
}

.empty-icon {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--color-surface-soft);
  color: var(--color-primary);
  margin-bottom: 16px;
}

.doc-empty h3 {
  font-family: var(--font-serif);
  font-size: 23px;
  font-weight: 400;
  color: var(--color-ink);
  margin-bottom: 7px;
}

.doc-empty p {
  max-width: 390px;
  font-size: 12px;
  line-height: 1.7;
  color: var(--color-muted);
  margin-bottom: 20px;
}

.doc-skeleton {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 24px;
  border-bottom: 1px solid var(--color-hairline-soft);
}

.skeleton-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  flex: 0 0 36px;
  background: #f0ebe2;
}

.skeleton-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.skeleton-line {
  display: block;
  width: 42%;
  height: 10px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0ebe2, #f8f4ec, #f0ebe2);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-line.tiny {
  width: 26%;
  height: 8px;
}

@keyframes shimmer {
  to {
    background-position: -200% 0;
  }
}

@media (max-width: 1000px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-aside {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 700px) {
  .detail-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 18px;
  }

  .head-actions {
    width: 100%;
  }

  .head-actions :deep(.el-button) {
    flex: 1;
  }

  .head-actions :deep(.el-upload) {
    flex: 1;
  }

  .head-actions :deep(.el-upload .el-button) {
    width: 100%;
  }

  .doc-row {
    padding: 15px 16px;
    gap: 10px;
  }

  .doc-index {
    display: none;
  }

  .doc-delete {
    opacity: 1;
  }

  .detail-aside {
    display: flex;
  }

  .doc-meta span:nth-child(n + 4) {
    display: none;
  }
}
</style>
