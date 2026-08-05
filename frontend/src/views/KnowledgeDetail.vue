<template>
  <div class="kb-detail">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="$router.push('/knowledge')">返回</el-button>
        <h2>{{ kbName }}</h2>
      </div>
      <div class="header-actions">
        <el-upload
          :show-file-list="false"
          :before-upload="beforeUpload"
          :http-request="handleUpload"
          multiple
          accept=".txt,.md,.pdf,.doc,.docx,.html,.json,.csv"
        >
          <el-button type="primary" :icon="Upload" :loading="uploading">
            {{ uploading ? '上传中...' : '上传文档' }}
          </el-button>
        </el-upload>
        <el-button :icon="ChatDotRound" @click="$router.push(`/chat/${kbId}`)">
          去对话
        </el-button>
      </div>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <el-progress :percentage="uploadProgress" :status="uploadProgress === 100 ? 'success' : undefined" />
      <span class="upload-tip">
        {{ uploadProgress < 30 ? '正在上传文件...' :
           uploadProgress < 70 ? '正在加载 Embedding 模型（首次较慢）...' :
           uploadProgress < 100 ? '正在分块并向量化...' : '上传完成！' }}
      </span>
    </div>

    <!-- 文档列表 -->
    <el-card v-loading="loading" class="doc-card">
      <template #header>
        <span class="doc-title">文档列表（{{ docs.length }}）</span>
      </template>

      <el-empty v-if="!loading && !docs.length" description="还没有文档，点击右上角上传" />

      <el-table v-show="docs.length" :data="docs" stripe style="width: 100%">
        <el-table-column prop="filename" label="文件名" min-width="240">
          <template #default="{ row }">
            <div class="file-name">
              <el-icon :size="18" color="#409eff"><Document /></el-icon>
              <span>{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="120">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="分块数" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.chunk_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_at" label="上传时间" width="180">
          <template #default="{ row }">{{ formatDate(row.uploaded_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              text
              :icon="Delete"
              @click="onDeleteDoc(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Upload, Document, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { listDocuments, uploadDocument, deleteDocument } from '../api/knowledge'

const route = useRoute()
const kbId = computed(() => parseInt(route.params.id))
const kbName = ref('')
const docs = ref([])
const loading = ref(false)

const uploading = ref(false)
const uploadProgress = ref(0)

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

  // 模拟进度（实际进度无法从 fetch 得知，按阶段推进）
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
    // 错误已由 axios 拦截器统一提示
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
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => {
  // 从路由 query 取知识库名称（从列表页跳转过来时带的）
  kbName.value = route.query.name || `知识库 #${kbId.value}`
  fetchDocs()
})
</script>

<style scoped>
.kb-detail {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  font-size: 20px;
  color: #303133;
}

.upload-progress {
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 16px;
}

.upload-tip {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  color: #409eff;
}

.doc-card {
  border-radius: 8px;
}

.doc-title {
  font-weight: 600;
  font-size: 15px;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
