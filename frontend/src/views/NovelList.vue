<template>
  <div class="novel-list">
    <div class="page-header">
      <h2>我的小说</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
        创建小说
      </el-button>
    </div>

    <el-row :gutter="16" v-if="novels.length > 0">
      <el-col :span="8" v-for="novel in novels" :key="novel.id" style="margin-bottom: 16px">
        <el-card class="novel-card" shadow="hover" @click="$router.push(`/novel/${novel.id}`)">
          <div class="card-content">
            <div class="novel-title">{{ novel.title }}</div>
            <div class="novel-meta">
              <el-tag v-if="novel.genre" size="small">{{ novel.genre }}</el-tag>
              <span class="chapter-count">{{ novel.chapter_count }} 章</span>
            </div>
            <div class="novel-desc" v-if="novel.description">
              {{ novel.description.length > 50 ? novel.description.slice(0, 50) + '...' : novel.description }}
            </div>
            <div class="novel-time">{{ formatTime(novel.created_at) }}</div>
          </div>
          <div class="card-actions" @click.stop>
            <el-button size="small" :icon="Delete" circle @click="onDelete(novel)" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-else description="还没有小说项目，开始创作吧！" :image-size="120">
      <el-button type="primary" @click="showCreateDialog = true">创建第一部小说</el-button>
    </el-empty>

    <el-dialog v-model="showCreateDialog" title="创建小说项目" width="540px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="创作模式">
          <el-radio-group v-model="form.mode">
            <el-radio-button label="new">首写（全新创作）</el-radio-button>
            <el-radio-button label="continue">续写（导入已有内容）</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="小说名">
          <el-input v-model="form.title" placeholder="请输入小说名称" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.genre" placeholder="选择类型" allow-create filterable style="width: 100%">
            <el-option label="玄幻" value="玄幻" />
            <el-option label="都市" value="都市" />
            <el-option label="言情" value="言情" />
            <el-option label="科幻" value="科幻" />
            <el-option label="悬疑" value="悬疑" />
            <el-option label="历史" value="历史" />
            <el-option label="武侠" value="武侠" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="简单描述小说内容（续写模式可留空，AI会自动生成）" />
        </el-form-item>
        <el-form-item v-if="form.mode === 'continue'" label="导入文件">
          <el-upload
            :show-file-list="true"
            :auto-upload="false"
            :limit="1"
            accept=".txt"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
          >
            <el-button type="primary" :icon="Upload">选择TXT文件</el-button>
            <template #tip>
              <div style="font-size: 12px; color: #909399; margin-top: 4px">
                上传已有小说TXT文件，AI会自动拆分章节、提取角色、生成大纲和记忆
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate">
          {{ form.mode === 'continue' ? '创建并导入' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Upload } from '@element-plus/icons-vue'
import { listNovels, createNovel, deleteNovel, importNovelText } from '../api/novel'

const router = useRouter()
const novels = ref([])
const showCreateDialog = ref(false)
const creating = ref(false)
const form = ref({ title: '', genre: '', description: '', mode: 'new' })
const importFile = ref(null)

function onFileChange(file) {
  importFile.value = file.raw
}

function onFileRemove() {
  importFile.value = null
}

async function fetchList() {
  try {
    novels.value = await listNovels()
  } catch (e) { /* handled by interceptor */ }
}

async function onCreate() {
  if (!form.value.title) {
    ElMessage.warning('请输入小说名称')
    return
  }
  if (form.value.mode === 'continue' && !importFile.value) {
    ElMessage.warning('续写模式请上传TXT文件')
    return
  }

  creating.value = true
  try {
    // 先创建小说项目
    const novel = await createNovel({
      title: form.value.title,
      genre: form.value.genre,
      description: form.value.description,
      style_guide: '',
    })

    // 续写模式：导入文件
    if (form.value.mode === 'continue' && importFile.value) {
      ElMessage.info('正在导入并AI解析，请耐心等待...')
      try {
        const result = await importNovelText(novel.id, importFile.value)
        ElMessage.success(`导入成功：${result.chapters_imported}章，${result.characters_extracted}个角色`)
      } catch (e) {
        ElMessage.error('导入失败，请重试')
      }
    } else {
      ElMessage.success('创建成功')
    }

    showCreateDialog.value = false
    form.value = { title: '', genre: '', description: '', mode: 'new' }
    importFile.value = null
    router.push(`/novel/${novel.id}`)
  } finally {
    creating.value = false
  }
}

async function onDelete(novel) {
  try {
    await ElMessageBox.confirm(`确定要删除小说「${novel.title}」吗？所有章节和角色将一并删除。`, '删除确认', { type: 'warning' })
    await deleteNovel(novel.id)
    ElMessage.success('已删除')
    fetchList()
  } catch { /* cancelled */ }
}

function formatTime(t) {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(fetchList)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.novel-card {
  cursor: pointer;
  transition: transform 0.2s;
  position: relative;
}

.novel-card:hover {
  transform: translateY(-2px);
}

.card-content {
  padding: 8px;
}

.novel-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.novel-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.chapter-count {
  font-size: 12px;
  color: #909399;
}

.novel-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.5;
}

.novel-time {
  font-size: 12px;
  color: #c0c4cc;
}

.card-actions {
  position: absolute;
  top: 12px;
  right: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.novel-card:hover .card-actions {
  opacity: 1;
}
</style>
