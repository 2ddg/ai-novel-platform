<template>
  <div class="chat-page">
    <!-- 左侧历史记录 -->
    <div class="history-sidebar">
      <div class="sidebar-header">
        <span>对话历史</span>
        <el-button
          v-if="currentKbId"
          type="danger"
          size="small"
          text
          @click="onClearHistory"
        >
          清空
        </el-button>
      </div>

      <el-select
        v-model="currentKbId"
        placeholder="选择知识库"
        class="kb-select"
        @change="onKbChange"
      >
        <el-option
          v-for="kb in kbList"
          :key="kb.id"
          :label="kb.name"
          :value="kb.id"
        />
      </el-select>

      <div class="history-list" v-loading="historyLoading">
        <div
          v-for="item in history"
          :key="item.id"
          class="history-item"
          :class="{ active: activeHistoryId === item.id }"
          @click="selectHistory(item)"
        >
          <div class="history-question">{{ item.question }}</div>
          <div class="history-time">{{ formatTime(item.created_at) }}</div>
          <el-icon
            class="history-delete"
            :size="14"
            @click.stop="onDeleteHistory(item, $event)"
          >
            <Close />
          </el-icon>
        </div>
        <el-empty v-if="!history.length && !historyLoading" description="暂无对话" :image-size="60" />
      </div>
    </div>

    <!-- 右侧对话区 -->
    <div class="chat-main">
      <!-- 空状态 -->
      <div v-if="!currentKbId" class="chat-empty">
        <el-icon :size="64" color="#c0c4cc"><ChatDotRound /></el-icon>
        <p>请先在左侧选择一个知识库</p>
      </div>

      <template v-else>
        <!-- 消息列表 -->
        <div ref="messagesRef" class="messages-container">
          <div v-if="!messages.length" class="chat-empty">
            <el-icon :size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
            <p>开始提问吧！</p>
          </div>

          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message-item"
            :class="msg.role"
          >
            <div class="avatar">
              <el-icon v-if="msg.role === 'user'" :size="20" color="#fff"><User /></el-icon>
              <el-icon v-else :size="20" color="#fff"><Service /></el-icon>
            </div>
            <div class="message-body">
              <div class="message-content">
                <!-- 用户消息：纯文本 -->
                <span v-if="msg.role === 'user'">{{ msg.content }}</span>

                <!-- AI 消息：Markdown 渲染 -->
                <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>

                <!-- 流式中指示器 -->
                <span v-if="msg.streaming" class="cursor">|</span>
              </div>

              <!-- 来源引用 -->
              <div v-if="msg.sources && msg.sources.length" class="sources">
                <span class="sources-label">参考来源（{{ uniqueSourceCount(msg.sources) }}个文档，{{ msg.sources.length }}个片段）：</span>
                <el-tag
                  v-for="(s, si) in msg.sources"
                  :key="si"
                  size="small"
                  type="info"
                  class="source-tag"
                >
                  {{ s.filename }}#{{ s.chunk_index ?? si + 1 }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="input-area">
          <div class="input-wrapper">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              placeholder="输入你的问题，Enter 发送，Shift+Enter 换行"
              :disabled="streaming"
              @keydown="onKeydown"
              resize="none"
            />
            <el-button
              type="primary"
              :icon="Promotion"
              :loading="streaming"
              :disabled="!inputText.trim()"
              @click="onSend"
              circle
            />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound, User, Service, Promotion, Close,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import { listKnowledge } from '../api/knowledge'
import { chatStream, getHistory, deleteHistory, clearHistory as clearHistoryApi } from '../api/chat'

const route = useRoute()

// 知识库列表（供选择）
const kbList = ref([])
const currentKbId = ref(null)

// 消息 & 历史
const messages = ref([])
const history = ref([])
const historyLoading = ref(false)
const activeHistoryId = ref(null)

// 输入
const inputText = ref('')
const streaming = ref(false)
const messagesRef = ref()

// 渲染 Markdown
marked.setOptions({ breaks: true, gfm: true })
function renderMarkdown(text) {
  return marked.parse(text || '')
}

// 自动滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 加载知识库列表
async function fetchKbList() {
  try {
    kbList.value = await listKnowledge()
    // 如果路由带 kbId，自动选中
    if (route.params.id) {
      currentKbId.value = parseInt(route.params.id)
      onKbChange()
    }
  } catch {}
}

// 切换知识库
async function onKbChange() {
  if (!currentKbId.value) return
  messages.value = []
  activeHistoryId.value = null
  await fetchHistory()
}

// 加载历史
async function fetchHistory() {
  historyLoading.value = true
  try {
    history.value = await getHistory(currentKbId.value)
  } finally {
    historyLoading.value = false
  }
}

// 选中历史记录
function selectHistory(item) {
  activeHistoryId.value = item.id
  messages.value = [
    { role: 'user', content: item.question },
    { role: 'assistant', content: item.answer, sources: item.sources || [] },
  ]
  scrollToBottom()
}

