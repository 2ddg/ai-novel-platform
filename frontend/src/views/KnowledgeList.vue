<template>
  <div class="knowledge-list">
    <div class="page-header">
      <h2>知识库管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
        新建知识库
      </el-button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrap">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-else-if="!list.length"
      description="还没有知识库，点击右上角新建"
    />

    <!-- 卡片列表 -->
    <el-row v-else :gutter="20">
      <el-col
        v-for="kb in list"
        :key="kb.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
      >
        <el-card class="kb-card" shadow="hover" @click="goDetail(kb)">
          <div class="kb-icon">
            <el-icon :size="40" color="#409eff"><FolderOpened /></el-icon>
          </div>
          <div class="kb-info">
            <h3 class="kb-name" :title="kb.name">{{ kb.name }}</h3>
            <p class="kb-desc" :title="kb.description || '暂无描述'">
              {{ kb.description || '暂无描述' }}
            </p>
            <div class="kb-meta">
              <span><el-icon><Document /></el-icon> {{ kb.document_count }} 文档</span>
              <span>{{ formatDate(kb.created_at) }}</span>
            </div>
          </div>
          <div class="kb-actions" @click.stop>
            <el-button
              type="primary"
              size="small"
              :icon="ChatDotRound"
              circle
              @click="goChat(kb)"
            />
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              circle
              @click="onDelete(kb)"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建知识库" width="440px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="给知识库起个名字" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="简单描述这个知识库的用途（选填）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Loading, FolderOpened, Document, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { listKnowledge, createKnowledge, deleteKnowledge } from '../api/knowledge'

const router = useRouter()

const loading = ref(false)
const list = ref([])

const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref()
const createForm = ref({ name: '', description: '' })
const createRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
}

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
      `确定要删除知识库「${kb.name}」吗？该知识库的所有文档和对话历史将一并删除。`,
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
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

onMounted(fetchList)
</script>

<style scoped>
.knowledge-list {
  max-width: 1400px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 20px;
  color: #303133;
}

.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 60px;
  color: #409eff;
}

.kb-card {
  position: relative;
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.2s;
  border-radius: 8px;
}

.kb-card:hover {
  transform: translateY(-4px);
}

.kb-icon {
  text-align: center;
  padding: 20px 0 12px;
}

.kb-info {
  padding: 0 4px;
}

.kb-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-desc {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
  height: 36px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.kb-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.kb-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.kb-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.kb-card:hover .kb-actions {
  opacity: 1;
}
</style>
