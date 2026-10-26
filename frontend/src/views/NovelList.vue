<template>
  <div class="novel-page fade-rise">
    <header class="page-head">
      <div class="head-copy">
        <p class="page-kicker">YOUR SHELF</p>
        <h1 class="page-title">我的书架</h1>
        <p class="page-subtitle">
          每一本书都从一张空白稿纸开始。继续写，或者开一本新的。
        </p>
      </div>
      <el-button type="primary" :icon="Plus" class="head-action" @click="showCreateDialog = true">
        创建小说
      </el-button>
    </header>

    <section class="shelf-summary">
      <div class="summary-item">
        <span class="summary-value">{{ String(novels.length).padStart(2, '0') }}</span>
        <span class="summary-label">在写作品</span>
      </div>
      <span class="summary-divider" />
      <div class="summary-item">
        <span class="summary-value">{{ String(totalChapters).padStart(2, '0') }}</span>
        <span class="summary-label">已写章节</span>
      </div>
      <span class="summary-divider" />
      <p class="summary-note">
        <span class="note-dot" /> 写作台上的一切都会自动保存
      </p>
    </section>

    <div v-if="loading" class="shelf-grid">
      <div v-for="i in 2" :key="i" class="novel-card skeleton-card">
        <div class="skeleton-cover" />
        <div class="skeleton-copy">
          <span class="skeleton-line short" />
          <span class="skeleton-line" />
          <span class="skeleton-line tiny" />
          <span class="skeleton-line" />
        </div>
      </div>
    </div>

    <section v-else-if="!novels.length" class="empty-shelf">
      <span class="empty-index">01</span>
      <div class="empty-book">
        <span class="empty-book-mark">✳</span>
        <span class="empty-book-line" />
        <span class="empty-book-line short" />
      </div>
      <h2>书架还空着</h2>
      <p>创建第一本小说，把人物、大纲和第一章放上去。故事就从这里开始。</p>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
        写下第一本
      </el-button>
    </section>

    <section v-else class="shelf-grid">
      <article
        v-for="(novel, index) in novels"
        :key="novel.id"
        class="novel-card hover-lift"
        @click="$router.push(`/novel/${novel.id}`)"
      >
        <div class="book-cover" :style="coverStyle(novel)">
          <span class="cover-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <span class="cover-initial">{{ titleInitial(novel.title) }}</span>
          <div class="cover-bottom">
            <span class="cover-genre">{{ novel.genre || '未分类' }}</span>
            <span class="cover-label">AI NOVEL</span>
          </div>
          <span class="cover-spine" />
        </div>

        <div class="novel-info">
          <div class="info-top">
            <span class="info-index">BOOK {{ String(novel.id).padStart(3, '0') }}</span>
            <span class="info-date">{{ formatTime(novel.created_at) }}</span>
          </div>

          <h2 class="novel-title">{{ novel.title }}</h2>
          <p class="novel-desc">
            {{ novel.description || '还没有写简介。打开它，补上这本书的第一句话。' }}
          </p>

          <div class="novel-meta">
            <span class="meta-pill">
              <el-icon><Document /></el-icon>
              {{ novel.chapter_count || 0 }} 章
            </span>
            <span class="meta-pill" v-if="novel.genre">
              <el-icon><CollectionTag /></el-icon>
              {{ novel.genre }}
            </span>
          </div>

          <div class="card-footer">
            <button type="button" class="open-link" @click.stop="$router.push(`/novel/${novel.id}`)">
              继续写
              <el-icon><Right /></el-icon>
            </button>
            <button
              type="button"
              class="delete-link"
              aria-label="删除小说"
              @click.stop="onDelete(novel)"
            >
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
      </article>
    </section>

    <el-dialog
      v-model="showCreateDialog"
      title="创建小说项目"
      width="560px"
      @closed="resetCreateForm"
    >
      <p class="dialog-lead">选择一种开始方式。新项目会立刻建立，随后进入写作台。</p>

      <el-form :model="form" label-position="top" class="create-form">
        <el-form-item label="创作模式">
          <el-radio-group v-model="form.mode" class="mode-switch">
            <el-radio-button label="new">全新创作</el-radio-button>
            <el-radio-button label="continue">导入续写</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="小说名">
          <el-input v-model="form.title" placeholder="给这本书起一个名字" maxlength="200" show-word-limit />
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
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="简单描述小说内容（续写模式可留空，AI 会自动生成）"
          />
        </el-form-item>

        <el-form-item v-if="form.mode === 'continue'" label="导入文件">
          <el-upload
            class="import-upload"
            :show-file-list="true"
            :auto-upload="false"
            :limit="1"
            accept=".txt"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
          >
            <el-button type="primary" :icon="Upload">选择 TXT 文件</el-button>
            <template #tip>
              <div class="upload-tip">
                上传已有小说 TXT，AI 会自动拆分章节、提取角色、生成大纲和记忆。
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate">
          {{ form.mode === 'continue' ? '创建并导入' : '创建并开始写' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Delete, Upload, Document, CollectionTag, Right,
} from '@element-plus/icons-vue'
import { listNovels, createNovel, deleteNovel, importNovelText } from '../api/novel'
import { bookCoverStyle, bookInitial } from '../utils/bookCover'

const router = useRouter()
const novels = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const form = ref({ title: '', genre: '', description: '', mode: 'new' })
const importFile = ref(null)

const totalChapters = computed(() => novels.value.reduce((sum, novel) => sum + (novel.chapter_count || 0), 0))

const coverStyle = (novel) => bookCoverStyle(novel.genre)
const titleInitial = bookInitial

function onFileChange(file) {
  importFile.value = file.raw
}

function onFileRemove() {
  importFile.value = null
}

function resetCreateForm() {
  form.value = { title: '', genre: '', description: '', mode: 'new' }
  importFile.value = null
}

async function fetchList() {
  loading.value = true
  try {
    novels.value = await listNovels()
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  if (!form.value.title) {
    ElMessage.warning('请输入小说名称')
    return
  }
  if (form.value.mode === 'continue' && !importFile.value) {
    ElMessage.warning('续写模式请上传 TXT 文件')
    return
  }

  creating.value = true
  try {
    const novel = await createNovel({
      title: form.value.title,
      genre: form.value.genre,
      description: form.value.description,
      style_guide: '',
    })

    if (form.value.mode === 'continue' && importFile.value) {
      ElMessage.info('正在导入并 AI 解析，请耐心等待...')
      try {
        const result = await importNovelText(novel.id, importFile.value)
        ElMessage.success(`导入成功：${result.chapters_imported} 章，${result.characters_extracted} 个角色`)
      } catch (e) {
        ElMessage.error('导入失败，项目已保留，可在详情页重新导入')
        router.push(`/novel/${novel.id}`)
        return
      }
    } else {
      ElMessage.success('创建成功')
    }

    showCreateDialog.value = false
    resetCreateForm()
    router.push(`/novel/${novel.id}`)
  } finally {
    creating.value = false
  }
}

async function onDelete(novel) {
  try {
    await ElMessageBox.confirm(
      `确定要删除小说「${novel.title}」吗？所有章节和角色将一并删除。`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteNovel(novel.id)
    ElMessage.success('已删除')
    fetchList()
  } catch {
    // cancelled
  }
}

function formatTime(t) {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

onMounted(fetchList)
</script>

<style scoped>
.novel-page {
  max-width: 1360px;
  margin: 0 auto;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 28px;
  margin-bottom: 32px;
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

.shelf-summary {
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

.shelf-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.novel-card {
  display: grid;
  grid-template-columns: 144px minmax(0, 1fr);
  gap: 22px;
  min-height: 238px;
  padding: 18px;
  border: 1px solid var(--color-hairline);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  overflow: hidden;
}

.book-cover {
  position: relative;
  min-height: 202px;
  border-radius: 8px 12px 12px 8px;
  padding: 16px 15px 14px 22px;
  color: #faf9f5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 8px 12px 28px rgba(24, 23, 21, 0.18);
  transform: rotate(-1deg);
  transition: transform var(--dur-base) var(--ease-out);
}

.novel-card:hover .book-cover {
  transform: rotate(0deg) translateY(-3px);
}

.cover-spine {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 9px;
  background: rgba(0, 0, 0, 0.2);
  border-right: 1px solid rgba(255, 255, 255, 0.15);
}

.cover-index {
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 1px;
  color: rgba(250, 249, 245, 0.55);
}

.cover-initial {
  margin: auto 0;
  font-family: var(--font-serif);
  font-size: 76px;
  line-height: 1;
  color: var(--cover-accent);
  opacity: 0.92;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.cover-bottom {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.16);
}

.cover-genre {
  font-size: 10px;
  letter-spacing: 0.8px;
  color: rgba(250, 249, 245, 0.9);
}

.cover-label {
  font-family: var(--font-mono);
  font-size: 7px;
  letter-spacing: 1.5px;
  color: rgba(250, 249, 245, 0.4);
}

.novel-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 2px 0;
}

.info-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.info-index {
  font-family: var(--font-mono);
  font-size: 8.5px;
  letter-spacing: 1.2px;
  color: var(--color-muted-soft);
}

.info-date {
  font-size: 9.5px;
  color: var(--color-muted-soft);
}

.novel-title {
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 400;
  line-height: 1.2;
  letter-spacing: -0.5px;
  color: var(--color-ink);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.novel-desc {
  font-size: 12.5px;
  line-height: 1.65;
  color: var(--color-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 41px;
  margin-bottom: 13px;
}

.novel-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-bottom: auto;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 9px;
  border-radius: 999px;
  background: var(--color-surface-soft);
  color: var(--color-muted);
  font-size: 10px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16px;
  margin-top: 14px;
  border-top: 1px solid var(--color-hairline-soft);
}

.open-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-primary);
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
}

.open-link .el-icon {
  font-size: 10px;
  transition: transform var(--dur-fast);
}

.open-link:hover .el-icon {
  transform: translateX(3px);
}

.delete-link {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-muted-soft);
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--dur-fast), color var(--dur-fast), background var(--dur-fast);
}

.novel-card:hover .delete-link {
  opacity: 1;
}

.delete-link:hover {
  color: var(--color-error);
  background: rgba(198, 69, 69, 0.08);
}

.empty-shelf {
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

.empty-book {
  width: 94px;
  height: 124px;
  padding: 16px 13px;
  border-radius: 6px 10px 10px 6px;
  background: var(--color-surface-dark);
  color: var(--color-primary);
  box-shadow: 10px 12px 0 rgba(204, 120, 92, 0.14);
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin-bottom: 22px;
  transform: rotate(-3deg);
}

.empty-book-mark {
  font-size: 18px;
}

.empty-book-line {
  height: 1px;
  background: rgba(250, 249, 245, 0.22);
}

.empty-book-line.short {
  width: 62%;
}

.empty-shelf h2 {
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 400;
  letter-spacing: -0.5px;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.empty-shelf p {
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

.create-form :deep(.el-form-item__label) {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.6px;
  color: var(--color-muted);
}

.mode-switch :deep(.el-radio-button__inner) {
  height: 38px;
  padding: 0 18px;
  line-height: 36px;
  border-radius: 8px;
  font-size: 12px;
}

.mode-switch :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 8px 0 0 8px;
}

.mode-switch :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 8px 8px 0;
}

.upload-tip {
  font-size: 11px;
  line-height: 1.6;
  color: var(--color-muted-soft);
  margin-top: 5px;
}

.skeleton-card {
  cursor: default;
}

.skeleton-cover {
  min-height: 202px;
  border-radius: 8px 12px 12px 8px;
  background: linear-gradient(90deg, #e8e0d2, #f5f0e8, #e8e0d2);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-copy {
  display: flex;
  flex-direction: column;
  gap: 13px;
  padding-top: 8px;
}

.skeleton-line {
  height: 10px;
  border-radius: 4px;
  width: 80%;
  background: linear-gradient(90deg, #f0ebe2, #f8f4ec, #f0ebe2);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-line.short {
  width: 24%;
  height: 8px;
}

.skeleton-line.tiny {
  width: 56%;
}

@keyframes shimmer {
  to {
    background-position: -200% 0;
  }
}

@media (max-width: 1080px) {
  .shelf-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .page-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 18px;
  }

  .shelf-summary {
    flex-wrap: wrap;
    gap: 16px;
  }

  .summary-note {
    width: 100%;
    margin-left: 0;
  }

  .novel-card {
    grid-template-columns: 108px minmax(0, 1fr);
    gap: 16px;
    min-height: 200px;
    padding: 14px;
  }

  .book-cover {
    min-height: 172px;
    padding-left: 18px;
  }

  .cover-initial {
    font-size: 56px;
  }

  .novel-title {
    font-size: 21px;
  }

  .novel-desc {
    -webkit-line-clamp: 2;
  }

  .delete-link {
    opacity: 1;
  }

  .empty-shelf {
    min-height: 350px;
    padding: 34px 22px;
  }
}

@media (max-width: 440px) {
  .novel-card {
    grid-template-columns: 84px minmax(0, 1fr);
    gap: 13px;
  }

  .book-cover {
    min-height: 150px;
  }

  .cover-initial {
    font-size: 44px;
  }

  .cover-genre,
  .cover-label,
  .cover-index {
    font-size: 7px;
  }

  .novel-meta {
    display: none;
  }
}
</style>