// 删除一条历史
async function onDeleteHistory(item, e) {
  e.stopPropagation()
  await ElMessageBox.confirm('确定删除该条对话记录？', '提示', { type: 'warning' })
    .then(async () => {
      await deleteHistory(item.id)
      ElMessage.success('已删除')
      if (activeHistoryId.value === item.id) {
        messages.value = []
        activeHistoryId.value = null
      }
      fetchHistory()
    }).catch(() => {})
}

// 清空历史
async function onClearHistory() {
  await ElMessageBox.confirm('确定清空当前知识库的所有对话历史？', '提示', { type: 'warning' })
    .then(async () => {
      await clearHistoryApi(currentKbId.value)
      ElMessage.success('已清空')
      messages.value = []
      activeHistoryId.value = null
      fetchHistory()
    }).catch(() => {})
}

// 发送消息（流式）
async function onSend() {
  const question = inputText.value.trim()
  if (!question || streaming.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: question })
  inputText.value = ''
  scrollToBottom()

  // 添加 AI 消息占位
  const aiMsg = { role: 'assistant', content: '', sources: [], streaming: true }
  messages.value.push(aiMsg)
  scrollToBottom()

  streaming.value = true
  activeHistoryId.value = null

  try {
    const resp = await chatStream({
      question,
      kb_id: currentKbId.value,
      top_k: 5,
    })

    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`)
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      // 按 \n\n 分割 SSE 事件
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const lines = part.split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const evt = JSON.parse(data)
            if (evt.type === 'sources') {
              aiMsg.sources = evt.data
            } else if (evt.type === 'chunk') {
              aiMsg.content += evt.data
              scrollToBottom()
            } else if (evt.type === 'error') {
              aiMsg.content = '抱歉，出现错误：' + evt.data
              aiMsg.streaming = false
              streaming.value = false
              scrollToBottom()
              return
            }
          } catch {
            // 非 JSON 数据，直接拼接
            aiMsg.content += data
            scrollToBottom()
          }
        }
      }
    }

    // 流结束
    aiMsg.streaming = false
    ElMessage.success('回答完成')

    // 刷新历史
    fetchHistory()
  } catch (e) {
    aiMsg.content = '抱歉，出现错误：' + (e.message || '未知错误')
    aiMsg.streaming = false
  } finally {
    streaming.value = false
    scrollToBottom()
  }
}

// 键盘事件
function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}

function formatTime(str) {
  if (!str) return ''
  const d = new Date(str)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function uniqueSourceCount(sources) {
  if (!sources || !sources.length) return 0
  const names = new Set(sources.map(s => s.filename))
  return names.size
}

onMounted(fetchKbList)
</script>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - 100px);
  gap: 16px;
}

/* 左侧历史 */
.history-sidebar {
  width: 260px;
  background: #fff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 600;
  font-size: 14px;
}

.kb-select {
  margin: 10px 12px;
  width: calc(100% - 24px);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  padding: 10px 12px;
  border-radius: 6px;
  margin-bottom: 4px;
  cursor: pointer;
  position: relative;
  transition: background 0.15s;
}

.history-item:hover {
  background: #f5f7fa;
}

.history-item.active {
  background: #ecf5ff;
}

.history-question {
  font-size: 13px;
  color: #303133;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  padding-right: 20px;
}

.history-time {
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
}

.history-delete {
  position: absolute;
  top: 8px;
  right: 8px;
  color: #c0c4cc;
  opacity: 0;
  transition: opacity 0.15s;
}

.history-item:hover .history-delete {
  opacity: 1;
}

.history-delete:hover {
  color: #f56c6c;
}

/* 右侧对话区 */
.chat-main {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  gap: 12px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #409eff;
}

.message-item.assistant .avatar {
  background: #67c23a;
}

.message-body {
  max-width: 70%;
}

.message-item.user .message-body {
  align-items: flex-end;
  display: flex;
  flex-direction: column;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-item.user .message-content {
  background: #409eff;
  color: #fff;
  border-top-right-radius: 4px;
}

.message-item.assistant .message-content {
  background: #f4f4f5;
  color: #303133;
  border-top-left-radius: 4px;
}

.markdown-body :deep(p) {
  margin: 0 0 8px;
}
.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}
.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.markdown-body :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}
.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.cursor {
  display: inline-block;
  animation: blink 0.8s infinite;
  font-weight: bold;
}
@keyframes blink {
  50% { opacity: 0; }
}

.sources {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.sources-label {
  font-size: 12px;
  color: #909399;
  margin-right: 4px;
}

.source-tag {
  font-size: 11px;
}

/* 输入区 */
.input-area {
  padding: 12px 24px 16px;
  border-top: 1px solid #f0f0f0;
}

.input-wrapper {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
}
</style>
