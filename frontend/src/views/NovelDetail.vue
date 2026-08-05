<template>
  <div class="novel-detail" v-loading="loading">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="$router.push('/novel')">返回</el-button>
        <h2 style="margin-left: 12px">{{ novel?.title }}</h2>
        <el-tag v-if="novel?.genre" style="margin-left: 8px">{{ novel.genre }}</el-tag>
      </div>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 基本信息 + 风格 -->
      <el-tab-pane label="基本信息" name="info">
        <el-form :model="editForm" label-width="100px" style="max-width: 700px">
          <el-form-item label="小说名">
            <el-input v-model="editForm.title" />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="editForm.genre" placeholder="选择类型" allow-create filterable style="width: 100%">
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
            <el-input v-model="editForm.description" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="写作风格">
            <el-input v-model="editForm.style_guide" type="textarea" :rows="12" placeholder="写作风格指南（可使用默认）" />
            <el-button link type="primary" @click="useDefaultStyle">使用默认风格模板</el-button>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="onSaveInfo">保存</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 角色设定 -->
      <el-tab-pane label="角色设定" name="characters">
        <div class="tab-header">
          <div>
            <el-button type="primary" :icon="Plus" @click="showCharDialog = true">添加角色</el-button>
            <el-button
              type="success"
              :icon="MagicStick"
              :loading="extractingChars"
              :disabled="!chapters.length"
              @click="onExtractCharacters"
            >
              AI扫描全文补充角色
            </el-button>
          </div>
        </div>
        <el-table :data="characters" style="width: 100%">
          <el-table-column prop="name" label="角色名" width="120" />
          <el-table-column prop="personality" label="性格" show-overflow-tooltip />
          <el-table-column prop="background" label="背景" show-overflow-tooltip />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="onEditChar(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="onDeleteChar(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-dialog v-model="showCharDialog" :title="editingChar ? '编辑角色' : '添加角色'" width="450px">
          <el-form :model="charForm" label-width="80px">
            <el-form-item label="角色名">
              <el-input v-model="charForm.name" />
            </el-form-item>
            <el-form-item label="性格">
              <el-input v-model="charForm.personality" type="textarea" :rows="2" placeholder="性格特征、说话风格等" />
            </el-form-item>
            <el-form-item label="背景">
              <el-input v-model="charForm.background" type="textarea" :rows="2" placeholder="身世、经历、动机等" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showCharDialog = false">取消</el-button>
            <el-button type="primary" @click="onSaveChar">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- 大纲 -->
      <el-tab-pane label="大纲" name="outline">
        <div class="tab-header">
          <div>
            <el-button type="primary" :icon="MagicStick" :loading="generating" @click="onGenerateOutline">
              {{ novel?.outline ? '重新生成大纲' : 'AI生成大纲' }}
            </el-button>
            <el-button
              type="success"
              :icon="MagicStick"
              :loading="regeneratingOutline"
              :disabled="!chapters.length"
              @click="onRegenerateOutline"
            >
              根据已有章节生成
            </el-button>
          </div>
        </div>
        <el-input
          v-model="outlineIdeas"
          type="textarea"
          :rows="4"
          placeholder="（可选）填写你的想法、思路或灵感片段，AI会围绕你的想法补足完整大纲。留空则由AI全自动生成。"
          style="margin-bottom: 12px"
        />
        <el-input
          v-model="outlineText"
          type="textarea"
          :rows="20"
          placeholder="AI生成的大纲将显示在这里，也可以手动编辑"
        />
        <div style="margin-top: 12px; text-align: right">
          <el-button type="primary" :loading="saving" @click="onSaveOutline">保存大纲</el-button>
        </div>
      </el-tab-pane>

      <!-- 章节 -->
      <el-tab-pane label="章节" name="chapters">
        <div class="tab-header">
          <span style="color: #909399">共 {{ chapters.length }} 章</span>
        </div>
        <el-table :data="chapters" style="width: 100%" @row-click="onOpenChapter">
          <el-table-column prop="chapter_num" label="第X章" width="80" />
          <el-table-column prop="title" label="标题" width="150" />
          <el-table-column prop="summary" label="摘要" show-overflow-tooltip />
          <el-table-column label="操作" width="200" @click.stop>
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="onOpenChapter(row)">继续写作</el-button>
              <el-button size="small" @click="onEditChapter(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="onDeleteChapter(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-divider />

        <div class="write-section">
          <h3>写新章节</h3>
          <el-form :model="writeForm" label-width="100px" inline>
            <el-form-item label="章节号">
              <el-input-number v-model="writeForm.chapter_num" :min="1" :max="999" />
            </el-form-item>
            <el-form-item label="标题">
              <el-input v-model="writeForm.title" placeholder="章节标题" style="width: 200px" />
            </el-form-item>
            <el-form-item label="章节要求">
              <el-input v-model="writeForm.chapter_outline" placeholder="本章主要事件/冲突" style="width: 300px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="writing" @click="onGenerateChapter">AI写作</el-button>
            </el-form-item>
            <el-form-item>
              <el-button type="success" :loading="streaming" @click="onStreamChapter">流式写作</el-button>
            </el-form-item>
          </el-form>
        </div>

        <div v-if="writingContent" class="chapter-preview">
          <div class="preview-header">
            <span>生成中...</span>
            <el-button size="small" @click="writingContent = ''">关闭</el-button>
          </div>
          <div class="preview-content">{{ writingContent }}</div>
        </div>
      </el-tab-pane>

      <!-- 记忆（分章节） -->
      <el-tab-pane label="记忆" name="memory">
        <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
          AI自动维护关键状态记忆：每章写完后自动生成对应记忆条目。记忆是给AI用的，确保续写时角色状态、伏笔、剧情不丢。
        </el-alert>

        <!-- 全局记忆 -->
        <el-card style="margin-bottom: 16px">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">全局记忆（跨章节）</span>
              <el-button
                size="small"
                type="success"
                :icon="MagicStick"
                :loading="generatingGlobalMemory"
                :disabled="!chapters.length"
                @click="onGenerateGlobalMemory"
              >
                AI生成
              </el-button>
            </div>
          </template>
          <el-input
            v-model="memoryGlobal"
            type="textarea"
            :rows="4"
            placeholder="全局记忆：贯穿整本小说的关键设定（如世界观、核心矛盾等）。点击AI生成可自动分析章节内容。"
          />
        </el-card>

        <!-- 分章记忆 -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px">
          <span style="font-weight: 600">分章记忆</span>
          <div>
            <el-button
              size="small"
              type="success"
              :icon="MagicStick"
              :loading="regeneratingMemory"
              :disabled="!chapters.length"
              @click="showRegenMemoryDialog = true"
            >
              AI重新生成记忆
            </el-button>
          </div>
        </div>
        <el-alert
          v-if="memoryChapters.length && memoryChapters.some(m => m.content && m.content.includes('临时记忆'))"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 12px"
        >
          当前记忆为导入时的临时摘要（内容前150字）。点击"AI重新生成记忆"可让AI分析章节内容，生成结构化记忆（角色状态、伏笔、剧情进展等）。
        </el-alert>
        <el-empty v-if="!memoryChapters.length" description="暂无分章记忆，写章节后会自动生成" :image-size="60" />
        <el-collapse v-else v-model="expandedMemories">
          <el-collapse-item
            v-for="mem in memoryChapters"
            :key="mem.id || mem.chapter_num"
            :name="mem.chapter_num"
          >
            <template #title>
              <span style="font-weight: 600">第{{ mem.chapter_num }}章后记忆</span>
              <el-tag v-if="mem.content && mem.content.includes('临时记忆')" size="small" type="warning" style="margin-left: 8px">临时</el-tag>
            </template>
            <el-input
              v-model="mem.content"
              type="textarea"
              :rows="6"
              placeholder="本章后的记忆状态"
            />
            <div style="margin-top: 8px; text-align: right">
              <el-button size="small" type="primary" @click="onSaveChapterMemory(mem)">保存此章记忆</el-button>
            </div>
          </el-collapse-item>
        </el-collapse>

        <div style="margin-top: 16px; text-align: right">
          <el-button type="primary" :loading="savingMemory" @click="onSaveAllMemory">保存全部记忆</el-button>
        </div>
      </el-tab-pane>

      <!-- 全文 + AI修改意见 -->
      <el-tab-pane label="全文" name="fulltext">
        <div class="tab-header">
          <span style="color: #909399">共 {{ chapters.length }} 章</span>
          <div>
            <el-button
              type="warning"
              :icon="MagicStick"
              :loading="reviewing"
              :disabled="!chapters.length"
              @click="showReviewDialog = true"
            >
              AI修改意见
            </el-button>
            <el-button
              type="success"
              :icon="Download"
              :disabled="!chapters.length"
              @click="showExportDialog = true"
            >
              导出
            </el-button>
          </div>
        </div>

        <!-- AI审阅结果 -->
        <el-card v-if="reviewResult" style="margin-bottom: 16px">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">AI修改建议</span>
              <el-button size="small" text @click="reviewResult = ''">关闭</el-button>
            </div>
          </template>
          <div class="review-content">{{ reviewResult }}</div>
        </el-card>

        <!-- 分章节表格 -->
        <el-table
          :data="chapters"
          style="width: 100%"
          @row-click="onEditChapter"
        >
          <el-table-column prop="chapter_num" label="第X章" width="80" />
          <el-table-column prop="title" label="标题" width="180" />
          <el-table-column prop="content" label="内容预览" show-overflow-tooltip>
            <template #default="{ row }">
              {{ (row.content || '').slice(0, 60) }}{{ (row.content || '').length > 60 ? '...' : '' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" @click.stop>
            <template #default="{ row }">
              <el-button size="small" @click.stop="onEditChapter(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 章节编辑器 -->
    <el-dialog v-model="showChapterEditor" :title="`第${editingChapter?.chapter_num || ''}章 编辑`" width="80%" top="5vh">
      <el-form v-if="editingChapter" label-width="60px">
        <el-form-item label="标题">
          <el-input v-model="editingChapter.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="editingChapter.content" type="textarea" :rows="20" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChapterEditor = false">取消</el-button>
        <el-button type="primary" :loading="savingChapter" @click="onSaveChapter">保存</el-button>
      </template>
    </el-dialog>

    <!-- AI修改意见：选择章节 -->
    <el-dialog v-model="showReviewDialog" title="AI修改意见" width="500px">
      <p style="color: #909399; margin-bottom: 12px">选择要审阅的章节，AI会扫描内容并提出修改建议（只提建议，不改写）：</p>
      <el-checkbox-group v-model="reviewSelected">
        <div v-for="ch in chapters" :key="ch.id" style="margin-bottom: 8px">
          <el-checkbox :label="ch.id">
            第{{ ch.chapter_num }}章 {{ ch.title || '' }}
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="reviewing"
          :disabled="!reviewSelected.length"
          @click="onReview"
        >
          开始审阅（{{ reviewSelected.length }}章）
        </el-button>
      </template>
    </el-dialog>

    <!-- AI重新生成记忆：选择章节 -->
    <el-dialog v-model="showRegenMemoryDialog" title="AI重新生成记忆" width="500px">
      <p style="color: #909399; margin-bottom: 12px">
        选择要重新生成记忆的章节（AI会分析章节内容，生成结构化记忆：角色状态、伏笔、剧情进展等）：
      </p>
      <div style="margin-bottom: 12px">
        <el-button size="small" @click="regenMemorySelected = chapters.map(c => c.chapter_num)">全选</el-button>
        <el-button size="small" @click="regenMemorySelected = []">清空</el-button>
      </div>
      <el-checkbox-group v-model="regenMemorySelected">
        <div v-for="ch in chapters" :key="ch.id" style="margin-bottom: 8px">
          <el-checkbox :label="ch.chapter_num">
            第{{ ch.chapter_num }}章 {{ ch.title || '' }}
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="showRegenMemoryDialog = false">取消</el-button>
        <el-button
          type="success"
          :loading="regeneratingMemory"
          :disabled="!regenMemorySelected.length"
          @click="onRegenerateMemory"
        >
          生成（{{ regenMemorySelected.length }}章）
        </el-button>
      </template>
    </el-dialog>

    <!-- 导出对话框 -->
    <el-dialog v-model="showExportDialog" title="导出章节" width="500px">
      <p style="color: #909399; margin-bottom: 12px">选择要导出的章节和格式：</p>
      <div style="margin-bottom: 12px">
        <el-button size="small" @click="exportSelected = chapters.map(c => c.id)">全选</el-button>
        <el-button size="small" @click="exportSelected = []">清空</el-button>
      </div>
      <el-checkbox-group v-model="exportSelected" style="margin-bottom: 16px">
        <div v-for="ch in chapters" :key="ch.id" style="margin-bottom: 8px">
          <el-checkbox :label="ch.id">
            第{{ ch.chapter_num }}章 {{ ch.title || '' }}
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <el-form-item label="格式" label-width="60px">
        <el-radio-group v-model="exportFormat">
          <el-radio-button label="txt">TXT</el-radio-button>
          <el-radio-button label="md">Markdown</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button
          type="success"
          :disabled="!exportSelected.length"
          @click="onExport"
        >
          导出（{{ exportSelected.length }}章）
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, MagicStick, Download } from '@element-plus/icons-vue'
import {
  getNovel, updateNovel, listCharacters, createCharacter, updateCharacter, deleteCharacter,
  generateOutline, listChapters, getChapter, updateChapter, deleteChapter,
  generateChapter, getMemory, updateMemory, reviewChapters, regenerateMemory,
  extractCharacters, regenerateOutline, generateGlobalMemory,
} from '../api/novel'
import { DEFAULT_STYLE_GUIDE } from '../config'

const route = useRoute()
const novelId = computed(() => route.params.id)

const loading = ref(false)
const saving = ref(false)
const generating = ref(false)
const writing = ref(false)
const streaming = ref(false)
const savingMemory = ref(false)
const savingChapter = ref(false)
const reviewing = ref(false)

const novel = ref(null)
const activeTab = ref('info')
const outlineText = ref('')
const outlineIdeas = ref('')
const memoryGlobal = ref('')
const memoryChapters = ref([])
const expandedMemories = ref([])
const characters = ref([])
const chapters = ref([])
const writingContent = ref('')

// AI审阅
const showReviewDialog = ref(false)
const reviewSelected = ref([])
const reviewResult = ref('')

// AI重新生成记忆
const showRegenMemoryDialog = ref(false)
const regenMemorySelected = ref([])
const regeneratingMemory = ref(false)

// 导出
const showExportDialog = ref(false)
const exportSelected = ref([])
const exportFormat = ref('txt')

// AI扫描补充角色 / 大纲 / 全局记忆
const extractingChars = ref(false)
const regeneratingOutline = ref(false)
const generatingGlobalMemory = ref(false)

const editForm = ref({ title: '', genre: '', description: '', style_guide: '' })

const showCharDialog = ref(false)
const editingChar = ref(null)
const charForm = ref({ name: '', personality: '', background: '' })

const showChapterEditor = ref(false)
const editingChapter = ref(null)

const writeForm = ref({ chapter_num: 1, title: '', chapter_outline: '' })

async function fetchData() {
  loading.value = true
  try {
    const [n, chars, chs, mem] = await Promise.all([
      getNovel(novelId.value),
      listCharacters(novelId.value),
      listChapters(novelId.value),
      getMemory(novelId.value).catch(() => ({ chapters: [], global: '' })),
    ])
    novel.value = n
    editForm.value = { title: n.title, genre: n.genre, description: n.description, style_guide: n.style_guide || '' }
    outlineText.value = n.outline || ''
    characters.value = chars
    chapters.value = chs
    // 分章节记忆
    memoryGlobal.value = mem.global || ''
    memoryChapters.value = mem.chapters || []
    if (chs.length > 0) {
      writeForm.value.chapter_num = chs[chs.length - 1].chapter_num + 1
    }
  } finally {
    loading.value = false
  }
}

function useDefaultStyle() {
  editForm.value.style_guide = DEFAULT_STYLE_GUIDE
}

async function onSaveInfo() {
  saving.value = true
  try {
    const n = await updateNovel(novelId.value, editForm.value)
    novel.value = n
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}

async function onGenerateOutline() {
  generating.value = true
  try {
    const result = await generateOutline(novelId.value, outlineIdeas.value)
    outlineText.value = result.outline
    ElMessage.success('大纲生成成功')
  } finally {
    generating.value = false
  }
}

async function onSaveOutline() {
  saving.value = true
  try {
    await updateNovel(novelId.value, {
      title: novel.value.title,
      genre: novel.value.genre,
      description: novel.value.description,
      style_guide: novel.value.style_guide,
      outline: outlineText.value,
    })
    ElMessage.success('大纲已保存')
  } finally {
    saving.value = false
  }
}

async function onSaveAllMemory() {
  savingMemory.value = true
  try {
    await updateMemory(novelId.value, {
      global: memoryGlobal.value,
      chapters: memoryChapters.value.map(m => ({ chapter_num: m.chapter_num, content: m.content })),
    })
    ElMessage.success('全部记忆已保存')
  } finally {
    savingMemory.value = false
  }
}

async function onSaveChapterMemory(mem) {
  try {
    await updateMemory(novelId.value, { chapter_num: mem.chapter_num, content: mem.content })
    ElMessage.success(`第${mem.chapter_num}章记忆已保存`)
  } catch { /* handled by interceptor */ }
}

// AI修改意见
async function onReview() {
  reviewing.value = true
  showReviewDialog.value = false
  try {
    const result = await reviewChapters(novelId.value, reviewSelected.value)
    reviewResult.value = result.suggestions
    activeTab.value = 'fulltext'
    ElMessage.success('审阅完成')
  } finally {
    reviewing.value = false
  }
}

// AI重新生成记忆
async function onRegenerateMemory() {
  regeneratingMemory.value = true
  showRegenMemoryDialog.value = false
  try {
    const result = await regenerateMemory(novelId.value, regenMemorySelected.value)
    const okCount = result.results.filter(r => r.status === 'ok').length
    const failCount = result.results.filter(r => r.status === 'failed').length
    ElMessage.success(`记忆生成完成：成功${okCount}章${failCount ? '，失败' + failCount + '章' : ''}`)
    // 重新拉取记忆
    const mem = await getMemory(novelId.value)
    memoryChapters.value = mem.chapters || []
    // 展开刚生成的章节
    expandedMemories.value = regenMemorySelected.value
  } finally {
    regeneratingMemory.value = false
  }
}

// 导出
function onExport() {
  const selected = chapters.value
    .filter(c => exportSelected.value.includes(c.id))
    .sort((a, b) => a.chapter_num - b.chapter_num)

  if (!selected.length) {
    ElMessage.warning('请选择要导出的章节')
    return
  }

  let content = ''
  const title = novel.value?.title || '小说'
  if (exportFormat.value === 'md') {
    content = `# ${title}\n\n`
    for (const ch of selected) {
      content += `## 第${ch.chapter_num}章 ${ch.title || ''}\n\n${ch.content || ''}\n\n`
    }
  } else {
    content = `${title}\n\n`
    for (const ch of selected) {
      content += `第${ch.chapter_num}章 ${ch.title || ''}\n\n${ch.content || ''}\n\n\n`
    }
  }

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${title}.${exportFormat.value}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  ElMessage.success(`已导出 ${selected.length} 章`)
  showExportDialog.value = false
}

// AI扫描补充角色
async function onExtractCharacters() {
  extractingChars.value = true
  try {
    const result = await extractCharacters(novelId.value)
    if (result.total_added > 0) {
      ElMessage.success(`扫描完成，新增 ${result.total_added} 个角色：${result.added.join('、')}`)
    } else {
      ElMessage.success('扫描完成，没有发现新角色')
    }
    characters.value = await listCharacters(novelId.value)
  } finally {
    extractingChars.value = false
  }
}

// 根据已有章节重新生成大纲
async function onRegenerateOutline() {
  regeneratingOutline.value = true
  try {
    const result = await regenerateOutline(novelId.value)
    outlineText.value = result.outline
    ElMessage.success('大纲已根据已有章节重新生成')
  } finally {
    regeneratingOutline.value = false
  }
}

// AI生成全局记忆
async function onGenerateGlobalMemory() {
  generatingGlobalMemory.value = true
  try {
    const result = await generateGlobalMemory(novelId.value)
    memoryGlobal.value = result.global_memory
    ElMessage.success('全局记忆已生成')
  } finally {
    generatingGlobalMemory.value = false
  }
}

async function onGenerateChapter() {
  if (!writeForm.value.chapter_outline) {
    ElMessage.warning('请填写章节要求')
    return
  }
  writing.value = true
  writingContent.value = ''
  try {
    const result = await generateChapter(novelId.value, {
      chapter_num: writeForm.value.chapter_num,
      chapter_outline: writeForm.value.chapter_outline,
      title: writeForm.value.title || `第${writeForm.value.chapter_num}章`,
    })
    writingContent.value = result.chapter.content
    ElMessage.success('章节生成成功')
    fetchData()
  } finally {
    writing.value = false
  }
}

async function onStreamChapter() {
  if (!writeForm.value.chapter_outline) {
    ElMessage.warning('请填写章节要求')
    return
  }
  streaming.value = true
  writingContent.value = ''

  const token = localStorage.getItem('token')
  try {
    const response = await fetch('/api/novel/' + novelId.value + '/chapters/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        chapter_num: writeForm.value.chapter_num,
        chapter_outline: writeForm.value.chapter_outline,
        title: writeForm.value.title || `第${writeForm.value.chapter_num}章`,
      }),
    })

    if (!response.ok) {
      ElMessage.error('请求失败: ' + response.status)
      streaming.value = false
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          if (dataStr === '[DONE]') {
            streaming.value = false
            fetchData()
            ElMessage.success('章节生成成功')
            return
          }
          try {
            const data = JSON.parse(dataStr)
            if (data.type === 'chunk') {
              writingContent.value += data.data
            } else if (data.type === 'error') {
              ElMessage.error(data.data)
              streaming.value = false
              return
            } else if (data.type === 'done') {
              writingContent.value += `\n\n---\n章节已保存：${data.data.chapter_id}`
            }
          } catch {
            writingContent.value += dataStr
          }
        }
      }
    }
  } catch (e) {
    ElMessage.error('流式请求失败: ' + e.message)
  } finally {
    streaming.value = false
  }
}

function onOpenChapter(row) {
  editingChapter.value = { ...row }
  showChapterEditor.value = true
}

async function onEditChapter(row) {
  editingChapter.value = { ...row }
  showChapterEditor.value = true
}

async function onSaveChapter() {
  if (!editingChapter.value) return
  savingChapter.value = true
  try {
    await updateChapter(novelId.value, editingChapter.value.id, {
      title: editingChapter.value.title,
      content: editingChapter.value.content,
    })
    ElMessage.success('保存成功')
    showChapterEditor.value = false
    fetchData()
  } finally {
    savingChapter.value = false
  }
}

async function onDeleteChapter(row) {
  try {
    await ElMessageBox.confirm(`确定删除第${row.chapter_num}章？`, '删除确认', { type: 'warning' })
    await deleteChapter(novelId.value, row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { /* cancelled */ }
}

function onEditChar(row) {
  editingChar.value = row
  charForm.value = { name: row.name, personality: row.personality, background: row.background }
  showCharDialog.value = true
}

async function onDeleteChar(row) {
  try {
    await ElMessageBox.confirm(`确定删除角色「${row.name}」？`, '删除确认', { type: 'warning' })
    await deleteCharacter(novelId.value, row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { /* cancelled */ }
}

async function onSaveChar() {
  if (!charForm.value.name) {
    ElMessage.warning('请填写角色名')
    return
  }
  try {
    if (editingChar.value) {
      await updateCharacter(novelId.value, editingChar.value.id, charForm.value)
    } else {
      await createCharacter(novelId.value, charForm.value)
    }
    ElMessage.success('保存成功')
    showCharDialog.value = false
    editingChar.value = null
    charForm.value = { name: '', personality: '', background: '' }
    fetchData()
  } catch { /* handled */ }
}

onMounted(fetchData)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.tab-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.write-section {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  margin-top: 16px;
}

.chapter-preview {
  margin-top: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-size: 13px;
  color: #606266;
}

.preview-content {
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
}

.review-content {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
  color: #303133;
  background: #fdf6ec;
  padding: 16px;
  border-radius: 6px;
}
</style>
